#!/usr/bin/env python3
"""
plot_comparison.py - four-panel model comparison figure.

A  gene-level recovery: correct (TP) and incorrect (FP) predictions,
   with a dashed line at the true number of gold genes
B  F1 under each normalisation condition
C  attribute annotation accuracy (induction / outcome / species)
D  precision-recall, marker shape by mode and size by parameter count
"""
import csv, argparse, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib.cm as cm
import matplotlib.colors as mcolors

ap = argparse.ArgumentParser()
ap.add_argument("--csv", default="results/figure_data.csv")
ap.add_argument("--out", default="results/model_comparison")
ap.add_argument("--norm", default="hgnc",
                help="normalisation condition shown in panels A, C and D")
a = ap.parse_args()

rows = list(csv.DictReader(open(a.csv)))
for r in rows:
    for k in ("F1","P","R","induction","outcome","species"):
        r[k] = float(r[k]) if r[k] not in ("", "-", None) else float("nan")
    for k in ("TP","FP","FN","TN","params","fail"):
        r[k] = int(r[k])
    r["key"] = f"{r['model']} ({r['mode'][:4]}, {r['prompt']})"

main = [r for r in rows if r["norm"] == a.norm]
main.sort(key=lambda r: r["F1"])
keys = [r["key"] for r in main]
y = range(len(main))

C_OK, C_BAD = "#4EC3E0", "#E8482C"
C_NORM = {"none": "#BDBDBD", "hgnc": "#3C8DBC", "jamie": "#E8A33D", "cascade": "#1B9E77"}
NORM_LABEL = {"none": "none", "hgnc": "HGNC", "jamie": "fuzzy+LLM", "cascade": "cascade"}
C_ATTR = {"induction": "#E8482C", "outcome": "#4EC3E0", "species": "#1B9E77"}
MODE_MK = {"Instruct": "o", "Thinking": "^"}
pnorm = mcolors.Normalize(vmin=0, vmax=30)
pcmap = matplotlib.colormaps.get_cmap("Purples")

figA, axA = plt.subplots(figsize=(10, 6))
figB, axB = plt.subplots(figsize=(10, 6))
figC, axC = plt.subplots(figsize=(10, 6))
figD, axD = plt.subplots(figsize=(8, 7))

def side_markers(ax, data):
    """Disabled: parameter count and mode are now written into the tick labels,
    which avoids glyphs overlapping variable-length model names."""
    return
    tr = ax.get_yaxis_transform()
    for i, r in enumerate(data):
        ax.scatter(-0.11, i, transform=tr, clip_on=False, s=95, marker="s",
                   color=pcmap(pnorm(r["params"])), edgecolor="#555", linewidth=.6,
                   zorder=5)
        ax.scatter(-0.055, i, transform=tr, clip_on=False, s=95,
                   marker=MODE_MK[r["mode"]], color="#7FB3A5",
                   edgecolor="#555", linewidth=.6, zorder=5)

# --- A: gene-level recovery -------------------------------------------
tp = [r["TP"] for r in main]
fp = [r["FP"] for r in main]
axA.barh(list(y), tp, color=C_OK, label="Correct (TP)")
axA.barh(list(y), fp, left=tp, color=C_BAD, label="Incorrect (FP)")
true_n = main[0]["TP"] + main[0]["FN"]
axA.axvline(true_n, ls="--", color="black", lw=1.6,
            label=f"True number of genes ({true_n})")
axA.set_yticks(list(y)); axA.set_yticklabels(keys)
axA.set_xlabel("Number of predicted genes")
axA.set_title(f"A   Gene-level recovery  ({a.norm} normalisation)",
              loc="left", fontweight="bold")
axA.legend(fontsize=9, loc="center left", bbox_to_anchor=(1.02, 0.5),
           frameon=False)
side_markers(axA, main)

# --- B: F1 by normalisation -------------------------------------------
order = ["none", "jamie", "hgnc", "cascade"]
h = 0.8 / len(order)
def match_row(r, nm):
    tail = r["dir"].split("/", 1)[1] if "/" in r["dir"] else r["dir"]
    for x in rows:
        if x["norm"] == nm and (x["dir"].endswith(tail) or tail in x["dir"]):
            return x
    return None
for j, nm in enumerate(order):
    vals, ys = [], []
    for i, r in enumerate(main):
        m = match_row(r, nm)
        if m:
            vals.append(m["F1"]); ys.append(i + (j - (len(order)-1)/2) * h)
    axB.barh(ys, vals, height=h, color=C_NORM[nm], label=NORM_LABEL[nm])
