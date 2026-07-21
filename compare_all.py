#!/usr/bin/env python3
"""
compare_all.py - score every result directory and build one comparison table.
Adds health columns (thinking / avg size / looped) so unusable runs are visible.
"""
import os, re, sys, glob, csv, subprocess, argparse

ap = argparse.ArgumentParser()
ap.add_argument("--root", default="results")
ap.add_argument("--gold", default="data/gold_answers.jsonl")
ap.add_argument("--out", default="results/comparison_all.csv")
ap.add_argument("--min_files", type=int, default=20, help="skip tiny test dirs")
args = ap.parse_args()

def find_dirs(root):
    out = []
    for d, _, files in os.walk(root):
        if any(f.endswith(".txt") and not f.endswith("_raw.txt") for f in files):
            n = len([f for f in files if f.endswith(".txt") and not f.endswith("_raw.txt")])
            if n >= args.min_files:
                out.append((d, n))
    return sorted(out)

def health(d):
    fs = [f for f in glob.glob(d + "/*.txt") if not f.endswith("_raw.txt")]
    tot = closed = looped = 0
    for f in fs:
        sz = os.path.getsize(f)
        tot += sz
        if sz > 35 * 1024:
            looped += 1
        try:
            if "</think>" in open(f, encoding="utf-8", errors="ignore").read():
                closed += 1
        except Exception:
            pass
    return {"avg_kb": tot / len(fs) / 1024 if fs else 0,
            "think_pct": 100.0 * closed / len(fs) if fs else 0,
            "looped": looped}

def score(d):
    try:
        r = subprocess.run([sys.executable, "score_v2.py", "--gold", args.gold,
                            "--pred_dir", d], capture_output=True, text=True, timeout=900)
    except Exception as e:
        return {"error": str(e)[:40]}
    t = r.stdout
    def g(pat, cast=float):
        m = re.search(pat, t)
        return cast(m.group(1)) if m else None
    out = {
        "scored":    g(r"Files scored:\s*(\d+)", int),
        "parse_fail":g(r"parse failures:\s*(\d+)", int),
        "TP":        g(r"TP=(\d+)", int),
        "FP":        g(r"FP=(\d+)", int),
        "FN":        g(r"FN=(\d+)", int),
        "TN":        g(r"TN=(\d+)", int),
        "P":         g(r"Precision.*?=\s*([\d.]+)"),
        "R":         g(r"Recall.*?=\s*([\d.]+)"),
        "F1":        g(r"F1\s*=\s*([\d.]+)"),
    }
    for f in ["outcome", "induction", "species"]:
        out[f] = g(rf"{f}\s+accuracy=([\d.]+)")
    if out["F1"] is None:
        out["error"] = (r.stderr or t).strip().splitlines()[-1][:40] if (r.stderr or t).strip() else "no output"
    return out

dirs = find_dirs(args.root)
print(f"Found {len(dirs)} result directories (>= {args.min_files} files)\n")

rows = []
for d, n in dirs:
    print(f"  scoring {d} ({n}) ...", flush=True)
    h = health(d)
    s = score(d)
    rows.append({"dir": d.replace(args.root + "/", ""), "n_files": n, **h, **s})

rows.sort(key=lambda r: (r.get("F1") is None, -(r.get("F1") or 0)))

hdr = f"{'run':38s} {'n':>4s} {'sc':>4s} {'F1':>6s} {'P':>6s} {'R':>6s} {'TN':>4s} " \
      f"{'ind':>5s} {'out':>5s} {'sp':>5s} {'fail':>5s} {'KB':>6s} {'think%':>7s} {'loop':>5s}"
print("\n" + hdr)
print("-" * len(hdr))
for r in rows:
    if r.get("F1") is None:
        print(f"{r['dir'][:38]:38s} {r['n_files']:4d} {'':>4s} {'ERR':>6s}  {r.get('error','')[:40]}")
        continue
    def f(k, w=6, p=3):
        v = r.get(k)
        return f"{v:{w}.{p}f}" if isinstance(v, float) else f"{'-':>{w}s}"
    print(f"{r['dir'][:38]:38s} {r['n_files']:4d} {r.get('scored') or 0:4d} "
          f"{f('F1')} {f('P')} {f('R')} {r.get('TN') or 0:4d} "
          f"{f('induction',5)} {f('outcome',5)} {f('species',5)} "
          f"{r.get('parse_fail') or 0:5d} {r['avg_kb']:6.1f} {r['think_pct']:6.0f}% {r['looped']:5d}")

cols = ["dir","n_files","scored","F1","P","R","TP","FP","FN","TN",
        "induction","outcome","species","parse_fail","avg_kb","think_pct","looped","error"]
os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
with open(args.out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
print(f"\nSaved -> {args.out}")
