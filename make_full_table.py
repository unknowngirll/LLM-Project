#!/usr/bin/env python3
"""
make_full_table.py - one comprehensive results table for the repository.

Scores every completed run under all four normalisation conditions and
writes RESULTS_ALL.md plus a CSV. Also reports throughput (median seconds
per paper, from output file timestamps) for the deployment cost estimate.
"""
import os, re, sys, csv, glob, statistics, subprocess
from pathlib import Path

# (model, params_B, mode, prompt, results subpath)
RUNS = [
    ("Qwen3-4B-Instruct", 4,  "Instruct", "v2",     "dev/Qwen3-4B-Instruct-2507"),
    ("Qwen3-4B-Thinking", 4,  "Thinking", "v2",     "dev/Qwen3-4B-Thinking-2507"),
    ("Qwen3.5-4B",        4,  "Instruct", "v3",     "nothink_35/Qwen3.5-4B"),
    ("Qwen3-8B",          8,  "Instruct", "v3",     "nothink_8b/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Thinking", "v3",     "simple_8b/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Thinking", "v5",     "v5_think_8b/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Thinking", "v6lite", "q8b_think_v6lite/Qwen3-8B"),
    ("Qwen3.6-27B",      27,  "Instruct", "v3",     "qwen36_v3/Qwen3.6-27B"),
    ("Qwen3.6-27B",      27,  "Thinking", "v3",     "simple_36/Qwen3.6-27B"),
    ("Llama-3.1-8B",      8,  "Instruct", "v3",     "llama31_v3/Llama-3.1-8B-Instruct"),
    ("Gemma-4-12B",      12,  "Thinking", "v6",     "gemma4_v6/gemma-4-12B-it"),
    ("Magistral-Small",  24,  "Instruct", "v3",     "magistral_v3_new/Magistral-Small-2509"),
    ("Magistral-Small",  24,  "Thinking", "v5",     "magi_think_v5/Magistral-Small-2509"),
    ("Magistral-Small",  24,  "Thinking", "v6",     "magi_think_v6/Magistral-Small-2509"),
]

NORMS = [
    ("none",      "results",             "data/gold_answers.jsonl"),
    ("fuzzy+LLM", "results_jamie",       "data/gold_answers.jsonl"),
    ("HGNC",      "results_norm",        "data/gold_answers_norm.jsonl"),
    ("cascade",   "results_cascade_all", "data/gold_answers_norm.jsonl"),
]

def resolve(root, sub):
    if root == "results":
        return os.path.join(root, sub)
    hits = glob.glob(os.path.join(root, "**", sub), recursive=True)
    return hits[0] if hits else os.path.join(root, sub)

def score(d, gold):
    if not os.path.isdir(d) or not os.path.exists(gold):
        return None
    n = len([f for f in glob.glob(d + "/*.txt") if not f.endswith("_raw.txt")])
    if n < 100:
        return None
    r = subprocess.run([sys.executable, "score_v2.py", "--gold", gold, "--pred_dir", d],
                       capture_output=True, text=True, timeout=1800)
    t = r.stdout
    def g(p, c=float):
        m = re.search(p, t)
        return c(m.group(1)) if m else None
    o = {"n": n,
         "F1": g(r"F1\s*=\s*([\d.]+)"), "P": g(r"Precision.*?=\s*([\d.]+)"),
         "R": g(r"Recall.*?=\s*([\d.]+)"), "TP": g(r"TP=(\d+)", int),
         "FP": g(r"FP=(\d+)", int), "FN": g(r"FN=(\d+)", int),
         "TN": g(r"TN=(\d+)", int), "fail": g(r"parse failures:\s*(\d+)", int)}
    for f in ("outcome", "induction", "species"):
        o[f] = g(rf"{f}\s+accuracy=([\d.]+)")
    return o if o["F1"] is not None else None

