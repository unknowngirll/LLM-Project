#!/usr/bin/env python3
"""
make_master_table.py - one table holding every run across every scoring
condition, so the effect of each normalisation strategy is visible in
one place rather than scattered across separate reports.
"""
import os, re, sys, csv, glob, subprocess, argparse

RUNS = [
    # (model, params_B, mode, prompt, results subpath)
    ("Qwen3-4B-Instruct", 4,  "Instruct", "v2",     "dev/Qwen3-4B-Instruct-2507"),
    ("Qwen3-4B-Thinking", 4,  "Thinking", "v2",     "dev/Qwen3-4B-Thinking-2507"),
    ("Qwen3.5-4B",        4,  "Instruct", "v3",     "nothink_35/Qwen3.5-4B"),
    ("Llama-3.1-8B",      8,  "Instruct", "v3",     "llama31_v3/Llama-3.1-8B-Instruct"),
    ("Qwen3.6-27B",      27,  "Instruct", "v3",     "qwen36_v3/Qwen3.6-27B"),
    ("Qwen3.6-27B",      27,  "Thinking", "v3",     "simple_36/Qwen3.6-27B"),
    ("Gemma-4-12B",      12,  "Thinking", "v6full", "gemma4_v6/gemma-4-12B-it"),
    ("Magistral-Small",  24,  "Instruct", "v3",     "magistral_v3_new/Magistral-Small-2509"),
    # Qwen3-8B instruct sweep
    ("Qwen3-8B",          8,  "Instruct", "v1",     "psweep_v1/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Instruct", "v2",     "psweep_v2/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Instruct", "v3",     "psweep_v3/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Instruct", "v4",     "psweep_v4/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Instruct", "v5",     "psweep_v5/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Instruct", "v6lite", "psweep_v6lite/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Instruct", "v6full", "psweep_v6full/Qwen3-8B"),
    # Qwen3-8B thinking sweep
    ("Qwen3-8B",          8,  "Thinking", "v1",     "qthink_v1/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Thinking", "v2",     "qthink_v2/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Thinking", "v3",     "simple_8b/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Thinking", "v4",     "qthink_v4/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Thinking", "v5",     "v5_think_8b/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Thinking", "v6lite", "q8b_think_v6lite/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Thinking", "v6full", "q8b_think_v6full/Qwen3-8B"),
    # Magistral thinking sweep
    ("Magistral-Small",  24,  "Thinking", "v1",     "magi_think_v1/Magistral-Small-2509"),
    ("Magistral-Small",  24,  "Thinking", "v2",     "magi_think_v2/Magistral-Small-2509"),
    ("Magistral-Small",  24,  "Thinking", "v3",     "magi_think_v3/Magistral-Small-2509"),
    ("Magistral-Small",  24,  "Thinking", "v4",     "magi_think_v4/Magistral-Small-2509"),
    ("Magistral-Small",  24,  "Thinking", "v5",     "magi_think_v5/Magistral-Small-2509"),
    ("Magistral-Small",  24,  "Thinking", "v6lite", "magi_think_v6lite/Magistral-Small-2509"),
    ("Magistral-Small",  24,  "Thinking", "v6full", "magi_think_v6/Magistral-Small-2509"),
    # dynamic k-nearest few-shot
    ("Qwen3-8B",          8,  "Instruct", "v5 k=0", "dyn_k0/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Instruct", "v5 k=3", "dyn_k3/Qwen3-8B"),
    ("Qwen3-8B",          8,  "Instruct", "v5 k=5", "dyn_k5/Qwen3-8B"),
]

NORMS = [
    ("none",      "results",             "data/gold_answers.jsonl"),
    ("fuzzy+LLM", "results_jamie",       "data/gold_answers.jsonl"),
    ("HGNC v1",   "results_norm",        "data/gold_answers_norm.jsonl"),
    ("HGNC v2",   "results_norm2",       "data/gold_answers_norm.jsonl"),
    ("cascade",   "results_cascade_all", "data/gold_answers_norm.jsonl"),
]

ap = argparse.ArgumentParser()
ap.add_argument("--md",  default="RESULTS_MASTER.md")
ap.add_argument("--csv", default="results/master_comparison.csv")
a = ap.parse_args()

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
    r = subprocess.run([sys.executable, "score_v2.py", "--gold", gold,
                        "--pred_dir", d], capture_output=True, text=True, timeout=1800)
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

