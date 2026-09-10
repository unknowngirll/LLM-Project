#!/usr/bin/env python3
"""
export_attributes.py - attribute accuracy for the replicate and held-out runs,
so that the gene-level and attribute-level results can be shown side by side.
"""
import os, re, sys, csv, glob, subprocess

def score(d, gold):
    if not os.path.isdir(d):
        return None
    r = subprocess.run([sys.executable, "score_v2.py", "--gold", gold,
                        "--pred_dir", d], capture_output=True, text=True,
                       timeout=1800)
    t = r.stdout
    o = {}
    for f in ("outcome", "induction", "species"):
        m = re.search(rf"{f}\s+accuracy=([\d.]+)\s+\(correct=(\d+), wrong=(\d+), "
                      rf"abstain=(\d+), n=(\d+)\)", t)
        if m:
            o[f] = {"accuracy": float(m.group(1)), "correct": int(m.group(2)),
                    "wrong": int(m.group(3)), "abstain": int(m.group(4)),
                    "n": int(m.group(5))}
    return o or None

rows = []

REPS = {"Magistral-Small": ["magi_think_v6/Magistral-Small-2509",
                            "magi_v6_r2/Magistral-Small-2509",
                            "magi_v6_r3/Magistral-Small-2509"],
        "Qwen3-8B": ["q8b_think_v6full/Qwen3-8B",
                     "q8_v6_r2/Qwen3-8B", "q8_v6_r3/Qwen3-8B"],
        "Gemma-4-12B": ["gemma4_v6/gemma-4-12B-it"]}

for model, subs in REPS.items():
    for i, sub in enumerate(subs, 1):
        s = score(os.path.join("results_norm2", sub),
                  "data/gold_answers_norm.jsonl")
        if not s:
            print("  missing:", sub, flush=True); continue
        for field, v in s.items():
            rows.append({"set": "development", "model": model, "run": i,
                         "field": field, **v})

HO = [("Magistral-Small", "final_eval_v7/Magistral-Small-2509"),
      ("Qwen3-8B", "final_eval_q8b/Qwen3-8B"),
      ("Gemma-4-12B", "final_eval_gemma/gemma-4-12B-it")]

for model, sub in HO:
    s = score(os.path.join("results_norm2", sub),
              "data/gold_final_eval_norm.jsonl")
    if not s:
        print("  missing:", sub, flush=True); continue
    for field, v in s.items():
        rows.append({"set": "held-out", "model": model, "run": 1,
                     "field": field, **v})

os.makedirs("figdata", exist_ok=True)
cols = ["set", "model", "run", "field", "accuracy", "correct", "wrong",
        "abstain", "n"]
with open("figdata/attributes.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow(r)
print(f"\nwrote figdata/attributes.csv ({len(rows)} rows)")
