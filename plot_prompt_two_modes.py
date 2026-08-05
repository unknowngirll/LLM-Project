#!/usr/bin/env python3
"""
plot_prompt_two_modes.py - prompt-version sweep for Qwen3-8B in both modes.

Left panel  : F1 after HGNC normalisation, instruct vs thinking
Right panel : how many of the 267 papers the model rejected outright,
              which is the mechanism behind the F1 differences.
"""
import os, re, sys, csv, glob, subprocess, argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="results/prompt_two_modes")
a = ap.parse_args()

VERSIONS = ["v1", "v2", "v3", "v4", "v5", "v6lite", "v6full"]

INSTRUCT = {v: f"psweep_{v}/Qwen3-8B" for v in VERSIONS}
THINKING = {
    "v1": "qthink_v1/Qwen3-8B",
    "v2": "qthink_v2/Qwen3-8B",
    "v3": "simple_8b/Qwen3-8B",
    "v4": "qthink_v4/Qwen3-8B",
    "v5": "v5_think_8b/Qwen3-8B",
    "v6lite": "q8b_think_v6lite/Qwen3-8B",
    "v6full": "q8b_think_v6full/Qwen3-8B",
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

rows = []
for v in VERSIONS:
    r = {"version": v,
         "F1_instruct": f1(INSTRUCT[v]), "F1_thinking": f1(THINKING[v]),
         "rej_instruct": rejected(INSTRUCT[v]), "rej_thinking": rejected(THINKING[v])}
    rows.append(r)
    print(f"  {v:8s} instruct {r['F1_instruct']} (rej {r['rej_instruct']})   "
          f"thinking {r['F1_thinking']} (rej {r['rej_thinking']})", flush=True)

x = range(len(VERSIONS))
C_I, C_T = "#E8A33D", "#3C8DBC"

fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.5, 5))

# --- left: F1 ---
for key, col, lab in (("F1_instruct", C_I, "Instruct"),
                      ("F1_thinking", C_T, "Thinking")):
    ys = [r[key] for r in rows]
    ax.plot(x, ys, "-o", color=col, lw=2.4, ms=8, label=lab)
    for i, y in enumerate(ys):
        if y is not None:
            ax.annotate(f"{y:.3f}", (i, y), fontsize=7.5, ha="center", color=col,
                        xytext=(0, 9 if key == "F1_thinking" else -15),
                        textcoords="offset points")

ax.set_xticks(list(x)); ax.set_xticklabels(VERSIONS)
ax.set_xlabel("Prompt version"); ax.set_ylabel("F1 (gene level, HGNC-normalised)")
ax.set_title("A   Prompt development", loc="left", fontweight="bold")
ax.legend(fontsize=9, frameon=False, loc="lower left")
ax.grid(axis="y", alpha=.25); ax.set_axisbelow(True)

# --- right: rejection rate ---
w = 0.38
ax2.bar([i - w/2 for i in x], [r["rej_instruct"] or 0 for r in rows],
        width=w, color=C_I, label="Instruct")
ax2.bar([i + w/2 for i in x], [r["rej_thinking"] or 0 for r in rows],
        width=w, color=C_T, label="Thinking")
ax2.axhline(92, ls="--", color="black", lw=1.4,
            label="True negatives in the set (92)")
ax2.set_xticks(list(x)); ax2.set_xticklabels(VERSIONS)
ax2.set_xlabel("Prompt version"); ax2.set_ylabel("Papers rejected outright")
ax2.set_title("B   Rejection rate", loc="left", fontweight="bold")
ax2.legend(fontsize=9, frameon=False, loc="upper left")
ax2.grid(axis="y", alpha=.25); ax2.set_axisbelow(True)

for A in (ax, ax2):
    for s in ("top", "right"):
        A.spines[s].set_visible(False)

fig.suptitle("Qwen3-8B across prompt versions \u2014 267-paper OATargets set "
             "(175 positives + 92 true negatives)", fontsize=10, y=1.0, color="#555")

for ext in ("png", "pdf"):
    fig.savefig(f"{a.out}.{ext}", dpi=220, bbox_inches="tight")

with open(a.out + ".csv", "w", newline="", encoding="utf-8") as fh:
    w2 = csv.DictWriter(fh, fieldnames=["version", "F1_instruct", "F1_thinking",
                                        "rej_instruct", "rej_thinking"])
    w2.writeheader(); [w2.writerow(r) for r in rows]

print(f"\nsaved {a.out}.png and {a.out}.csv")
