#!/usr/bin/env python3
"""
plot_prompt_progression.py - F1 across prompt versions for one model.
Two lines: raw output and after HGNC normalisation.
"""
import os, re, sys, csv, subprocess, argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("--run_prefix", default="psweep_")
ap.add_argument("--model_dir", default="Qwen3-8B")
ap.add_argument("--title", default="Qwen3-8B (instruct)")
ap.add_argument("--versions", nargs="+",
                default=["v1", "v2", "v3", "v4", "v5", "v6lite"])
ap.add_argument("--out", default="results/prompt_progression")
a = ap.parse_args()

def f1(pred_dir, gold):
    if not os.path.isdir(pred_dir):
        return None
    r = subprocess.run([sys.executable, "score_v2.py", "--gold", gold,
                        "--pred_dir", pred_dir], capture_output=True,
                       text=True, timeout=1800)
    m = re.search(r"F1\s*=\s*([\d.]+)", r.stdout)
    return float(m.group(1)) if m else None

raw, norm = [], []
for v in a.versions:
    sub = f"{a.run_prefix}{v}/{a.model_dir}"
    raw.append(f1(os.path.join("results", sub), "data/gold_answers.jsonl"))
    norm.append(f1(os.path.join("results_norm", sub), "data/gold_answers_norm.jsonl"))
    print(f"  {v:8s} raw={raw[-1]}  hgnc={norm[-1]}", flush=True)

x = range(len(a.versions))
# second panel: how many papers the model rejected outright
import glob
rejected = []
for v in a.versions:
    d = os.path.join("results", f"{a.run_prefix}{v}/{a.model_dir}")
    fs = glob.glob(d + "/*.txt")
    rejected.append(sum(1 for f in fs
                        if '"result"' in open(f, encoding="utf-8",
                                              errors="ignore").read()))
    print(f"  {a.versions[len(rejected)-1]:8s} rejected {rejected[-1]}/{len(fs)}", flush=True)

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 5))
ax.plot(x, raw,  "-o", color="#BDBDBD", lw=2, ms=8, label="Raw output")
ax.plot(x, norm, "-o", color="#3C8DBC", lw=2.5, ms=9, label="After HGNC normalisation")

for i, (r, n) in enumerate(zip(raw, norm)):
    if n is not None:
        ax.annotate(f"{n:.3f}", (i, n), fontsize=8, ha="center",
                    xytext=(0, 9), textcoords="offset points", color="#2C7FB8")
    if r is not None:
        ax.annotate(f"{r:.3f}", (i, r), fontsize=8, ha="center",
                    xytext=(0, -14), textcoords="offset points", color="#888")

best = max((n for n in norm if n is not None), default=None)
if best is not None:
    ax.axhline(best, ls=":", color="#bbb", lw=1, zorder=0)

ax.set_xticks(list(x))
ax.set_xticklabels(a.versions)
ax.set_xlabel("Prompt version")
ax.set_ylabel("F1 (gene level)")
ax.set_title(f"Prompt development — {a.title}", loc="left", fontweight="bold")
ax.legend(fontsize=9, frameon=False, loc="lower right")
ax.grid(axis="y", alpha=.25); ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.suptitle("267-paper OATargets set (175 positives + 92 true negatives)",
             fontsize=9, y=.97, color="#555")

ax2.bar([str(v) for v in a.versions], rejected, color="#E8482C", alpha=.85, width=.55)
ax2.axhline(92, ls="--", color="black", lw=1.4,
            label="True negatives in the set (92)")
ax2.set_xlabel("Prompt version"); ax2.set_ylabel("Papers rejected outright")
ax2.set_title("Rejection rate", loc="left", fontweight="bold")
ax2.legend(fontsize=9, frameon=False)
ax2.grid(axis="y", alpha=.25); ax2.set_axisbelow(True)
for sp in ("top", "right"):
    ax2.spines[sp].set_visible(False)

for ext in ("png", "pdf"):
    fig.savefig(f"{a.out}.{ext}", dpi=220, bbox_inches="tight")

with open(a.out + ".csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["prompt", "F1_raw", "F1_hgnc"])
    for v, r, n in zip(a.versions, raw, norm):
        w.writerow([v, r, n])
print(f"\nsaved {a.out}.png and {a.out}.csv")
