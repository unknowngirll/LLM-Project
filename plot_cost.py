#!/usr/bin/env python3
"""
plot_cost.py - accuracy against compute cost.

Throughput is estimated from the gaps between consecutive output-file
timestamps, taking the median so that queue stalls and the initial model
load do not dominate. Runs were scheduled across several GPU types, so
these figures are indicative rather than a controlled benchmark.
"""
import os, re, sys, csv, glob, statistics, subprocess, argparse
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 11, "axes.linewidth": 0.9,
                     "legend.frameon": False})

ap = argparse.ArgumentParser()
ap.add_argument("--corpus", type=int, default=11000)
ap.add_argument("--prefix", default="results/cost")
a = ap.parse_args()

RUNS = [
    ("Qwen3.5-4B",      4,  "Instruct", "v3",     "nothink_35/Qwen3.5-4B"),
    ("Llama-3.1-8B",    8,  "Instruct", "v3",     "llama31_v3/Llama-3.1-8B-Instruct"),
    ("Qwen3-8B",        8,  "Instruct", "v5",     "psweep_v5/Qwen3-8B"),
    ("Qwen3-8B",        8,  "Thinking", "v3",     "simple_8b/Qwen3-8B"),
    ("Qwen3-8B",        8,  "Thinking", "v6full", "q8b_think_v6full/Qwen3-8B"),
    ("Qwen3-8B",        8,  "Thinking", "v7full", "q8b_think_v7full/Qwen3-8B"),
    ("Gemma-4-12B",    12,  "Thinking", "v6full", "gemma4_v6/gemma-4-12B-it"),
    ("Magistral-Small",24,  "Instruct", "v3",     "magistral_v3_new/Magistral-Small-2509"),
    ("Magistral-Small",24,  "Thinking", "v6full", "magi_think_v6/Magistral-Small-2509"),
    ("Magistral-Small",24,  "Thinking", "v7full", "magi_think_v7full/Magistral-Small-2509"),
    ("Qwen3.6-27B",    27,  "Instruct", "v3",     "qwen36_v3/Qwen3.6-27B"),
    ("Qwen3.6-27B",    27,  "Thinking", "v3",     "simple_36/Qwen3.6-27B"),
]

JOBNAME = {
    "nothink_35/Qwen3.5-4B": "n_q35",
    "llama31_v3/Llama-3.1-8B-Instruct": "llama31",
    "psweep_v5/Qwen3-8B": "p_v5",
    "simple_8b/Qwen3-8B": "s_q8b",
    "q8b_think_v6full/Qwen3-8B": "q8b_v6f",
    "q8b_think_v7full/Qwen3-8B": "q8b_v7full",
    "gemma4_v6/gemma-4-12B-it": "gem4_v6",
    "magistral_v3_new/Magistral-Small-2509": "magi_v3",
    "magi_think_v6/Magistral-Small-2509": "magi_v6",
    "magi_think_v7full/Magistral-Small-2509": "magi_v7full",
    "qwen36_v3/Qwen3.6-27B": "q36_v3",
    "simple_36/Qwen3.6-27B": "s_q36",
}

COLOUR = {"Qwen3.5-4B": "#BDBDBD", "Qwen3-8B": "#3C8DBC",
          "Llama-3.1-8B": "#9E9E9E", "Gemma-4-12B": "#E8A33D",
          "Magistral-Small": "#1B9E77", "Qwen3.6-27B": "#7B52AB"}
MARKER = {"Instruct": "o", "Thinking": "^"}

def gpu_class(node):
    """Map a Barkla2 node name to its partition class."""
    m = re.match(r"gpu(\d+)", node or "")
    if not m:
        return "?"
    n = int(m.group(1))
    return "H100" if 31 <= n <= 32 else ("L40S" if 41 <= n <= 43 else "A-low")

def node_lookup():
    """jobname -> node, taken from the longest run of each name."""
    r = subprocess.run(["sacct", "-u", os.environ.get("USER", ""),
                        "--starttime", "2026-07-01",
                        "--format=JobName%20,NodeList%12,ElapsedRaw", "-X", "-P", "-n"],
                       capture_output=True, text=True)
    best = {}
    for line in r.stdout.splitlines():
        parts = line.split("|")
        if len(parts) < 3:
            continue
        name, node, el = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if not el.isdigit():
            continue
        if name not in best or int(el) > best[name][1]:
            best[name] = (node, int(el))
    return {k: v[0] for k, v in best.items()}

NODES = node_lookup()

