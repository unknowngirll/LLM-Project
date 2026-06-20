#!/usr/bin/env python3
"""make_table.py - per-observation diagnostic table (gene/induction/outcome/species) as CSV."""
import os
import re
import csv
import json
import argparse
from collections import defaultdict, Counter

OUTCOME_TO_GOLD = {"increased": "detrimental", "decreased": "protective", "no change": "no effect"}
SPECIES_NORM = {"mice": "mouse", "mouse": "mouse", "rats": "rat", "rat": "rat",
                "rabbits": "rabbit", "rabbit": "rabbit", "guinea pigs": "guinea pig",
                "guinea pig": "guinea pig", "pigs": "pig", "pig": "pig", "dogs": "dog", "dog": "dog"}
INDUCTION_TO_GOLD = {"surgical": {"surgical"}, "chemical": {"mia", "protease"},
                     "mechanical": {"exercise"}, "spontaneous": {"ageing"}, "ageing": {"ageing"},
                     "metabolic": {"high fat diet"}, "transgenic": {"genetic", "ageing"}}
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
    if not os.path.exists(path):
        return None
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

def outcome_match(model_v, gold_v):
    if is_abstain(model_v):
        return "abstain"
    return "yes" if OUTCOME_TO_GOLD.get(norm(model_v)) == norm(gold_v) else "no"

def induction_match(model_v, gold_v):
    if is_abstain(model_v):
        return "abstain"
    allowed = INDUCTION_TO_GOLD.get(norm(model_v))
    return "yes" if (allowed is not None and norm(gold_v) in allowed) else "no"

def species_match(model_v, gold_v):
    if is_abstain(model_v):
        return "abstain"
    return "yes" if SPECIES_NORM.get(norm(model_v), norm(model_v)) == norm(gold_v) else "no"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gold", default="data/gold_answers.jsonl")
    ap.add_argument("--pred_dir", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    gold = load_gold(args.gold)
    rows = []

    for fn in sorted(os.listdir(args.pred_dir)):
        if not fn.endswith(".txt") or fn.endswith("_raw.txt"):
            continue
        pmid = fn[:-4]
        if pmid not in gold:
            continue
        preds = parse_model_file(os.path.join(args.pred_dir, fn)) or []
        golds = gold[pmid]

        pred_by_gene = defaultdict(list)
        for o in preds:
            if o.get("target"):
                pred_by_gene[norm(o["target"])].append(o)
        gold_genes = {norm(o["gene"]) for o in golds}

        for g in golds:
            gene = norm(g["gene"])
            plist = pred_by_gene.get(gene, [])
            if plist:
                gd = gold_direction(g["effect_on_gene_product"])
                match = None
                for pp in plist:
                    if norm(pp.get("manipulation_direction", "")) == gd:
                        match = pp
                        break
                if match is None:
                    match = plist[0]
                rows.append({
                    "PMID": pmid, "row_type": "TP",
                    "gene_gold": g["gene"], "gene_LLM": match.get("target", ""), "gene_match": "yes",
                    "induction_gold": g["simple_model"], "induction_LLM": match.get("oa_induction", ""),
                    "induction_match": induction_match(match.get("oa_induction"), g["simple_model"]),
                    "outcome_gold": g["susceptibility_observed"], "outcome_LLM": match.get("oa_severity_outcome", ""),
                    "outcome_match": outcome_match(match.get("oa_severity_outcome"), g["susceptibility_observed"]),
                    "species_gold": g["species"], "species_LLM": match.get("species", ""),
                    "species_match": species_match(match.get("species"), g["species"]),
                })
            else:
                rows.append({
                    "PMID": pmid, "row_type": "FN",
                    "gene_gold": g["gene"], "gene_LLM": "MISSED", "gene_match": "no",
                    "induction_gold": g["simple_model"], "induction_LLM": "MISSED", "induction_match": "no",
                    "outcome_gold": g["susceptibility_observed"], "outcome_LLM": "MISSED", "outcome_match": "no",
                    "species_gold": g["species"], "species_LLM": "MISSED", "species_match": "no",
                })

        for gene, plist in pred_by_gene.items():
            if gene not in gold_genes:
                for pp in plist:
                    rows.append({
                        "PMID": pmid, "row_type": "FP",
                        "gene_gold": "NONE", "gene_LLM": pp.get("target", ""), "gene_match": "no",
                        "induction_gold": "NONE", "induction_LLM": pp.get("oa_induction", ""), "induction_match": "no",
                        "outcome_gold": "NONE", "outcome_LLM": pp.get("oa_severity_outcome", ""), "outcome_match": "no",
                        "species_gold": "NONE", "species_LLM": pp.get("species", ""), "species_match": "no",
                    })

    cols = ["PMID", "row_type", "gene_gold", "gene_LLM", "gene_match",
            "induction_gold", "induction_LLM", "induction_match",
            "outcome_gold", "outcome_LLM", "outcome_match",
            "species_gold", "species_LLM", "species_match"]
    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    c = Counter(r["row_type"] for r in rows)
    print(f"Wrote {len(rows)} rows to {args.out}")
    print(f"  TP rows: {c['TP']}  FN rows: {c['FN']}  FP rows: {c['FP']}")

if __name__ == "__main__":
    main()