def health(d):
    fs = [f for f in glob.glob(d + "/*.txt") if not f.endswith("_raw.txt")]
    if not fs:
        return {}
    closed = sum(1 for f in fs
                 if "</think>" in open(f, encoding="utf-8", errors="ignore").read())
    ts = sorted(Path(f).stat().st_mtime for f in fs)
    gaps = sorted(b - a for a, b in zip(ts, ts[1:]) if 0 < b - a < 3600)
    return {"kb": sum(os.path.getsize(f) for f in fs) / len(fs) / 1024,
            "closed_pct": 100.0 * closed / len(fs),
            "sec": gaps[len(gaps) // 2] if gaps else None}

rows, best = [], {}
for model, params, mode, prompt, sub in RUNS:
    h = health(os.path.join("results", sub))
    if not h:
        print(f"  skip (no output): {sub}", flush=True)
        continue
    rec = {"model": model, "params": params, "mode": mode, "prompt": prompt,
           "dir": sub, **h}
    for norm, root, gold in NORMS:
        s = score(resolve(root, sub), gold)
        rec[norm] = s["F1"] if s else None
        if norm == "HGNC" and s:
            rec.update({k: s[k] for k in
                        ("n", "P", "R", "TP", "FP", "FN", "TN", "fail",
                         "induction", "outcome", "species")})
    vals = [rec.get(nm) for nm, _, _ in NORMS if rec.get(nm) is not None]
    rec["best"] = max(vals) if vals else None
    print(f"  {model:18s} {mode:9s} {prompt:7s} best={rec['best']}", flush=True)
    rows.append(rec)

rows.sort(key=lambda r: -(r["best"] or 0))

def f(v, p=3):
    return f"{v:.{p}f}" if isinstance(v, float) else ("–" if v is None else str(v))

with open("RESULTS_ALL.md", "w", encoding="utf-8") as fh:
    fh.write("# Model comparison — full results\n\n")
    fh.write("All runs on the OATargets evaluation set (267 papers: 175 positives + "
             "92 true negatives), scored with `score_v2.py`. Rows sorted by best F1.\n\n")
    fh.write("Earlier v2 runs used a 175-paper positives-only set and are marked "
             "accordingly; their TN is 0 by construction and they are not directly "
             "comparable with the 267-paper rows.\n\n")

    fh.write("## Headline: F1 under each normalisation condition\n\n")
    fh.write("| Model | Params | Mode | Prompt | none | fuzzy+LLM | HGNC | cascade |\n")
    fh.write("|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        cells = []
        for nm, _, _ in NORMS:
            v = r.get(nm)
            cells.append(f"**{f(v)}**" if v is not None and v == r["best"] else f(v))
        fh.write(f"| {r['model']} | {r['params']}B | {r['mode']} | {r['prompt']} | "
                 + " | ".join(cells) + " |\n")

    fh.write("\n## Detail (HGNC-normalised scoring)\n\n")
    fh.write("| Model | Mode | Prompt | F1 | P | R | TP | FP | FN | TN | "
             "Induction | Outcome | Species | Parse fail |\n")
    fh.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        fh.write(f"| {r['model']} | {r['mode']} | {r['prompt']} | {f(r.get('HGNC'))} | "
                 f"{f(r.get('P'))} | {f(r.get('R'))} | {f(r.get('TP'))} | "
                 f"{f(r.get('FP'))} | {f(r.get('FN'))} | {f(r.get('TN'))} | "
                 f"{f(r.get('induction'))} | {f(r.get('outcome'))} | "
                 f"{f(r.get('species'))} | {f(r.get('fail'))} |\n")

    fh.write("\n## Run characteristics\n\n")
    fh.write("Throughput is the median gap between consecutive output files. "
             "The projection is for the full ~11,000-paper corpus on one GPU.\n\n")
    fh.write("| Model | Mode | Prompt | Papers | Reasoning closed | Avg output | "
             "Median s/paper | Projected GPU-h for 11,000 |\n")
    fh.write("|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        sec = r.get("sec")
        proj = f"{sec * 11000 / 3600:.0f}" if sec else "–"
        fh.write(f"| {r['model']} | {r['mode']} | {r['prompt']} | {r.get('n','–')} | "
                 f"{r['closed_pct']:.0f}% | {r['kb']:.1f} KB | "
                 f"{f(sec, 0) if sec else '–'} | {proj} |\n")

    fh.write("\n## Normalisation conditions\n\n")
    fh.write("| Condition | Description |\n|---|---|\n")
    fh.write("| `none` | Raw model output scored against the unmodified gold |\n")
    fh.write("| `fuzzy+LLM` | Fuzzy matching over an NCBI gene database, with a "
             "language model adjudicating between candidates |\n")
    fh.write("| `HGNC` | Deterministic alias mapping from the HGNC complete set; "
             "the same rules are applied to the gold so matching is symmetric |\n")
    fh.write("| `cascade` | HGNC first, then fuzzy+LLM over whatever the "
             "deterministic pass left unresolved |\n")

cols = (["model", "params", "mode", "prompt", "dir", "n"]
        + [nm for nm, _, _ in NORMS]
        + ["best", "P", "R", "TP", "FP", "FN", "TN",
           "induction", "outcome", "species", "fail", "kb", "closed_pct", "sec"])
with open("results/all_models_comparison.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    [w.writerow(r) for r in rows]

print(f"\n{len(rows)} runs -> RESULTS_ALL.md and results/all_models_comparison.csv")