axB.set_yticks(list(y)); axB.set_yticklabels(keys)
axB.set_xlabel("F1"); axB.set_xlim(0, 1)
axB.set_title("B   Effect of gene normalisation", loc="left", fontweight="bold")
axB.legend(title="Normalisation", fontsize=9, title_fontsize=9,
           loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)

# --- C: attribute accuracy --------------------------------------------
for j, f in enumerate(["induction", "outcome", "species"]):
    axC.barh([i + (j - 1) * h for i in y], [r[f] * 100 for r in main],
             height=h, color=C_ATTR[f], label=f.capitalize())
axC.set_yticks(list(y)); axC.set_yticklabels(keys)
axC.set_xlabel("Annotation accuracy (%)"); axC.set_xlim(0, 100)
axC.set_title("C   Attribute annotation accuracy", loc="left", fontweight="bold")
axC.legend(title="Field", fontsize=9, title_fontsize=9,
           loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
side_markers(axC, main)

# --- D: precision vs recall -------------------------------------------
# Short label: the model name already carries its size, so params are not
# repeated. Offsets alternate so adjacent points do not collide.
def short_key(r):
    tag = "Think" if r["mode"] == "Thinking" else "Inst"
    return f"{r['model']} ({tag}{'*' if r['prompt'] == 'v5' else ''})"

pts = sorted(main, key=lambda r: (r["R"], r["P"]))
offsets = [(9, 7), (9, -12), (-9, 9), (-9, -13)]
for i, r in enumerate(pts):
    axD.scatter(r["R"], r["P"], s=60 + r["params"] * 12,
                marker=MODE_MK[r["mode"]], color=pcmap(pnorm(r["params"])),
                edgecolor="#333", linewidth=.8, zorder=3)
    dx, dy = offsets[i % len(offsets)]
    axD.annotate(short_key(r), (r["R"], r["P"]), fontsize=8,
                 xytext=(dx, dy), textcoords="offset points",
                 ha="left" if dx > 0 else "right", zorder=4,
                 bbox=dict(boxstyle="round,pad=0.15", fc="white",
                           ec="none", alpha=0.75))

lo = min(min(r["R"] for r in main), min(r["P"] for r in main)) - 0.08
hi = max(max(r["R"] for r in main), max(r["P"] for r in main)) + 0.08
axD.plot([lo, hi], [lo, hi], ls=":", color="#bbb", lw=1, zorder=1)
axD.set_xlim(lo, hi); axD.set_ylim(lo, hi)
axD.set_aspect("equal", adjustable="box")
axD.set_xlabel("Recall"); axD.set_ylabel("Precision")
axD.set_title("D   Precision vs recall", loc="left", fontweight="bold")
axD.legend(handles=[Line2D([], [], marker=MODE_MK[m], ls="", color="#888",
                           markeredgecolor="#333", markersize=8, label=m)
                    for m in ("Instruct", "Thinking")],
           fontsize=9, loc="lower right", frameon=True, framealpha=.9,
           edgecolor="#ddd")

for ax in (axA, axB, axC):
    ax.grid(axis="x", alpha=.25, zorder=0); ax.set_axisbelow(True)
axD.grid(alpha=.25, zorder=0); axD.set_axisbelow(True)
for ax in (axA, axB, axC, axD):
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)

sm = cm.ScalarMappable(norm=pnorm, cmap=pcmap); sm.set_array([])
cbD = figD.colorbar(sm, ax=axD, location="right", fraction=.025,
                    pad=.03, shrink=.6, aspect=25)
cbD.set_label("Parameters (B)", fontsize=9)

CAP = ("267-paper OATargets set (175 positives + 92 true negatives). "
       "* = v5 prompts; all others v3.")
for fg, ax, tag, name in [(figA, axA, "A", "recovery"), (figB, axB, "B", "normalisation"),
                          (figC, axC, "C", "attributes"), (figD, axD, "D", "precision_recall")]:
    fg.suptitle(CAP, fontsize=9, y=1.005, color="#555")
    fg.savefig(f"{a.out}_{tag}_{name}.png", dpi=220, bbox_inches="tight")
    fg.savefig(f"{a.out}_{tag}_{name}.pdf", bbox_inches="tight")
    print(f"saved {a.out}_{tag}_{name}.png")
