#!/usr/bin/env python3
"""score.py - Jamie's table-based scoring (TP/FP/FN/TN)."""
import os
import re
import json
import argparse
from collections import defaultdict

OUTCOME_TO_GOLD = {"increased": "detrimental", "decreased": "protective", "no change": "no effect"}
SPECIES_NORM = {"mice": "mouse", "mouse": "mouse", "rats": "rat", "rat": "rat",
                "rabbits": "rabbit", "rabbit": "rabbit", "guinea pigs": "guinea pig",
                "guinea pig": "guinea pig", "pigs": "pig", "pig": "pig", "dogs": "dog", "dog": "dog"}
# v6 and earlier emitted an abstract taxonomy that needed translating; v7 asks
# the model for gold's own vocabulary directly. Both are accepted so older runs
# stay rescorable.
INDUCTION_TO_GOLD = {"surgical": {"surgical"}, "chemical": {"mia", "protease"},
                     "mechanical": {"exercise"}, "spontaneous": {"ageing"}, "ageing": {"ageing"},
                     "metabolic": {"high fat diet"}, "transgenic": {"genetic", "ageing"},
                     "protease": {"protease"}, "mia": {"mia"}, "exercise": {"exercise"},
                     "high fat diet": {"high fat diet"}}
GOLD_EFFECT_TO_DIR = {"removal": "loss", "knockdown": "loss", "inhibition": "loss",
                      "haploinsufficiency": "loss", "deficiency": "loss", "overexpression": "gain",
                      "increase": "gain", "activation": "gain", "mutation": "other"}
NOT_STATED = {"not stated", "n/a", ""}

def norm(s):
    return (s or "").strip().lower()

def is_abstain(s):
    return norm(s) in NOT_STATED

def gold_direction(effect):
    return GOLD_EFFECT_TO_DIR.get(norm(effect), "other")

def load_gold(path):
    gold = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rec = json.loads(line)
                gold[rec["pmid"]] = rec["gold_observations"]
    return gold

def parse_model_file(path):
    text = open(path, encoding="utf-8").read()
    if "</think>" in text:
        answer = text.rsplit("</think>", 1)[1]
    else:
        answer = re.sub(r"<think>.*", "", text, flags=re.DOTALL)
    m = re.search(r"\{.*\}", answer, flags=re.DOTALL)
    if not m:
        return None
    try:
        data = json.loads(m.group(0))
    except Exception:
        m2 = re.search(r"\{.*?\}", answer, flags=re.DOTALL)
        if not m2:
            return None
        try:
            data = json.loads(m2.group(0))
        except Exception:
            return None
    if isinstance(data, dict) and data.get("result"):
        return []
    if isinstance(data, dict):
        return data.get("observations", [])
    return []

