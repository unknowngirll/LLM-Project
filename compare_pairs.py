#!/usr/bin/env python3
"""compare_pairs.py - thinking vs non-thinking, paired by model family."""
import os, re, sys, glob, csv, subprocess

GOLD = "data/gold_answers.jsonl"
OUT  = "results/pairs_table.csv"

# (family, mode, dir, prompt, set-size)   <-- edit paths after the discovery step
SPEC = [
    ("Qwen3-4B",    "Instruct", "results/dev/Qwen3-4B-Instruct-2507",        "v2", 175),
    ("Qwen3-4B",    "Thinking", "results/dev/Qwen3-4B-Thinking-2507",    "v2", 175),
    ("Qwen3-8B",    "Instruct", "results/dev/Qwen3-8B",                  "v2", 175),
    ("Qwen3-8B",    "Thinking", "results/simple_8b/Qwen3-8B",            "v3", 267),
    ("Qwen3.6-27B", "Instruct", "results/qwen36_v3/Qwen3.6-27B",         "v3", 267),
    ("Qwen3.6-27B", "Thinking", "results/simple_36/Qwen3.6-27B",         "v3", 267),
]

def health(d):
    fs = [f for f in glob.glob(d + "/*.txt") if not f.endswith("_raw.txt")]
    if not fs:
        return None
    tot = sum(os.path.getsize(f) for f in fs)
    cl = sum(1 for f in fs if "</think>" in open(f, encoding="utf-8", errors="ignore").read())
    return {"n": len(fs), "kb": tot/len(fs)/1024, "think": 100.0*cl/len(fs),
            "loop": sum(1 for f in fs if os.path.getsize(f) > 35*1024)}

def score(d):
    r = subprocess.run([sys.executable, "score_v2.py", "--gold", GOLD, "--pred_dir", d],
                       capture_output=True, text=True, timeout=1800)
    t = r.stdout
    def g(p, c=float):
        m = re.search(p, t); return c(m.group(1)) if m else None
    o = {"scored": g(r"Files scored:\s*(\d+)", int), "fail": g(r"parse failures:\s*(\d+)", int),
         "TP": g(r"TP=(\d+)", int), "FP": g(r"FP=(\d+)", int),
         "FN": g(r"FN=(\d+)", int), "TN": g(r"TN=(\d+)", int),
         "P": g(r"Precision.*?=\s*([\d.]+)"), "R": g(r"Recall.*?=\s*([\d.]+)"),
         "F1": g(r"F1\s*=\s*([\d.]+)")}
    for f in ("outcome", "induction", "species"):
        o[f] = g(rf"{f}\s+accuracy=([\d.]+)")
    return o

rows = []
for fam, mode, d, prm, exp in SPEC:
    h = health(d)
    if h is None:
        print(f"  MISSING: {d}", flush=True); continue
    print(f"  scoring {fam:12s} {mode:9s} ({h['n']} files) ...", flush=True)
    rows.append({"family": fam, "mode": mode, "dir": d, "prompt": prm,
                 "expected": exp, **h, **score(d)})

def cell(r, k, w=6, p=3):
    v = r.get(k); return f"{v:{w}.{p}f}" if isinstance(v, float) else f"{'-':>{w}s}"

hdr = (f"{'model':13s} {'mode':9s} {'pr':3s} {'n':>4s} {'F1':>6s} {'P':>6s} {'R':>6s} "
       f"{'TN':>4s} {'ind':>5s} {'out':>5s} {'sp':>5s} {'fail':>5s} {'KB':>6s} {'th%':>4s}")
print("\n" + hdr); print("-"*len(hdr))
for fam in ["Qwen3-4B", "Qwen3-8B", "Qwen3.6-27B"]:
    grp = [r for r in rows if r["family"] == fam]
    for r in grp:
        flag = ""
        if (r.get("fail") or 0) > 10: flag += " !parse"
        if r["n"] != r["expected"]:   flag += f" !{r['n']}of{r['expected']}"
        print(f"{fam:13s} {r['mode']:9s} {r['prompt']:3s} {r['n']:4d} "
              f"{cell(r,'F1')} {cell(r,'P')} {cell(r,'R')} {r.get('TN') or 0:4d} "
              f"{cell(r,'induction',5)} {cell(r,'outcome',5)} {cell(r,'species',5)} "
              f"{r.get('fail') or 0:5d} {r['kb']:6.1f} {r['think']:3.0f}%{flag}")
    if len(grp) == 2 and all(g.get("F1") is not None for g in grp):
        ins = next(g for g in grp if g["mode"] == "Instruct")
        thk = next(g for g in grp if g["mode"] == "Thinking")
        d = thk["F1"] - ins["F1"]
        same = (ins["prompt"] == thk["prompt"] and ins["n"] == thk["n"])
        note = "" if same else "   (different prompt/set - NOT a fair pair)"
        print(f"{'':13s} {'delta F1':9s} {'':3s} {'':4s} {d:+6.3f}{note}")
    print()

os.makedirs("results", exist_ok=True)
cols = ["family","mode","prompt","dir","n","expected","scored","F1","P","R",
        "TP","FP","FN","TN","induction","outcome","species","fail","kb","think","loop"]
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader(); [w.writerow(r) for r in rows]
print(f"Saved -> {OUT}")
