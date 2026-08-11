#!/usr/bin/env python3
"""
plot_matrix.py - the model x prompt-version matrix as heatmaps.

Two panels, same layout, so a cell can be read across both:
  A  F1 (gene level, HGNC-normalised)
  B  median seconds per abstract, measured

Cells not run are left blank rather than imputed. Nothing is extrapolated
beyond the 267 abstracts actually processed.
"""
import os, re, sys, csv, glob, subprocess, argparse
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 10.5, "axes.linewidth": 0.9})

ap = argparse.ArgumentParser()
ap.add_argument("--prefix", default="results/matrix")
a = ap.parse_args()

VERSIONS = ["v1", "v2", "v3", "v4", "v5", "v6lite", "v6full", "v7lite", "v7full"]

# row label -> {prompt version: results subpath}
ROWS = [
    ("Qwen3.5-4B (Inst)", {
        "v3": "nothink_35/Qwen3.5-4B"}),
    ("Llama-3.1-8B (Inst)", {
        "v3": "llama31_v3/Llama-3.1-8B-Instruct"}),
    ("Qwen3-8B (Inst)", {
        "v1": "psweep_v1/Qwen3-8B", "v2": "psweep_v2/Qwen3-8B",
        "v3": "psweep_v3/Qwen3-8B", "v4": "psweep_v4/Qwen3-8B",
        "v5": "psweep_v5/Qwen3-8B", "v6lite": "psweep_v6lite/Qwen3-8B",
        "v6full": "psweep_v6full/Qwen3-8B"}),
    ("Qwen3-8B (Think)", {
        "v1": "qthink_v1/Qwen3-8B", "v2": "qthink_v2/Qwen3-8B",
        "v3": "simple_8b/Qwen3-8B", "v4": "qthink_v4/Qwen3-8B",
        "v5": "v5_think_8b/Qwen3-8B", "v6lite": "q8b_think_v6lite/Qwen3-8B",
        "v6full": "q8b_think_v6full/Qwen3-8B",
        "v7lite": "q8b_think_v7lite/Qwen3-8B",
        "v7full": "q8b_think_v7full/Qwen3-8B"}),
    ("Gemma-4-12B (Think)", {
        "v6full": "gemma4_v6/gemma-4-12B-it"}),
    ("Magistral-24B (Inst)", {
        "v3": "magistral_v3_new/Magistral-Small-2509"}),
    ("Magistral-24B (Think)", {
        "v1": "magi_think_v1/Magistral-Small-2509",
        "v2": "magi_think_v2/Magistral-Small-2509",
        "v3": "magi_think_v3/Magistral-Small-2509",
        "v4": "magi_think_v4/Magistral-Small-2509",
        "v5": "magi_think_v5/Magistral-Small-2509",
        "v6lite": "magi_think_v6lite/Magistral-Small-2509",
        "v6full": "magi_think_v6/Magistral-Small-2509",
        "v7lite": "magi_think_v7lite/Magistral-Small-2509",
        "v7full": "magi_think_v7full/Magistral-Small-2509"}),
    ("Qwen3.6-27B (Inst)", {
        "v3": "qwen36_v3/Qwen3.6-27B", "v4": "qwen36_v4/Qwen3.6-27B"}),
    ("Qwen3.6-27B (Think)", {
        "v3": "simple_36/Qwen3.6-27B"}),
]

def f1(sub):
    for root in ("results_norm2", "results_norm"):
        d = os.path.join(root, sub)
        if os.path.isdir(d):
            r = subprocess.run([sys.executable, "score_v2.py",
                                "--gold", "data/gold_answers_norm.jsonl",
                                "--pred_dir", d],
                               capture_output=True, text=True, timeout=1800)
            m = re.search(r"F1\s*=\s*([\d.]+)", r.stdout)
            if m:
                return float(m.group(1))
    return None

def seconds(sub):
    fs = glob.glob(os.path.join("results", sub) + "/*.txt")
    if len(fs) < 20:
        return None
    ts = sorted(Path(f).stat().st_mtime for f in fs)
    gaps = sorted(b - c for c, b in zip(ts, ts[1:]) if 0 < b - c < 7200)
    return gaps[len(gaps) // 2] if gaps else None

labels = [r[0] for r in ROWS]
F = np.full((len(ROWS), len(VERSIONS)), np.nan)
S = np.full((len(ROWS), len(VERSIONS)), np.nan)
records = []

for i, (label, mapping) in enumerate(ROWS):
    for j, v in enumerate(VERSIONS):
        sub = mapping.get(v)
        if not sub:
            continue
        score, sec = f1(sub), seconds(sub)
        if score is not None:
            F[i, j] = score
        if sec is not None:
            S[i, j] = sec
        print(f"  {label:24s} {v:7s} F1={score}  {sec}s", flush=True)
        records.append({"model": label, "prompt": v, "dir": sub,
                        "F1": score, "sec_per_abstract": sec})

def heatmap(ax, M, fmt, cmap, title, cbar_label, vmin=None, vmax=None):
    masked = np.ma.masked_invalid(M)
    cm = plt.get_cmap(cmap).copy()
    cm.set_bad("#F2F2F2")
    im = ax.imshow(masked, cmap=cm, aspect="auto", vmin=vmin, vmax=vmax)
    lo, hi = np.nanmin(M), np.nanmax(M)
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if np.isnan(M[i, j]):
                ax.text(j, i, "–", ha="center", va="center",
                        color="#AAA", fontsize=9)
            else:
                rel = (M[i, j] - lo) / (hi - lo + 1e-9)
                ax.text(j, i, fmt.format(M[i, j]), ha="center", va="center",
                        fontsize=8.5,
                        color="white" if rel > 0.62 else "black")
    ax.set_xticks(range(len(VERSIONS)))
    ax.set_xticklabels(VERSIONS, rotation=45, ha="right")
    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)
    ax.set_title(title, loc="left", fontweight="bold", pad=10)
    ax.set_xticks(np.arange(-.5, len(VERSIONS), 1), minor=True)
    ax.set_yticks(np.arange(-.5, len(labels), 1), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.6)
    ax.tick_params(which="minor", length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = plt.colorbar(im, ax=ax, fraction=.030, pad=.02)
    cb.set_label(cbar_label, fontsize=9)

fig, ax = plt.subplots(figsize=(9.5, 5.2))
heatmap(ax, F, "{:.3f}", "YlGnBu", "A   Extraction accuracy", "F1 (gene level)")
ax.set_xlabel("Prompt version")
for ext in ("png", "pdf"):
    fig.savefig(f"{a.prefix}_f1.{ext}", dpi=300, bbox_inches="tight")
print(f"\nsaved {a.prefix}_f1.png")
plt.close(fig)

fig, ax = plt.subplots(figsize=(9.5, 5.2))
heatmap(ax, S, "{:.0f}", "OrRd", "B   Generation time",
        "Median seconds per abstract")
ax.set_xlabel("Prompt version")
for ext in ("png", "pdf"):
    fig.savefig(f"{a.prefix}_time.{ext}", dpi=300, bbox_inches="tight")
print(f"saved {a.prefix}_time.png")

with open(f"{a.prefix}.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["model", "prompt", "dir",
                                       "F1", "sec_per_abstract"])
    w.writeheader(); [w.writerow(r) for r in records]
print(f"saved {a.prefix}.csv")
