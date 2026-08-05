#!/usr/bin/env python3
"""
plot_consensus.py - two figures for the multi-model consensus result.

A: precision and recall for each single model and each consensus rule
B: the confidence ladder - how often a gene is correct given how many
   models extracted it
"""
import os, re, sys, csv, json, glob, subprocess, argparse
from collections import Counter
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 11, "axes.linewidth": 0.9,
                     "legend.frameon": False})

ap = argparse.ArgumentParser()
ap.add_argument("--prefix", default="results/consensus")
a = ap.parse_args()

GOLD = "data/gold_answers_norm.jsonl"
MAG = "results_norm/magi_think_v6/Magistral-Small-2509"
QWN = "results_norm/q8b_think_v6lite/Qwen3-8B"
GEM = "results_norm/gemma4_v6/gemma-4-12B-it"

CONFIGS = [
    ("Magistral",  MAG,                                  "#9E9E9E"),
    ("Qwen3-8B",   QWN,                                  "#9E9E9E"),
    ("Gemma-4",    GEM,                                  "#9E9E9E"),
    ("2 of 3",     "results_consensus/vote2/v6",         "#3C8DBC"),
    ("3 of 3",     "results_consensus/vote3/v6",         "#1B9E77"),
]

def score(d):
    if not os.path.isdir(d):
        return None
    r = subprocess.run([sys.executable, "score_v2.py", "--gold", GOLD,
                        "--pred_dir", d], capture_output=True, text=True, timeout=1800)
    t = r.stdout
    def g(p, c=float):
        m = re.search(p, t); return c(m.group(1)) if m else None
    return {"F1": g(r"F1\s*=\s*([\d.]+)"), "P": g(r"Precision.*?=\s*([\d.]+)"),
            "R": g(r"Recall.*?=\s*([\d.]+)"), "FP": g(r"FP=(\d+)", int)}

rows = []
for name, d, col in CONFIGS:
    s = score(d)
    if s is None or s["F1"] is None:
        print(f"  missing: {d}", flush=True); continue
    rows.append({"config": name, "colour": col, **s})
    print(f"  {name:12s} F1={s['F1']:.3f}  P={s['P']:.3f}  "
          f"R={s['R']:.3f}  FP={s['FP']}", flush=True)

# ---------- figure A: precision / recall / F1 ----------
fig, ax = plt.subplots(figsize=(8.5, 4.8))
x = list(range(len(rows)))
w = 0.27
ax.bar([i - w for i in x], [r["P"] for r in rows], width=w,
       color="#3C8DBC", label="Precision")
ax.bar(x,                  [r["R"] for r in rows], width=w,
       color="#E8A33D", label="Recall")
ax.bar([i + w for i in x], [r["F1"] for r in rows], width=w,
       color="#777777", label="F1")
for i, r in enumerate(rows):
    ax.annotate(f"{r['P']:.3f}", (i - w, r["P"]), fontsize=7.5, ha="center",
                xytext=(0, 4), textcoords="offset points")
ax.set_xticks(x); ax.set_xticklabels([r["config"] for r in rows])
ax.set_ylabel("Score"); ax.set_ylim(0, 1.0)
ax.set_xlabel("Configuration")
ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=10,
          borderaxespad=0)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(axis="y", alpha=.22); ax.set_axisbelow(True)
for ext in ("png", "pdf"):
    fig.savefig(f"{a.prefix}_scores.{ext}", dpi=300, bbox_inches="tight")
print(f"\nsaved {a.prefix}_scores.png")
plt.close(fig)

# ---------- figure B: confidence ladder ----------
gold = {}
for l in open(GOLD, encoding="utf-8"):
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

labels = ["All three", "Two of three", "One only"]
prec   = [tier[3][1] / tier[3][0], tier[2][1] / tier[2][0], tier[1][1] / tier[1][0]]
counts = [tier[3][0], tier[2][0], tier[1][0]]
cols   = ["#1B9E77", "#3C8DBC", "#E8482C"]

fig, ax = plt.subplots(figsize=(7.5, 4.8))
bars = ax.bar(labels, [p * 100 for p in prec], color=cols, width=.55)
for b, p, n in zip(bars, prec, counts):
    ax.annotate(f"{p*100:.1f}%\n({n} genes)",
                (b.get_x() + b.get_width() / 2, p * 100),
                ha="center", fontsize=9.5,
                xytext=(0, 5), textcoords="offset points")
ax.set_ylabel("Genes that match the gold standard (%)")
ax.set_xlabel("Models extracting the gene")
ax.set_ylim(0, 100)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.grid(axis="y", alpha=.22); ax.set_axisbelow(True)
for ext in ("png", "pdf"):
    fig.savefig(f"{a.prefix}_ladder.{ext}", dpi=300, bbox_inches="tight")
print(f"saved {a.prefix}_ladder.png")

with open(f"{a.prefix}.csv", "w", newline="", encoding="utf-8") as fh:
    w2 = csv.writer(fh)
    w2.writerow(["tier", "genes", "correct", "precision"])
    for v, lab in ((3, "all_three"), (2, "two_of_three"), (1, "one_only")):
        n, c = tier[v]; w2.writerow([lab, n, c, round(c / n, 3)])
    w2.writerow([])
    w2.writerow(["config", "F1", "P", "R", "FP"])
    for r in rows:
        w2.writerow([r["config"], r["F1"], r["P"], r["R"], r["FP"]])
print(f"saved {a.prefix}.csv")
