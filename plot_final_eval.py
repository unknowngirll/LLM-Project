#!/usr/bin/env python3
"""
plot_final_eval.py - development against held-out performance.

Grouped bars for the three headline metrics on each set, so that the
generalisation gap and its confinement to recall are visible at a glance.
"""
import csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 11, "axes.linewidth": 0.9,
                     "legend.frameon": False})

DEV  = {"Precision": 0.837, "Recall": 0.877, "F1": 0.856}
HELD = {"Precision": 0.831, "Recall": 0.759, "F1": 0.794}
SD = 0.018

metrics = ["Precision", "Recall", "F1"]
x = np.arange(len(metrics))
w = 0.34

fig, ax = plt.subplots(figsize=(7.5, 4.8))
b1 = ax.bar(x - w/2, [DEV[m] for m in metrics], width=w,
            color="#BDBDBD", label="Development set (n = 267)")
b2 = ax.bar(x + w/2, [HELD[m] for m in metrics], width=w,
            color="#1B9E77", label="Held-out set (n = 295)")

ax.errorbar(x - w/2, [DEV[m] for m in metrics], yerr=SD, fmt="none",
            ecolor="#555", capsize=4, lw=1.2)

for bars, d in ((b1, DEV), (b2, HELD)):
    for b, m in zip(bars, metrics):
        ax.annotate("%.3f" % d[m], (b.get_x() + b.get_width()/2, d[m]),
                    ha="center", fontsize=9, color="black",
                    xytext=(0, 8), textcoords="offset points")

for i, m in enumerate(metrics):
    diff = HELD[m] - DEV[m]
    ax.annotate("%+.3f" % diff, (i, 0.04), ha="center", fontsize=9.5,
                color="#C0392B" if diff < -SD else "#555")

ax.set_xticks(x); ax.set_xticklabels(metrics)
ax.set_ylabel("Score (HGNC-normalised)")
ax.set_ylim(0, 1.0)
ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=10,
          borderaxespad=0)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", alpha=.22); ax.set_axisbelow(True)

for ext in ("png", "pdf"):
    fig.savefig("results/final_eval.%s" % ext, dpi=300, bbox_inches="tight")
print("saved results/final_eval.png")

with open("results/final_eval.csv", "w", newline="", encoding="utf-8") as fh:
    w2 = csv.writer(fh)
    w2.writerow(["metric", "development", "held_out", "difference"])
    for m in metrics:
        w2.writerow([m, DEV[m], HELD[m], round(HELD[m] - DEV[m], 3)])
print("saved results/final_eval.csv")
