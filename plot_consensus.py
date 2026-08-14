#!/usr/bin/env python3
"""
plot_consensus.py - two horizontal figures for the multi-model consensus work.

A: precision, recall and F1 for each single model, every pairwise combination
   under both agreement rules, and both three-model voting rules
B: the confidence ladder, broken down by which models agreed rather than by
   how many, so that every subset is named explicitly

All inputs are scored after the revised HGNC normalisation.
"""
import os, re, sys, csv, json, glob, subprocess, argparse
from collections import Counter, defaultdict
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

CONFIGS = [
    ("Magistral alone",                      MAG, "single"),
    ("Qwen3-8B alone",                       QWN, "single"),
    ("Gemma-4 alone",                        GEM, "single"),
    ("Magistral + Qwen, gene in both",   f"{CONS}/MagQwen_intersection", "both"),
    ("Magistral + Gemma, gene in both",  f"{CONS}/MagGem_intersection",  "both"),
    ("Qwen + Gemma, gene in both",       f"{CONS}/QwenGem_intersection", "both"),
    ("Magistral + Qwen, gene in either",  f"{CONS}/MagQwen_union",  "either"),
    ("Magistral + Gemma, gene in either", f"{CONS}/MagGem_union",   "either"),
    ("Qwen + Gemma, gene in either",      f"{CONS}/QwenGem_union",  "either"),
    ("All three, 2 of 3 agree",           f"{CONS}/vote2", "three"),
    ("All three, 3 of 3 agree",           f"{CONS}/vote3", "three"),
]

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
    rows.append({"config": label, "category": cat, "dir": d, **s})
    print("  %-38s F1=%.3f P=%.3f R=%.3f FP=%d TN=%d"
          % (label, s["F1"], s["P"], s["R"], s["FP"], s["TN"]), flush=True)

# ---------------- figure A: horizontal grouped bars ----------------
y = np.arange(len(rows))
h = 0.26
fig, ax = plt.subplots(figsize=(9.5, 8))

ax.barh(y - h, [r["P"] for r in rows],  height=h, color="#3C8DBC", label="Precision")
ax.barh(y,     [r["R"] for r in rows],  height=h, color="#E8A33D", label="Recall")
ax.barh(y + h, [r["F1"] for r in rows], height=h, color="#666666", label="F1")

for i, r in enumerate(rows):
    for off, key in ((-h, "P"), (0, "R"), (h, "F1")):
        ax.annotate("%.3f" % r[key], (r[key], i + off), fontsize=7.5,
                    va="center", ha="left", color="black",
                    xytext=(3, 0), textcoords="offset points")

seen = None
for i, r in enumerate(rows):
    if seen is not None and r["category"] != seen:
        ax.axhline(i - 0.5, color="#DDD", lw=1, zorder=0)
    seen = r["category"]

ax.set_yticks(y)
ax.set_yticklabels([r["config"] for r in rows], fontsize=9.5)
ax.invert_yaxis()
ax.set_xlabel("Score (HGNC-normalised)")
ax.set_xlim(0, 1.06)
ax.legend(loc="lower right", fontsize=10)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", alpha=.22); ax.set_axisbelow(True)

for ext in ("png", "pdf"):
    fig.savefig("%s_scores.%s" % (a.prefix, ext), dpi=300, bbox_inches="tight")
print("\nsaved %s_scores.png" % a.prefix)
plt.close(fig)

# ---------------- figure B: which models agreed ----------------
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

MODELS = [("Magistral", MAG), ("Qwen", QWN), ("Gemma", GEM)]
subsets = defaultdict(lambda: [0, 0])          # frozenset -> [n, correct]

for f in sorted(glob.glob(MAG + "/*.txt")):
    fn = os.path.basename(f); pmid = fn[:-4]
    if pmid not in gold:
        continue
    found = {name: genes(os.path.join(d, fn)) for name, d in MODELS}
    allg = set().union(*found.values())
    for g in allg:
        who = frozenset(n for n in found if g in found[n])
        subsets[who][0] += 1
        subsets[who][1] += (g in gold[pmid])

ORDER = [
    (frozenset({"Magistral", "Qwen", "Gemma"}), "Magistral + Qwen + Gemma", "#1B9E77"),
    (frozenset({"Magistral", "Qwen"}),          "Magistral + Qwen",         "#3C8DBC"),
    (frozenset({"Magistral", "Gemma"}),         "Magistral + Gemma",        "#4FA3D1"),
    (frozenset({"Qwen", "Gemma"}),              "Qwen + Gemma",             "#7FBEE0"),
    (frozenset({"Magistral"}),                  "Magistral only",           "#E8482C"),
    (frozenset({"Qwen"}),                       "Qwen only",                "#F07A5F"),
    (frozenset({"Gemma"}),                      "Gemma only",               "#F5A38F"),
]

bars = [(lab, col, subsets[key][0], subsets[key][1])
        for key, lab, col in ORDER if subsets[key][0] > 0]

fig, ax = plt.subplots(figsize=(9, 5.2))
yy = np.arange(len(bars))
pct = [100.0 * c / n for _, _, n, c in bars]
ax.barh(yy, pct, color=[c for _, c, _, _ in bars], height=.62)

for i, (lab, col, n, c) in enumerate(bars):
    ax.annotate("%.1f%%  (%d of %d genes)" % (pct[i], c, n), (pct[i], i),
                va="center", ha="left", fontsize=9.5, color="black",
                xytext=(5, 0), textcoords="offset points")

ax.set_yticks(yy)
ax.set_yticklabels([lab for lab, _, _, _ in bars], fontsize=10)
ax.invert_yaxis()
ax.set_xlabel("Extracted genes matching the gold standard (%)")
ax.set_xlim(0, 118)
ax.set_xticks([0, 20, 40, 60, 80, 100])
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="x", alpha=.22); ax.set_axisbelow(True)

for ext in ("png", "pdf"):
    fig.savefig("%s_ladder.%s" % (a.prefix, ext), dpi=300, bbox_inches="tight")
print("saved %s_ladder.png" % a.prefix)

with open(a.prefix + ".csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["models_agreeing", "genes", "correct", "proportion_correct"])
    for lab, _, n, c in bars:
        w.writerow([lab, n, c, round(c / n, 3)])
    w.writerow([])
    w.writerow(["configuration", "category", "F1", "P", "R",
                "TP", "FP", "FN", "TN"])
    for r in rows:
        w.writerow([r["config"], r["category"], r["F1"], r["P"], r["R"],
                    r["TP"], r["FP"], r["FN"], r["TN"]])
print("saved %s.csv" % a.prefix)

print("\nagreement breakdown:")
for lab, _, n, c in bars:
    print("  %-26s %3d genes, %3d correct (%.1f%%)" % (lab, n, c, 100.0 * c / n))
