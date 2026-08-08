#!/usr/bin/env python3
"""
normalise_gold.py - apply the same deterministic rules to the gold file so
that matching stays symmetric.

Only the formatting rules matter here, since the gold already carries official
symbols; without them a gold entry of HLA-DRB1 would stop matching a prediction
normalised to HLADRB1. Context disambiguation (R6) is deliberately off: the
gold needs no alias resolution.
"""
import json, argparse, importlib.util, sys, os
from collections import Counter

# --- parse our own args first, while sys.argv is still intact ---
ap = argparse.ArgumentParser()
ap.add_argument("--gold", default="data/gold_answers.jsonl")
ap.add_argument("--out",  default="data/gold_answers_norm.jsonl")
ap.add_argument("--hgnc", default="~/scratch/ref/hgnc_complete_set.txt")
a = ap.parse_args()

# --- import normalise_genes for its functions, with a harmless argv ---
real_argv = sys.argv
sys.argv = ["ng", "--pred_dirs", "__no_such_dir__",
            "--report", "/tmp/_ng_dummy.csv", "--out_root", "/tmp/_ng_dummy"]
spec = importlib.util.spec_from_file_location("ng", "normalise_genes.py")
ng = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(ng)
except SystemExit:
    pass
finally:
    sys.argv = real_argv

cand, official, names = ng.load_hgnc(os.path.expanduser(a.hgnc))
maps = (cand, official, names, {})          # empty NCBI tier, no context

stats, changed, total = Counter(), 0, 0
with open(a.gold, encoding="utf-8") as fi, open(a.out, "w", encoding="utf-8") as fo:
    for line in fi:
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        for o in rec.get("gold_observations", []):
            total += 1
            old = o.get("gene", "")
            new = ng.norm_one(old, maps, stats)
            if ng.squash(old) != ng.squash(new):
                changed += 1
            o["gene"] = new
        fo.write(json.dumps(rec, ensure_ascii=False) + "\n")

print(f"gold normalised -> {a.out}")
print(f"  {total} gold observations, {changed} symbols changed")
print("  rules fired:", dict(stats))
