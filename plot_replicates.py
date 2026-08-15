#!/usr/bin/env python3
"""
plot_replicates.py - run-to-run variation across independent seeds.

Strip plot: one point per run, with the mean marked. With three replicates a
strip plot is preferable to a bar chart, since it shows the individual
observations rather than hiding them behind a summary statistic.
"""
import os, re, sys, csv, glob, subprocess, argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 11, "axes.linewidth": 0.9,
                     "legend.frameon": False})

ap = argparse.ArgumentParser()
ap.add_argument("--prefix", default="results/replicates")
a = ap.parse_args()

RUNS = {
    "Magistral-24B": [
        "magi_think_v6/Magistral-Small-2509",
        "magi_v6_s2/Magistral-Small-2509",
        "magi_v6_s3/Magistral-Small-2509",
    ],
    "Qwen3-8B": [
        "q8b_think_v6full/Qwen3-8B",
        "q8_v6_s2/Qwen3-8B",
        "q8_v6_s3/Qwen3-8B",
    ],
}
COLOUR = {"Magistral-24B": "#1B9E77", "Qwen3-8B": "#3C8DBC"}

def score(sub):
    for root in ("results_norm2", "results_norm"):
        d = os.path.join(root, sub)
        if not os.path.isdir(d):
            continue
        r = subprocess.run([sys.executable, "score_v2.py",
                            "--gold", "data/gold_answers_norm.jsonl",
                            "--pred_dir", d],
                           capture_output=True, text=True, timeout=1800)
        t = r.stdout
        def g(p):
            m = re.search(p, t)
            return float(m.group(1)) if m else None
        f1 = g(r"F1\s*=\s*([\d.]+)")
        if f1 is not None:
            return {"F1": f1, "P": g(r"Precision.*?=\s*([\d.]+)"),
                    "R": g(r"Recall.*?=\s*([\d.]+)")}
    return None

rows = []
for model, subs in RUNS.items():
    for i, sub in enumerate(subs, 1):
        s = score(sub)
        if s is None:
            print(f"  missing: {sub}", flush=True); continue
        rows.append({"model": model, "run": i, "dir": sub, **s})
        print(f"  {model:14s} run {i}  F1={s['F1']:.3f} "
              f"P={s['P']:.3f} R={s['R']:.3f}", flush=True)

METRICS = [("F1", "F1"), ("P", "Precision"), ("R", "Recall")]
models = [m for m in RUNS if any(r["model"] == m for r in rows)]

fig, axes = plt.subplots(1, 3, figsize=(11, 4.6), sharey=False)
rng = np.random.default_rng(0)

for ax, (key, label) in zip(axes, METRICS):
    for x, model in enumerate(models):
        vals = [r[key] for r in rows if r["model"] == model]
        if not vals:
            continue
        jitter = rng.uniform(-0.06, 0.06, len(vals))
        ax.scatter([x + j for j in jitter], vals, s=70, zorder=3,
                   color=COLOUR.get(model, "#888"), edgecolor="#333", lw=.8,
                   alpha=.9)
        m, sd = float(np.mean(vals)), float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
        ax.hlines(m, x - 0.18, x + 0.18, color="#333", lw=2, zorder=4)
        ax.annotate(f"{m:.3f}\n\u00b1{sd:.3f}", (x, m), fontsize=8.5,
                    ha="center", va="bottom", color="black",
                    xytext=(0, 9), textcoords="offset points")
    ax.set_xticks(range(len(models)))
    ax.set_xticklabels(models, fontsize=9.5)
    ax.set_xlim(-0.55, len(models) - 0.45)
    ax.set_title(label, loc="left", fontweight="bold")
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", alpha=.22); ax.set_axisbelow(True)

axes[0].set_ylabel("Score (HGNC-normalised)")
fig.suptitle("Run-to-run variation, prompt v6, three independent seeds "
             "\u2014 267-paper OATargets set", fontsize=10, y=1.02, color="#555")

for ext in ("png", "pdf"):
    fig.savefig(f"{a.prefix}.{ext}", dpi=300, bbox_inches="tight")
print(f"\nsaved {a.prefix}.png")

with open(f"{a.prefix}.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["model", "run", "dir", "F1", "P", "R"])
    w.writeheader(); [w.writerow(r) for r in rows]

print("\nsummary:")
for model in models:
    for key, label in METRICS:
        vals = [r[key] for r in rows if r["model"] == model]
        if len(vals) > 1:
            print(f"  {model:14s} {label:10s} mean {np.mean(vals):.3f} "
                  f"SD {np.std(vals, ddof=1):.3f} range {max(vals)-min(vals):.3f}")
