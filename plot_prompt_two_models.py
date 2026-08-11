#!/usr/bin/env python3
"""
plot_prompt_two_models.py - prompt sweep across two models in thinking mode.
Writes two standalone figures with legends outside the axes.
"""
import os, re, sys, csv, glob, subprocess, argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({"font.size": 11, "axes.linewidth": 0.9,
                     "legend.frameon": False})

ap = argparse.ArgumentParser()
ap.add_argument("--prefix", default="results/prompt_two_models")
a = ap.parse_args()

VERSIONS = ["v1", "v2", "v3", "v4", "v5", "v6lite", "v6full"]

MODELS = {
    "Qwen3-8B": ("#3C8DBC", {
        "v1": "qthink_v1/Qwen3-8B",
        "v2": "qthink_v2/Qwen3-8B",
        "v3": "simple_8b/Qwen3-8B",
        "v4": "qthink_v4/Qwen3-8B",
        "v5": "v5_think_8b/Qwen3-8B",
        "v6lite": "q8b_think_v6lite/Qwen3-8B",
        "v6full": "q8b_think_v6full/Qwen3-8B",
    }),
    "Magistral-Small": ("#1B9E77", {
        "v1": "magi_think_v1/Magistral-Small-2509",
        "v2": "magi_think_v2/Magistral-Small-2509",
        "v3": "magi_think_v3/Magistral-Small-2509",
        "v4": "magi_think_v4/Magistral-Small-2509",
        "v5": "magi_think_v5/Magistral-Small-2509",
        "v6lite": "magi_think_v6lite/Magistral-Small-2509",
        "v6full": "magi_think_v6/Magistral-Small-2509",
    }),
}

def f1(sub):
    d = os.path.join("results_norm", sub)
    if not os.path.isdir(d):
        return None
    r = subprocess.run([sys.executable, "score_v2.py",
                        "--gold", "data/gold_answers_norm.jsonl",
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

data, rows = {}, []
for name, (col, dirs) in MODELS.items():
    data[name] = {}
    print(f"\n=== {name} ===", flush=True)
    for v in VERSIONS:
        data[name][v] = {"F1": f1(dirs[v]), "rej": rejected(dirs[v])}
        print(f"  {v:8s} F1={data[name][v]['F1']}  rejected={data[name][v]['rej']}",
              flush=True)
        rows.append({"model": name, "version": v,
                     "F1": data[name][v]["F1"], "rejected": data[name][v]["rej"]})

x = list(range(len(VERSIONS)))

# ---- figure 1: F1 ----
fig, ax = plt.subplots(figsize=(8.5, 4.8))
for name, (col, _) in MODELS.items():
    xs = [i for i, v in enumerate(VERSIONS) if data[name][v]["F1"] is not None]
    ys = [data[name][v]["F1"] for v in VERSIONS if data[name][v]["F1"] is not None]
    if not xs:
        continue
    ax.plot(xs, ys, "-o", color=col, lw=2.4, ms=8, label=name)
    for i, y in zip(xs, ys):
        ax.annotate(f"{y:.3f}", (i, y), fontsize=8, ha="center", color="black",
                    xytext=(0, 10), textcoords="offset points")

vals = [d["F1"] for m in data.values() for d in m.values() if d["F1"] is not None]
pad = (max(vals) - min(vals)) * 0.30 or 0.02
ax.set_ylim(min(vals) - pad, max(vals) + pad)
ax.set_xticks(x)
ax.set_xticklabels(VERSIONS)
ax.set_xlim(-0.45, len(VERSIONS) - 0.55)
ax.set_xlabel("Prompt version")
ax.set_ylabel("F1 (gene level, HGNC-normalised)")
ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=10, borderaxespad=0)
tidy(ax)
for ext in ("png", "pdf"):
    fig.savefig(f"{a.prefix}_f1.{ext}", dpi=300, bbox_inches="tight")
print(f"\nsaved {a.prefix}_f1.png")
plt.close(fig)

# ---- figure 2: rejection ----
fig, ax = plt.subplots(figsize=(8.5, 4.8))
w = 0.38
for k, (name, (col, _)) in enumerate(MODELS.items()):
    xs = [i + (k - 0.5) * w for i, v in enumerate(VERSIONS)
          if data[name][v]["rej"] is not None]
    ys = [data[name][v]["rej"] for v in VERSIONS if data[name][v]["rej"] is not None]
    if xs:
        ax.bar(xs, ys, width=w, color=col, label=name)
ax.axhline(92, ls="--", color="#333", lw=1.3, label="True negatives in set (92)")
ax.set_xticks(x)
ax.set_xticklabels(VERSIONS)
ax.set_xlabel("Prompt version")
ax.set_ylabel("Abstracts rejected outright")
ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=10, borderaxespad=0)
tidy(ax)
for ext in ("png", "pdf"):
    fig.savefig(f"{a.prefix}_rejection.{ext}", dpi=300, bbox_inches="tight")
print(f"saved {a.prefix}_rejection.png")

with open(f"{a.prefix}.csv", "w", newline="", encoding="utf-8") as fh:
    w2 = csv.DictWriter(fh, fieldnames=["model", "version", "F1", "rejected"])
    w2.writeheader()
    [w2.writerow(r) for r in rows]
print(f"saved {a.prefix}.csv")
