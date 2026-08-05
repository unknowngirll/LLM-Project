#!/usr/bin/env python3
"""
plot_prompt_per_mode.py - prompt-version sweep for Qwen3-8B.

Writes four standalone figures, one panel each, with legends placed outside
the axes so they never overlap the data. Titles are kept minimal on the
assumption that captions live in the manuscript.
"""
import os, re, sys, csv, glob, subprocess, argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.size": 11,
    "axes.linewidth": 0.9,
    "xtick.direction": "out",
    "ytick.direction": "out",
    "legend.frameon": False,
})

ap = argparse.ArgumentParser()
ap.add_argument("--prefix", default="results/prompt_sweep")
a = ap.parse_args()

VERSIONS = ["v1", "v2", "v3", "v4", "v5", "v6lite", "v6full"]

MODES = {
    "instruct": ("#E8A33D", {v: f"psweep_{v}/Qwen3-8B" for v in VERSIONS}),
    "thinking": ("#3C8DBC", {
        "v1": "qthink_v1/Qwen3-8B",
        "v2": "qthink_v2/Qwen3-8B",
        "v3": "simple_8b/Qwen3-8B",
        "v4": "qthink_v4/Qwen3-8B",
        "v5": "v5_think_8b/Qwen3-8B",
        "v6lite": "q8b_think_v6lite/Qwen3-8B",
        "v6full": "q8b_think_v6full/Qwen3-8B",
    }),
}

def f1(sub, root, gold):
    d = os.path.join(root, sub)
    if not os.path.isdir(d):
        return None
    r = subprocess.run([sys.executable, "score_v2.py", "--gold", gold,
                        "--pred_dir", d], capture_output=True, text=True, timeout=1800)
    m = re.search(r"F1\s*=\s*([\d.]+)", r.stdout)
    return float(m.group(1)) if m else None

def rejected(sub):
    fs = glob.glob(os.path.join("results", sub) + "/*.txt")
    if not fs:
        return None
    return sum(1 for f in fs
               if '"result"' in open(f, encoding="utf-8", errors="ignore").read())

def tidy(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", alpha=.22, lw=.8)
    ax.set_axisbelow(True)

rows = []
for mode, (col, dirs) in MODES.items():
    print(f"\n=== {mode} ===", flush=True)
    raw, norm, rej = [], [], []
    for v in VERSIONS:
        raw.append(f1(dirs[v], "results", "data/gold_answers.jsonl"))
        norm.append(f1(dirs[v], "results_norm", "data/gold_answers_norm.jsonl"))
        rej.append(rejected(dirs[v]))
        print(f"  {v:8s} raw={raw[-1]}  hgnc={norm[-1]}  rejected={rej[-1]}", flush=True)
        rows.append({"mode": mode, "version": v, "F1_raw": raw[-1],
                     "F1_hgnc": norm[-1], "rejected": rej[-1]})

    x = list(range(len(VERSIONS)))

    # ---------------- figure 1: F1 ----------------
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.plot(x, raw,  "-o", color="#9E9E9E", lw=1.8, ms=6, label="Raw output")
    ax.plot(x, norm, "-o", color=col,      lw=2.4, ms=8,
            label="After HGNC normalisation")

    vals = [v for v in raw + norm if v is not None]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.18 or 0.02
    ax.set_ylim(lo - pad, hi + pad)

    for i, (r, n) in enumerate(zip(raw, norm)):
        if n is not None:
            ax.annotate(f"{n:.3f}", (i, n), fontsize=8, ha="center", color="black",

                        xytext=(0, 10), textcoords="offset points")
        if r is not None:
            ax.annotate(f"{r:.3f}", (i, r), fontsize=8, ha="center", color="black",
                        xytext=(0, -16), textcoords="offset points")

    ax.set_xticks(x); ax.set_xticklabels(VERSIONS)
    ax.set_xlim(-0.45, len(VERSIONS) - 0.55)
    ax.set_xlabel("Prompt version")
    ax.set_ylabel("F1 (gene level)")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=10,
              borderaxespad=0)
    tidy(ax)
    out = f"{a.prefix}_{mode}_f1"
    for ext in ("png", "pdf"):
        fig.savefig(f"{out}.{ext}", dpi=300, bbox_inches="tight")
    print(f"  saved {out}.png", flush=True)
    plt.close(fig)

    # ---------------- figure 2: rejection rate ----------------
    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    ax.bar(x, [r or 0 for r in rej], color=col, width=.6, alpha=.9,
           label="Abstracts rejected")
    ax.axhline(92, ls="--", color="#333", lw=1.3,
               label="True negatives in set (92)")
    for i, r in enumerate(rej):
        if r is not None:
            ax.annotate(str(r), (i, r), fontsize=9, ha="center",color="black",
                        xytext=(0, 5), textcoords="offset points")

    top = max([r for r in rej if r is not None] + [92])
    ax.set_ylim(0, top * 1.18)
    ax.set_xticks(x); ax.set_xticklabels(VERSIONS)
    ax.set_xlabel("Prompt version")
    ax.set_ylabel("Abstracts rejected outright")
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=10,
              borderaxespad=0)
    tidy(ax)
    out = f"{a.prefix}_{mode}_rejection"
    for ext in ("png", "pdf"):
        fig.savefig(f"{out}.{ext}", dpi=300, bbox_inches="tight")
    print(f"  saved {out}.png", flush=True)
    plt.close(fig)

with open(f"{a.prefix}.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["mode", "version", "F1_raw",
                                       "F1_hgnc", "rejected"])
    w.writeheader(); [w.writerow(r) for r in rows]
print(f"\nsaved {a.prefix}.csv")
