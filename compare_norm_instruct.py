#!/usr/bin/env python3
"""
compare_norm_instruct.py - three-way normalisation comparison (none / hgnc / jamie)
across the instruct runs on the 267-paper evaluation set.
Prints a table, writes CSV and a markdown table for the repository.
"""
import os, re, sys, csv, subprocess, argparse

RUNS = [
    ("Qwen3-8B",     "nothink_8b/Qwen3-8B"),
    ("Qwen3.5-4B",   "nothink_35/Qwen3.5-4B"),
    ("Llama-3.1-8B", "llama31_v3/Llama-3.1-8B-Instruct"),
    ("Qwen3.6-27B",  "qwen36_v3/Qwen3.6-27B"),
]
METHODS = [
    ("none",  "results",       "data/gold_answers.jsonl"),
    ("hgnc",  "results_norm",  "data/gold_answers_norm.jsonl"),
    ("jamie", "results_jamie", "data/gold_answers.jsonl"),
]

ap = argparse.ArgumentParser()
ap.add_argument("--csv", default="results/instruct_normalisation.csv")
ap.add_argument("--md",  default="RESULTS_instruct.md")
a = ap.parse_args()

def score(pred_dir, gold):
    if not os.path.isdir(pred_dir) or not os.path.exists(gold):
        return None
    try:
        r = subprocess.run([sys.executable, "score_v2.py", "--gold", gold,
                            "--pred_dir", pred_dir],
                           capture_output=True, text=True, timeout=1800)
    except Exception:
        return None
    t = r.stdout
    def g(p, c=float):
        m = re.search(p, t)
        return c(m.group(1)) if m else None
    o = {"F1": g(r"F1\s*=\s*([\d.]+)"), "P": g(r"Precision.*?=\s*([\d.]+)"),
         "R": g(r"Recall.*?=\s*([\d.]+)"), "TP": g(r"TP=(\d+)", int),
         "FP": g(r"FP=(\d+)", int), "FN": g(r"FN=(\d+)", int),
         "TN": g(r"TN=(\d+)", int), "fail": g(r"parse failures:\s*(\d+)", int),
         "scored": g(r"Files scored:\s*(\d+)", int)}
    for f in ("outcome", "induction", "species"):
        o[f] = g(rf"{f}\s+accuracy=([\d.]+)")
    return o if o["F1"] is not None else None

rows = []
for model, sub in RUNS:
    for tag, root, gold in METHODS:
        d = os.path.join(root, sub)
        s = score(d, gold)
        if s is None:
            print(f"  MISSING: {d}", flush=True)
            continue
        rows.append({"model": model, "norm": tag, "dir": d, **s})

def f(v, p=3):
    return f"{v:.{p}f}" if isinstance(v, float) else ("-" if v is None else str(v))

hdr = (f"{'model':14s} {'norm':6s} {'F1':>6s} {'P':>6s} {'R':>6s} "
       f"{'TP':>4s} {'FP':>4s} {'FN':>4s} {'TN':>4s} {'ind':>5s} {'out':>5s} "
       f"{'sp':>5s} {'fail':>5s}")
print("\n" + hdr); print("-" * len(hdr))
last = None
for r in rows:
    if last and r["model"] != last:
        print()
    last = r["model"]
    print(f"{r['model']:14s} {r['norm']:6s} {f(r['F1']):>6s} {f(r['P']):>6s} "
          f"{f(r['R']):>6s} {r['TP']:4d} {r['FP']:4d} {r['FN']:4d} {r['TN']:4d} "
          f"{f(r['induction']):>5s} {f(r['outcome']):>5s} {f(r['species']):>5s} "
          f"{r['fail']:5d}")

# summary: F1 per method, side by side
print("\n" + "=" * 60)
print(f"{'model':14s} {'none':>8s} {'hgnc':>8s} {'jamie':>8s}")
print("-" * 60)
by = {}
for r in rows:
    by.setdefault(r["model"], {})[r["norm"]] = r["F1"]
for model, _ in RUNS:
    d = by.get(model, {})
    print(f"{model:14s} {f(d.get('none')):>8s} {f(d.get('hgnc')):>8s} "
          f"{f(d.get('jamie')):>8s}")

os.makedirs("results", exist_ok=True)
cols = ["model","norm","dir","scored","F1","P","R","TP","FP","FN","TN",
        "induction","outcome","species","fail"]
with open(a.csv, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader(); [w.writerow(r) for r in rows]

with open(a.md, "w", encoding="utf-8") as fh:
    fh.write("# Gene normalisation comparison (instruct models)\n\n")
    fh.write("All runs on the 267-paper evaluation set (175 positives + 92 true "
             "negatives), v3 prompts, non-thinking mode, scored with `score_v2.py`.\n\n")
    fh.write("| Method | Description |\n|---|---|\n")
    fh.write("| `none` | Raw model output, no normalisation |\n")
    fh.write("| `hgnc` | Deterministic HGNC alias mapping (`normalise_genes.py`), "
             "scored against normalised gold |\n")
    fh.write("| `jamie` | Fuzzy matching over an NCBI gene database plus LLM "
             "adjudication (`jamie_normalise_adapted.py`) |\n\n")

    fh.write("## F1 by normalisation method\n\n")
    fh.write("| Model | none | hgnc | jamie |\n|---|---|---|---|\n")
    for model, _ in RUNS:
        d = by.get(model, {})
        fh.write(f"| {model} | {f(d.get('none'))} | {f(d.get('hgnc'))} | "
                 f"{f(d.get('jamie'))} |\n")

    fh.write("\n## Full results\n\n")
    fh.write("| Model | Norm | F1 | P | R | TP | FP | FN | TN | Induction | "
             "Outcome | Species | Parse fail |\n")
    fh.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        fh.write(f"| {r['model']} | `{r['norm']}` | **{f(r['F1'])}** | {f(r['P'])} | "
                 f"{f(r['R'])} | {r['TP']} | {r['FP']} | {r['FN']} | {r['TN']} | "
                 f"{f(r['induction'])} | {f(r['outcome'])} | {f(r['species'])} | "
                 f"{r['fail']} |\n")

print(f"\nCSV      -> {a.csv}")
print(f"Markdown -> {a.md}")
