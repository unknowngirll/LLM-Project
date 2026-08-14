#!/usr/bin/env python3
"""
plot_consensus.py - two figures for the multi-model consensus experiment.

A: precision, recall and F1 for each single model, every pairwise combination
   under both agreement rules, and both three-model voting rules
B: the confidence ladder - how often an extracted gene is correct given how
   many of the three models extracted it

All inputs are scored after the revised HGNC normalisation.
"""
import os, re, sys, csv, json, glob, subprocess, argparse
from collections import Counter
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 11, "axes.linewidth": 0.9,
                     "legend.frameon": False})

ap = argparse.ArgumentParser()
ap.add_argument("--prefix", default="results/consensus")
ap.add_argument("--gold", default="data/gold_answers_norm.jsonl")
a = ap.parse_args()

MAG = "results_norm2/magi_think_v6/Magistral-Small-2509"
QWN = "results_norm2/q8b_think_v6full/Qwen3-8B"
GEM = "results_norm2/gemma4_v6/gemma-4-12B-it"
CONS = "results_consensus2"

# label, directory, category
CONFIGS = [
    ("Magistral\nalone",        MAG,                          "single"),
    ("Qwen3-8B\nalone",         QWN,                          "single"),
    ("Gemma-4\nalone",          GEM,                          "single"),
    ("Magistral + Qwen\nboth",  f"{CONS}/MagQwen_intersection", "both"),
    ("Magistral + Gemma\nboth", f"{CONS}/MagGem_intersection",  "both"),
    ("Qwen + Gemma\nboth",      f"{CONS}/QwenGem_intersection", "both"),
    ("Magistral + Qwen\neither", f"{CONS}/MagQwen_union",       "either"),
    ("Magistral + Gemma\neither", f"{CONS}/MagGem_union",       "either"),
    ("Qwen + Gemma\neither",    f"{CONS}/QwenGem_union",        "either"),
    ("All three\n2 of 3",       f"{CONS}/vote2",               "three"),
    ("All three\n3 of 3",       f"{CONS}/vote3",               "three"),
]

CAT_COLOUR = {"single": "#BDBDBD", "both": "#3C8DBC",
              "either": "#E8A33D", "three": "#1B9E77"}
CAT_LABEL = {"single": "Single model",
             "both": "Pair, gene found by both",
             "either": "Pair, gene found by either",
             "three": "Three-model vote"}

def score(d):
    if not os.path.isdir(d):
        return None
    r = subprocess.run([sys.executable, "score_v2.py", "--gold", a.gold,
                        "--pred_dir", d], capture_output=True, text=True,
                       timeout=1800)
    t = r.stdout
    def g(p, c=float):
        m = re.search(p, t)
        return c(m.group(1)) if m else None
    o = {"F1": g(r"F1\s*=\s*([\d.]+)"), "P": g(r"Precision.*?=\s*([\d.]+)"),
         "R": g(r"Recall.*?=\s*([\d.]+)"), "TP": g(r"TP=(\d+)", int),
         "FP": g(r"FP=(\d+)", int), "FN": g(r"FN=(\d+)", int),
         "TN": g(r"TN=(\d+)", int)}
    return o if o["F1"] is not None else None

rows = []
for label, d, cat in CONFIGS:
    s = score(d)
    if s is None:
        print("  missing:", d, flush=True); continue
    rows.append({"config": label.replace("\n", " "), "category": cat,
                 "dir": d, **s})
    print("  %-26s F1=%.3f P=%.3f R=%.3f FP=%d TN=%d"
          % (label.replace("\n", " "), s["F1"], s["P"], s["R"],
             s["FP"], s["TN"]), flush=True)

# ---------- figure A ----------
labels = [c[0] for c in CONFIGS if any(r["dir"] == c[1] for r in rows)]
data = [next(r for r in rows if r["dir"] == c[1])
        for c in CONFIGS if any(r["dir"] == c[1] for r in rows)]
cats = [c[2] for c in CONFIGS if any(r["dir"] == c[1] for r in rows)]

x = np.arange(len(data))
w = 0.27
fig, ax = plt.subplots(figsize=(13.5, 5.4))

ax.bar(x - w, [r["P"] for r in data], width=w, color="#3C8DBC", label="Precision")
ax.bar(x,     [r["R"] for r in data], width=w, color="#E8A33D", label="Recall")
ax.bar(x + w, [r["F1"] for r in data], width=w, color="#666666", label="F1")