def align_paper(golds, preds):
    gold_set = {norm(o["gene"]) for o in golds}
    pred_set = {norm(o.get("target", "")) for o in preds if o.get("target")}
    tp_genes = gold_set & pred_set
    fp_genes = pred_set - gold_set
    fn_genes = gold_set - pred_set
    gold_by_gene = defaultdict(list)
    for o in golds:
        gold_by_gene[norm(o["gene"])].append(o)
    pred_by_gene = defaultdict(list)
    for o in preds:
        if o.get("target"):
            pred_by_gene[norm(o["target"])].append(o)
    pairs = []
    for g in tp_genes:
        glist = gold_by_gene[g]
        plist = list(pred_by_gene[g])
        used = set()
        for gp in glist:
            gd = gold_direction(gp["effect_on_gene_product"])
            gold_ind = norm(gp.get("simple_model", ""))
            gold_out = norm(gp.get("susceptibility_observed", ""))
            best = None
            best_score = -1
            for i, pp in enumerate(plist):
                if i in used:
                    continue
                s = 0
                if norm(pp.get("manipulation_direction", "")) == gd:
                    s += 1
                pi = norm(pp.get("oa_induction", ""))
                allowed = INDUCTION_TO_GOLD.get(pi)
                if allowed is not None and gold_ind in allowed:
                    s += 1
                po = OUTCOME_TO_GOLD.get(norm(pp.get("oa_severity_outcome", "")))
                if po is not None and po == gold_out:
                    s += 1
                if s > best_score:
                    best_score = s
                    best = i
            if best is None:
                for i in range(len(plist)):
                    if i not in used:
                        best = i
                        break
            if best is not None:
                used.add(best)
                pairs.append((gp, plist[best]))
    return {"tp": len(tp_genes), "fp": len(fp_genes), "fn": len(fn_genes), "pairs": pairs}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default="data/gold_answers.jsonl")
    ap.add_argument("--pred_dir", required=True)
    ap.add_argument("--show_table", default=None)
    args = ap.parse_args()
    gold = load_gold(args.gold)

    if args.show_table:
        pmid = args.show_table
        preds = parse_model_file(os.path.join(args.pred_dir, f"{pmid}.txt")) or []
        golds = gold.get(pmid, [])
        print(f"\nPMID {pmid}")
        print(f"{'LLM_prediction':20s} {'OATargets':20s} result")
        gold_set = {norm(o['gene']) for o in golds}
        pred_set = {norm(o.get('target', '')) for o in preds if o.get('target')}
        if not gold_set and not pred_set:
            print(f"{'NA':20s} {'NA':20s} TN")
        for g in sorted(pred_set | gold_set):
            inp = g.upper() if g in pred_set else "NA"
            ing = g.upper() if g in gold_set else "NA"
            res = "TP" if (g in pred_set and g in gold_set) else ("FP" if g in pred_set else "FN")
            print(f"{inp:20s} {ing:20s} {res}")
        print()
        return

    TP = FP = FN = TN = 0
    attr = {f: {"correct": 0, "wrong": 0, "abstain": 0} for f in ["outcome", "induction", "species"]}
    n_files = 0
    n_parse_fail = 0

    for fn in os.listdir(args.pred_dir):
        if not fn.endswith(".txt") or fn.endswith("_raw.txt"):
            continue
        pmid = fn[:-4]
        if pmid not in gold:
            continue
        n_files += 1
        preds = parse_model_file(os.path.join(args.pred_dir, fn))
        if preds is None:
            n_parse_fail += 1
            preds = []
        golds = gold[pmid]
        has_gold = len(golds) > 0
        has_pred = any(o.get("target") for o in preds)
        if not has_gold and not has_pred:
            TN += 1
            continue
        res = align_paper(golds, preds)
        TP += res["tp"]
        FP += res["fp"]
        FN += res["fn"]
        for g, p in res["pairs"]:
            mv = p.get("oa_severity_outcome")
            if is_abstain(mv):
                attr["outcome"]["abstain"] += 1
            elif OUTCOME_TO_GOLD.get(norm(mv)) == norm(g["susceptibility_observed"]):
                attr["outcome"]["correct"] += 1
            else:
                attr["outcome"]["wrong"] += 1
            mv = p.get("oa_induction")
            if is_abstain(mv):
                attr["induction"]["abstain"] += 1
            else:
                allowed = INDUCTION_TO_GOLD.get(norm(mv))
                if allowed is not None and norm(g["simple_model"]) in allowed:
                    attr["induction"]["correct"] += 1
                else:
                    attr["induction"]["wrong"] += 1
            mv = p.get("species")
            if is_abstain(mv):
                attr["species"]["abstain"] += 1
            elif SPECIES_NORM.get(norm(mv), norm(mv)) == norm(g["species"]):
                attr["species"]["correct"] += 1
            else:
                attr["species"]["wrong"] += 1

    precision = TP / (TP + FP) if (TP + FP) else 0.0
    recall = TP / (TP + FN) if (TP + FN) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    print(f"\n=== Scoring: {args.pred_dir} ===")
    print(f"Files scored: {n_files} | JSON parse failures: {n_parse_fail}\n")
    print("GENE level (Jamie's TP/FP/FN/TN table)")
    print(f"  TP={TP}  FP={FP}  FN={FN}  TN={TN}")
    print(f"  Precision = TP/(TP+FP) = {precision:.3f}")
    print(f"  Recall    = TP/(TP+FN) = {recall:.3f}")
    print(f"  F1        = {f1:.3f}")
    print("\nATTRIBUTE level (accuracy on matched gene pairs)")
    for k, c in attr.items():
        total = c["correct"] + c["wrong"]
        acc = c["correct"] / total if total else 0.0
        print(f"  {k:12s} accuracy={acc:.3f}  (correct={c['correct']}, wrong={c['wrong']}, abstain={c['abstain']}, n={total})")
    print()

if __name__ == "__main__":
    main()
