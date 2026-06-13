#!/usr/bin/env python3
"""
score.py - evaluate one model's outputs against the OATargets gold standard.

Reports precision / recall / F1 at three levels:
  1. GENE-level    : did the model find the right genes? (set-based per paper)
  2. ATTRIBUTE-level: for matched (gene+direction) pairs, are the other fields right?
  3. STRICT        : an observation counts correct only if ALL scored fields match.

Matching key = (gene, manipulation_direction) so a gene with opposite effects
in the same paper is handled correctly.
"""
import os, re, json, argparse
from collections import defaultdict

# ---------- crosswalk (model vocab -> gold vocab) ----------
OUTCOME_TO_GOLD = {"increased":"detrimental","decreased":"protective",
                   "no change":"no effect"}
SPECIES_NORM = {"mice":"mouse","mouse":"mouse","rats":"rat","rat":"rat",
                "rabbits":"rabbit","rabbit":"rabbit","guinea pigs":"guinea pig",
                "guinea pig":"guinea pig","pigs":"pig","pig":"pig","dogs":"dog","dog":"dog"}
INDUCTION_TO_GOLD = {"surgical":{"surgical"},"chemical":{"mia","protease"},
                     "mechanical":{"exercise"},"spontaneous":{"ageing"},"ageing":{"ageing"},
                     "metabolic":{"high fat diet"},"transgenic":{"genetic"}}
# gold effect_on_gene_product -> coarse direction (Loss/Gain)
GOLD_EFFECT_TO_DIR = {"removal":"loss","knockdown":"loss","inhibition":"loss",
                      "haploinsufficiency":"loss","deficiency":"loss",
                      "overexpression":"gain","increase":"gain","activation":"gain",
                      "mutation":"other"}

def norm(s): return (s or "").strip().lower()

def model_outcome_to_gold(o): return OUTCOME_TO_GOLD.get(norm(o))
def model_species_to_gold(s): return SPECIES_NORM.get(norm(s), norm(s))
def induction_match(model_ind, gold_simple):
    s = INDUCTION_TO_GOLD.get(norm(model_ind))
    return s is not None and norm(gold_simple) in s

def gold_dir(effect): return GOLD_EFFECT_TO_DIR.get(norm(effect), "other")

# ---------- load gold ----------
def load_gold(path):
    gold = {}
    with open(path) as f:
        for line in f:
            line=line.strip()
            if not line: continue
            r=json.loads(line)
            gold[r["pmid"]] = r["gold_observations"]
    return gold

# ---------- parse a model output file (robust to extra text / <think>) ----------
def parse_model_file(path):
    txt = open(path, encoding="utf-8").read()
    txt = re.sub(r"<think>.*?</think>", "", txt, flags=re.DOTALL)
    # grab the first {...} JSON block
    m = re.search(r"\{.*\}", txt, flags=re.DOTALL)
    if not m: return None
    try:
        data = json.loads(m.group(0))
    except Exception:
        return None
    if isinstance(data, dict) and data.get("result"):  # "no valid perturbations"
        return []
    return data.get("observations", []) if isinstance(data, dict) else []

# ---------- counters ----------
class PRF:
    def __init__(self): self.tp=0; self.fp=0; self.fn=0
    def add(self, tp, fp, fn): self.tp+=tp; self.fp+=fp; self.fn+=fn
    def prf(self):
        p = self.tp/(self.tp+self.fp) if (self.tp+self.fp) else 0.0
        r = self.tp/(self.tp+self.fn) if (self.tp+self.fn) else 0.0
        f = 2*p*r/(p+r) if (p+r) else 0.0
        return p,r,f

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--gold", default="data/gold_answers.jsonl")
    ap.add_argument("--pred_dir", required=True, help="dir with <pmid>.txt model outputs")
    args=ap.parse_args()

    gold = load_gold(args.gold)

    gene_prf = PRF()
    attr_prf = {f:PRF() for f in ["outcome","induction","species"]}
    strict_prf = PRF()
    n_files=0; n_parse_fail=0

    for fn in os.listdir(args.pred_dir):
        if not fn.endswith(".txt") or fn.endswith("_raw.txt"): continue
        pmid = fn[:-4]
        if pmid not in gold: continue
        n_files+=1
        preds = parse_model_file(os.path.join(args.pred_dir, fn))
        if preds is None:
            n_parse_fail+=1; preds=[]
        golds = gold[pmid]

        # ---- GENE level (set based) ----
        gset = {norm(o["gene"]) for o in golds}
        pset = {norm(o.get("target","")) for o in preds if o.get("target")}
        tp=len(gset&pset); fp=len(pset-gset); fn_=len(gset-pset)
        gene_prf.add(tp,fp,fn_)

        # ---- build matching key (gene, direction) ----
        gold_by_key=defaultdict(list)
        for o in golds:
            gold_by_key[(norm(o["gene"]), gold_dir(o["effect_on_gene_product"]))].append(o)
        pred_by_key=defaultdict(list)
        for o in preds:
            pred_by_key[(norm(o.get("target","")), norm(o.get("manipulation_direction","")))].append(o)

        matched_pairs=[]
        used_keys=set()
        for key, glist in gold_by_key.items():
            plist = pred_by_key.get(key, [])
            for i in range(min(len(glist), len(plist))):
                matched_pairs.append((glist[i], plist[i]))
            used_keys.add(key)

        # ---- ATTRIBUTE level on matched pairs ----
        for g,p in matched_pairs:
            # outcome
            ok = model_outcome_to_gold(p.get("oa_severity_outcome")) == norm(g["susceptibility_observed"])
            attr_prf["outcome"].add(1 if ok else 0, 0 if ok else 1, 0)
            # induction
            ok = induction_match(p.get("oa_induction"), g["simple_model"])
            attr_prf["induction"].add(1 if ok else 0, 0 if ok else 1, 0)
            # species
            ok = model_species_to_gold(p.get("species")) == norm(g["species"])
            attr_prf["species"].add(1 if ok else 0, 0 if ok else 1, 0)

        # ---- STRICT (all fields incl. gene+direction already matched) ----
        strict_tp=0
        for g,p in matched_pairs:
            allok = (model_outcome_to_gold(p.get("oa_severity_outcome"))==norm(g["susceptibility_observed"])
                     and induction_match(p.get("oa_induction"), g["simple_model"])
                     and model_species_to_gold(p.get("species"))==norm(g["species"]))
            if allok: strict_tp+=1
        strict_fp = len(preds)-strict_tp
        strict_fn = len(golds)-strict_tp
        strict_prf.add(strict_tp, max(strict_fp,0), max(strict_fn,0))

    # ---------- report ----------
    print(f"\n=== Scoring: {args.pred_dir} ===")
    print(f"Files scored: {n_files} | JSON parse failures: {n_parse_fail}\n")
    def row(name, prf):
        p,r,f=prf.prf(); print(f"  {name:14s}  P={p:.3f}  R={r:.3f}  F1={f:.3f}")
    print("GENE level (did it find the right genes?)")
    row("gene", gene_prf)
    print("\nATTRIBUTE level (on matched gene+direction pairs)")
    for k,v in attr_prf.items(): row(k, v)
    print("\nSTRICT (all scored fields correct)")
    row("strict", strict_prf)
    print()

if __name__=="__main__":
    main()