for i, r in enumerate(data):
    ax.annotate("%.3f" % r["F1"], (i + w, r["F1"]), fontsize=7.5,
                ha="center", color="black", xytext=(0, 3),
                textcoords="offset points")

# separators between the four groups
seen, bounds = None, []
for i, c in enumerate(cats):
    if seen is not None and c != seen:
        bounds.append(i - 0.5)
    seen = c
for b in bounds:
    ax.axvline(b, color="#DDD", lw=1, zorder=0)

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=8.5)
ax.set_ylabel("Score (HGNC-normalised)")
ax.set_ylim(0, 1.0)
ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=10,
          borderaxespad=0)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", alpha=.22); ax.set_axisbelow(True)

for ext in ("png", "pdf"):
    fig.savefig("%s_scores.%s" % (a.prefix, ext), dpi=300, bbox_inches="tight")
print("\nsaved %s_scores.png" % a.prefix)
plt.close(fig)

# ---------- figure B: confidence ladder ----------
gold = {}
for l in open(a.gold, encoding="utf-8"):
    if l.strip():
        r = json.loads(l)
        gold[r["pmid"]] = {(o["gene"] or "").strip().upper()
                           for o in r["gold_observations"]}

def genes(path):
    try:
        t = open(path, encoding="utf-8", errors="ignore").read()
    except FileNotFoundError:
        return set()
    m = re.search(r"\{.*\}", t, re.DOTALL)
    if not m:
        return set()
    try:
        d = json.loads(m.group(0))
    except Exception:
        return set()
    if isinstance(d, dict) and d.get("result"):
        return set()
    return {(o.get("target") or "").strip().upper()
            for o in d.get("observations", []) if o.get("target")}

tier = {1: [0, 0], 2: [0, 0], 3: [0, 0]}
for f in sorted(glob.glob(MAG + "/*.txt")):
    fn = os.path.basename(f); pmid = fn[:-4]
    if pmid not in gold:
        continue
    votes = Counter()
    for d in (MAG, QWN, GEM):
        votes.update(genes(os.path.join(d, fn)))
    for g, v in votes.items():
        tier[v][0] += 1
        tier[v][1] += (g in gold[pmid])

lab = ["All three models", "Two of three", "One model only"]
prec = [tier[3][1] / tier[3][0] if tier[3][0] else 0,
        tier[2][1] / tier[2][0] if tier[2][0] else 0,
        tier[1][1] / tier[1][0] if tier[1][0] else 0]
counts = [tier[3][0], tier[2][0], tier[1][0]]
cols = ["#1B9E77", "#3C8DBC", "#E8482C"]

fig, ax = plt.subplots(figsize=(7.5, 4.8))
bars = ax.bar(lab, [p * 100 for p in prec], color=cols, width=.55)
for b, p, n in zip(bars, prec, counts):
    ax.annotate("%.1f%%\n(%d genes)" % (p * 100, n),
                (b.get_x() + b.get_width() / 2, p * 100),
                ha="center", fontsize=9.5, color="black",
                xytext=(0, 5), textcoords="offset points")
ax.set_ylabel("Extracted genes matching the gold standard (%)")
ax.set_xlabel("Number of models extracting the gene\n"
              "(Magistral-Small, Qwen3-8B, Gemma-4-12B)")
ax.set_ylim(0, 100)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", alpha=.22); ax.set_axisbelow(True)
for ext in ("png", "pdf"):
    fig.savefig("%s_ladder.%s" % (a.prefix, ext), dpi=300, bbox_inches="tight")
print("saved %s_ladder.png" % a.prefix)

with open(a.prefix + ".csv", "w", newline="", encoding="utf-8") as fh:
    w2 = csv.writer(fh)
    w2.writerow(["tier", "genes", "correct", "precision"])
    for v, name in ((3, "all_three"), (2, "two_of_three"), (1, "one_only")):
        n, c = tier[v]
        w2.writerow([name, n, c, round(c / n, 3) if n else 0])
    w2.writerow([])
    w2.writerow(["configuration", "category", "F1", "P", "R", "TP", "FP", "FN", "TN"])
    for r in rows:
        w2.writerow([r["config"], r["category"], r["F1"], r["P"], r["R"],
                     r["TP"], r["FP"], r["FN"], r["TN"]])
print("saved %s.csv" % a.prefix)
