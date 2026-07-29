#!/usr/bin/env python3
"""Temperature sweep figure - Qwen3-8B thinking, v3, 267 papers, 3 seeds each."""
import csv, statistics
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

rows = list(csv.DictReader(open("results/temperature_sweep.csv")))
for r in rows:
    for k in ("temp","F1","P","R","closed_pct"): r[k] = float(r[k])
    r["seed"] = int(r["seed"])
    r["looped"] = float(r["looped"])

temps = sorted(set(r["temp"] for r in rows))
def agg(t, k):
    v = [r[k] for r in rows if r["temp"] == t]
    return statistics.mean(v), (statistics.stdev(v) if len(v) > 1 else 0.0)

f1m = [agg(t,"F1")[0] for t in temps]; f1s = [agg(t,"F1")[1] for t in temps]
loop = [agg(t,"looped")[0] for t in temps]
spread = max(f1m) - min(f1m); noise = max(f1s)

figA, axA = plt.subplots(figsize=(6, 5))
figB, axB = plt.subplots(figsize=(6, 5))

# A: F1 vs temperature
axA.fill_between(temps, [m-s for m,s in zip(f1m,f1s)], [m+s for m,s in zip(f1m,f1s)],
                 color="#4EC3E0", alpha=0.25)
axA.plot(temps, f1m, "-o", color="#2C7FB8", lw=2, ms=7, zorder=3)
for r in rows:
    axA.plot(r["temp"], r["F1"], "o", color="#888", ms=4, alpha=0.6, zorder=2)
axA.set_xlabel("Temperature"); axA.set_ylabel("F1")
axA.set_title("A   F1 vs temperature", loc="left", fontweight="bold")
axA.text(0.02, 0.02, f"spread {spread:.3f} vs noise {noise:.3f}  \u2014 within noise",
         transform=axA.transAxes, fontsize=9, color="#555")
axA.set_xticks(temps)

# B: precision vs recall, colour = temp, marker shape = seed
from matplotlib.lines import Line2D
cmap = {0.3:"#FEE391", 0.6:"#FEC44F", 0.9:"#FE9929", 1.2:"#CC4C02"}
smap = {1:"o", 2:"s", 3:"^"}
for r in rows:
    axB.scatter(r["R"], r["P"], s=70, color=cmap[r["temp"]],
                marker=smap[r["seed"]], edgecolor="#555", lw=.6, zorder=3)
temp_leg = [Line2D([],[], marker="o", ls="", color=cmap[t], markeredgecolor="#555",
                   label=f"{t}") for t in temps]
seed_leg = [Line2D([],[], marker=smap[sd], ls="", color="#999", markeredgecolor="#555",
                   label=f"seed {sd}") for sd in (1,2,3)]
leg1 = axB.legend(handles=temp_leg, title="Temp", fontsize=8, frameon=False,
                  loc="upper left")
axB.add_artist(leg1)
axB.legend(handles=seed_leg, title="Seed", fontsize=8, frameon=False,
           loc="lower right")
axB.set_xlabel("Recall"); axB.set_ylabel("Precision")
axB.set_title("B   Precision vs recall", loc="left", fontweight="bold")


for ax in (axA, axB):
    for s in ("top","right"): ax.spines[s].set_visible(False)
    ax.grid(alpha=.25); ax.set_axisbelow(True)

for ext in ("png","pdf"):
    figA.savefig(f"results/temperature_A_f1.{ext}", dpi=220, bbox_inches="tight")
    figB.savefig(f"results/temperature_B_pr.{ext}", dpi=220, bbox_inches="tight")
print("saved results/temperature_A_f1.png and results/temperature_B_pr.png")
