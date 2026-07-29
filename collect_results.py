#!/usr/bin/env python3
"""
collect_results.py - score every comparable run under each normalisation
condition and write one tidy CSV for plotting.

Only runs over the same 267-paper evaluation set are included, so the
comparison is like-for-like. Runs on the older 175-paper v2 set, the
rejected v4 prompt, and the two broken Qwen3.5 thinking runs are excluded.
"""
import os, re, sys, csv, glob, subprocess, argparse

# (label, params_B, mode, prompt, results subpath)
RUNS = [
    ("Qwen3.5-4B",     4,  "Instruct", "v3", "nothink_35/Qwen3.5-4B"),
    ("Qwen3-8B",       8,  "Instruct", "v3", "nothink_8b/Qwen3-8B"),
    ("Llama-3.1-8B",   8,  "Instruct", "v3", "llama31_v3/Llama-3.1-8B-Instruct"),
    ("Magistral-Small",24, "Instruct", "v3", "magistral_v3_new/Magistral-Small-2509"),
    ("Qwen3.6-27B",    27, "Instruct", "v3", "qwen36_v3/Qwen3.6-27B"),
    ("Qwen3-8B",       8,  "Thinking", "v3", "simple_8b/Qwen3-8B"),
    ("Qwen3.6-27B",    27, "Thinking", "v3", "simple_36/Qwen3.6-27B"),
    ("Qwen3-8B",       8,  "Thinking", "v5", "v5_think_8b/Qwen3-8B"),
    # add when the run finishes:
    # ("Magistral-Small", 24, "Thinking", "v5", "magi_think_v5/Magistral-Small-2509"),
]

NORMS = [
    ("none",  "results",       "data/gold_answers.jsonl"),
    ("hgnc",  "results_norm",  "data/gold_answers_norm.jsonl"),
    ("jamie", "results_jamie", "data/gold_answers.jsonl"),
]

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="results/figure_data.csv")
ap.add_argument("--min_files", type=int, default=250)
a = ap.parse_args()

def score(pred_dir, gold):
    if not os.path.isdir(pred_dir) or not os.path.exists(gold):
        return None
    n = len([f for f in glob.glob(pred_dir + "/*.txt") if not f.endswith("_raw.txt")])
    if n < a.min_files:
        return None
    r = subprocess.run([sys.executable, "score_v2.py", "--gold", gold,
                        "--pred_dir", pred_dir],
                       capture_output=True, text=True, timeout=1800)
    t = r.stdout
    def g(p, c=float):
        m = re.search(p, t)
        return c(m.group(1)) if m else None
    o = {"n_files": n,
         "F1": g(r"F1\s*=\s*([\d.]+)"), "P": g(r"Precision.*?=\s*([\d.]+)"),
         "R": g(r"Recall.*?=\s*([\d.]+)"), "TP": g(r"TP=(\d+)", int),
         "FP": g(r"FP=(\d+)", int), "FN": g(r"FN=(\d+)", int),
         "TN": g(r"TN=(\d+)", int), "fail": g(r"parse failures:\s*(\d+)", int)}
    for f in ("outcome", "induction", "species"):
        o[f] = g(rf"{f}\s+accuracy=([\d.]+)")
    return o if o["F1"] is not None else None

rows = []
for label, params, mode, prompt, sub in RUNS:
    for norm, root, gold in NORMS:
        d = os.path.join(root, sub)
        s = score(d, gold)
        if s is None:
            print(f"  missing: {d}  [{norm}]", flush=True)
            continue
        print(f"  {label:16s} {mode:8s} {prompt} {norm:6s} F1={s['F1']:.3f}", flush=True)
        rows.append({"model": label, "params": params, "mode": mode,
                     "prompt": prompt, "norm": norm, "dir": d, **s})

os.makedirs("results", exist_ok=True)
cols = ["model","params","mode","prompt","norm","dir","n_files","F1","P","R",
        "TP","FP","FN","TN","induction","outcome","species","fail"]
with open(a.out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    [w.writerow(r) for r in rows]
print(f"\n{len(rows)} rows -> {a.out}")