def seconds_per_paper(sub):
    fs = glob.glob(os.path.join("results", sub) + "/*.txt")
    if len(fs) < 20:
        return None
    ts = sorted(Path(f).stat().st_mtime for f in fs)
    gaps = sorted(b - a for a, b in zip(ts, ts[1:]) if 0 < b - a < 7200)
    return gaps[len(gaps) // 2] if gaps else None

def f1(sub):
    d = os.path.join("results_norm2", sub)
    if not os.path.isdir(d):
        d = os.path.join("results_norm", sub)
    if not os.path.isdir(d):
        return None
    r = subprocess.run([sys.executable, "score_v2.py",
                        "--gold", "data/gold_answers_norm.jsonl",
                        "--pred_dir", d], capture_output=True, text=True, timeout=1800)
    m = re.search(r"F1\s*=\s*([\d.]+)", r.stdout)
    return float(m.group(1)) if m else None

rows = []
for model, params, mode, prompt, sub in RUNS:
    sec, score = seconds_per_paper(sub), f1(sub)
    if sec is None or score is None:
        print(f"  skip: {sub}", flush=True); continue
    hours = sec * a.corpus / 3600
    job = JOBNAME.get(sub, "")
    gpu = gpu_class(NODES.get(job, ""))
    rows.append({"model": model, "params": params, "mode": mode,
                 "prompt": prompt, "sec": sec, "F1": score, "gpu_h": hours,
                 "job": job, "gpu": gpu})
    print(f"  {model:16s} {mode:9s} {prompt:7s} {sec:6.0f} s/paper  "
          f"F1={score:.3f}  {hours:5.0f} GPU-h  [{gpu}]", flush=True)

# ---------- figure 1: accuracy against throughput ----------
fig, ax = plt.subplots(figsize=(8.5, 5.4))
for r in rows:
    ax.scatter(r["sec"], r["F1"], s=50 + r["params"] * 13,
               marker=MARKER[r["mode"]], color=COLOUR.get(r["model"], "#888"),
               edgecolor="#333", lw=.8, zorder=3, alpha=.9)
    ax.annotate(f"{r['model'].split('-')[0]} {r['prompt']} [{r['gpu']}]",
                (r["sec"], r["F1"]), fontsize=7.5, color="black",
                xytext=(7, 5), textcoords="offset points", zorder=4)

ax.set_xscale("log")
ax.set_xlabel("Median seconds per abstract (log scale)")
ax.set_ylabel("F1 (gene level, normalised)")
handles = [plt.Line2D([], [], marker=MARKER[m], ls="", color="#999",
                      markeredgecolor="#333", markersize=8, label=m)
           for m in ("Instruct", "Thinking")]
handles += [plt.Line2D([], [], marker="s", ls="", color=c,
                       markeredgecolor="#333", markersize=8, label=k)
            for k, c in COLOUR.items() if any(r["model"] == k for r in rows)]
ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.02, 1.0),
          fontsize=9, borderaxespad=0)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(alpha=.22); ax.set_axisbelow(True)
for ext in ("png", "pdf"):
    fig.savefig(f"{a.prefix}_accuracy_vs_speed.{ext}", dpi=300, bbox_inches="tight")
print(f"\nsaved {a.prefix}_accuracy_vs_speed.png")
plt.close(fig)

# ---------- figure 2: projected GPU-hours ----------
rows.sort(key=lambda r: r["gpu_h"])
fig, ax = plt.subplots(figsize=(9, 5))
labels = [f"{r['model']}\n{r['mode'][:5]} {r['prompt']}" for r in rows]
ax.bar(range(len(rows)), [r["gpu_h"] for r in rows],
       color=[COLOUR.get(r["model"], "#888") for r in rows], width=.62)
for i, r in enumerate(rows):
    ax.annotate(f"{r['gpu_h']:.0f}", (i, r["gpu_h"]), ha="center", fontsize=8.5,
                color="black", xytext=(0, 4), textcoords="offset points")
ax.set_xticks(range(len(rows)))
ax.set_xticklabels(labels, fontsize=7.5, rotation=45, ha="right")
ax.set_ylabel(f"Projected GPU-hours for {a.corpus:,} abstracts")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.grid(axis="y", alpha=.22); ax.set_axisbelow(True)
for ext in ("png", "pdf"):
    fig.savefig(f"{a.prefix}_gpu_hours.{ext}", dpi=300, bbox_inches="tight")
print(f"saved {a.prefix}_gpu_hours.png")

with open(f"{a.prefix}.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["model", "params", "mode", "prompt",
                                       "sec", "F1", "gpu_h", "job", "gpu"])
    w.writeheader(); [w.writerow(r) for r in rows]
print(f"saved {a.prefix}.csv")
