#!/usr/bin/env python3
"""Append cascade-normalised scores to figure_data.csv."""
import os, re, sys, csv, glob, subprocess

RUNS = [
    ("Qwen3.5-4B",     4,  "Instruct", "v3", "nothink_35/Qwen3.5-4B"),
    ("Qwen3-8B",       8,  "Instruct", "v3", "nothink_8b/Qwen3-8B"),
    ("Llama-3.1-8B",   8,  "Instruct", "v3", "llama31_v3/Llama-3.1-8B-Instruct"),
    ("Qwen3.6-27B",    27, "Instruct", "v3", "qwen36_v3/Qwen3.6-27B"),
]
GOLD = "data/gold_answers_norm.jsonl"

def find_cascade(sub):
    hits = glob.glob(f"results_cascade/**/{sub}/*.txt", recursive=True)
    return os.path.dirname(hits[0]) if hits else None

def score(d):
    r = subprocess.run([sys.executable, "score_v2.py", "--gold", GOLD, "--pred_dir", d],
                       capture_output=True, text=True, timeout=1800)
    t = r.stdout
    def g(p, c=float):
        m = re.search(p, t); return c(m.group(1)) if m else None
    o = {"F1": g(r"F1\s*=\s*([\d.]+)"), "P": g(r"Precision.*?=\s*([\d.]+)"),
         "R": g(r"Recall.*?=\s*([\d.]+)"), "TP": g(r"TP=(\d+)", int),
         "FP": g(r"FP=(\d+)", int), "FN": g(r"FN=(\d+)", int),
         "TN": g(r"TN=(\d+)", int), "fail": g(r"parse failures:\s*(\d+)", int)}
    for f in ("outcome", "induction", "species"):
        o[f] = g(rf"{f}\s+accuracy=([\d.]+)")
    return o

csv_path = "results/figure_data.csv"
rows = list(csv.DictReader(open(csv_path)))
cols = rows[0].keys()

added = 0
for label, params, mode, prompt, sub in RUNS:
    d = find_cascade(sub)
    if not d:
        print(f"  cascade missing: {sub}"); continue
    s = score(d)
    if s is None or s["F1"] is None:
        print(f"  score failed: {d}"); continue
    row = {"model": label, "params": params, "mode": mode, "prompt": prompt,
           "norm": "cascade", "dir": d, "n_files": 267}
    row.update(s)
    rows.append({k: row.get(k, "") for k in cols})
    added += 1
    print(f"  {label:14s} cascade F1={s['F1']:.3f}")

with open(csv_path, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader(); [w.writerow(r) for r in rows]
print(f"\nadded {added} cascade rows -> {csv_path}")