rows = []
for model, params, mode, prompt, sub in RUNS:
    raw = os.path.join("results", sub)
    n = len([f for f in glob.glob(raw + "/*.txt") if not f.endswith("_raw.txt")])
    if n < 100:
        print(f"  skip (no output): {sub}", flush=True)
        continue
    rejected = sum(1 for f in glob.glob(raw + "/*.txt")
                   if '"result"' in open(f, encoding="utf-8", errors="ignore").read())
    rec = {"model": model, "params": params, "mode": mode, "prompt": prompt,
           "dir": sub, "n": n, "rejected": rejected}
    for norm, root, gold in NORMS:
        s = score(resolve(root, sub), gold)
        rec[norm] = s["F1"] if s else None
        if norm == "HGNC v2" and s:
            rec.update({k: s[k] for k in
                        ("P", "R", "TP", "FP", "FN", "TN", "fail",
                         "induction", "outcome", "species")})
    vals = [rec.get(nm) for nm, _, _ in NORMS if rec.get(nm) is not None]
    rec["best"] = max(vals) if vals else None
    print(f"  {model:18s} {mode:9s} {prompt:7s} best={rec['best']}", flush=True)
    rows.append(rec)

rows.sort(key=lambda r: -(r["best"] or 0))

def f(v, p=3):
    return f"{v:.{p}f}" if isinstance(v, float) else ("--" if v is None else str(v))

with open(a.md, "w", encoding="utf-8") as fh:
    fh.write("# Master results table\n\n")
    fh.write("Every run scored under every normalisation condition. All runs use "
             "the 267-paper OATargets evaluation set (175 positives + 92 true "
             "negatives) and `score_v2.py`, except the two v2 rows, which predate "
             "the true negatives and used a 175-paper positives-only set - their "
             "TN is 0 by construction and they are not comparable with the rest.\n\n")

    fh.write("## Scoring conditions\n\n| Condition | Description |\n|---|---|\n")
    fh.write("| `none` | Raw model output against the unmodified gold |\n")
    fh.write("| `fuzzy+LLM` | Fuzzy matching over an NCBI gene database with a "
             "language model adjudicating between candidates |\n")
    fh.write("| `HGNC v1` | Deterministic alias mapping, first implementation |\n")
    fh.write("| `HGNC v2` | Revised mapping: indexes HGNC gene names as well as "
             "alias symbols, filters pseudogenes, strips mouse/rat ortholog "
             "suffixes, and resolves ambiguous aliases against the paper's own "
             "text |\n")
    fh.write("| `cascade` | `HGNC v1` followed by fuzzy+LLM on whatever it left "
             "unresolved |\n\n")

    fh.write("## F1 by condition\n\n")
    fh.write("| Model | Params | Mode | Prompt |" +
             "".join(f" {nm} |" for nm, _, _ in NORMS) + "\n")
    fh.write("|---|---|---|---|" + "---|" * len(NORMS) + "\n")
    for r in rows:
        cells = []
        for nm, _, _ in NORMS:
            v = r.get(nm)
            cells.append(f"**{f(v)}**" if v is not None and v == r["best"] else f(v))
        fh.write(f"| {r['model']} | {r['params']}B | {r['mode']} | {r['prompt']} | "
                 + " | ".join(cells) + " |\n")

    fh.write("\n## Detail under the revised normalisation (`HGNC v2`)\n\n")
    fh.write("| Model | Mode | Prompt | F1 | P | R | TP | FP | FN | TN | "
             "Rejected | Induction | Outcome | Species | Parse fail |\n")
    fh.write("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        fh.write(f"| {r['model']} | {r['mode']} | {r['prompt']} | "
                 f"{f(r.get('HGNC v2'))} | {f(r.get('P'))} | {f(r.get('R'))} | "
                 f"{f(r.get('TP'))} | {f(r.get('FP'))} | {f(r.get('FN'))} | "
                 f"{f(r.get('TN'))} | {r['rejected']} | {f(r.get('induction'))} | "
                 f"{f(r.get('outcome'))} | {f(r.get('species'))} | "
                 f"{f(r.get('fail'))} |\n")

    fh.write("\n## Notes\n\n")
    fh.write("- The rejected column counts abstracts for which the model returned "
             "the explicit rejection object. 92 of the 267 genuinely warrant "
             "rejection, so counts far above that indicate over-rejection.\n")
    fh.write("- Prompt v1 emits `animal_species` rather than `species` and has no "
             "`manipulation_direction` field, so its species accuracy is zero by "
             "construction and its attribute scores are not comparable.\n")
    fh.write("- Most conditions are a single run. Repeat runs at one temperature "
             "gave a standard deviation of 0.015 F1, so differences smaller than "
             "roughly 0.03 should not be read as real.\n")

cols = (["model", "params", "mode", "prompt", "dir", "n", "rejected"]
        + [nm for nm, _, _ in NORMS]
        + ["best", "P", "R", "TP", "FP", "FN", "TN",
           "induction", "outcome", "species", "fail"])
os.makedirs(os.path.dirname(a.csv) or ".", exist_ok=True)
with open(a.csv, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    [w.writerow(r) for r in rows]

print(f"\n{len(rows)} runs -> {a.md} and {a.csv}")
