#!/usr/bin/env python3
"""analyse_temperature.py - aggregate the temperature sweep, mean +/- sd across seeds."""
import os, re, sys, glob, csv, statistics, subprocess, argparse

ap = argparse.ArgumentParser()
ap.add_argument("--gold", default="data/gold_answers.jsonl")
ap.add_argument("--csv", default="results/temperature_sweep.csv")
ap.add_argument("--md",  default="RESULTS_temperature.md")
a = ap.parse_args()

def parse_tag(tag):
    m = re.match(r"t(\d+)_s(\d+)", tag)
    if not m: return None, None
    raw = m.group(1)
    temp = float(raw[0] + "." + raw[1:]) if len(raw) > 1 else float(raw)
    return temp, int(m.group(2))

def score(d):
    r = subprocess.run([sys.executable, "score_v2.py", "--gold", a.gold,
                        "--pred_dir", d], capture_output=True, text=True, timeout=1800)
    t = r.stdout
    def g(p, c=float):
        m = re.search(p, t); return c(m.group(1)) if m else None
    o = {"F1": g(r"F1\s*=\s*([\d.]+)"), "P": g(r"Precision.*?=\s*([\d.]+)"),
         "R": g(r"Recall.*?=\s*([\d.]+)"), "fail": g(r"parse failures:\s*(\d+)", int)}
    return o if o["F1"] is not None else None

def health(d):
    fs = glob.glob(d + "/*.txt")
    if not fs: return {}
    cl = sum(1 for f in fs if "</think>" in open(f, encoding="utf-8", errors="ignore").read())
    return {"n": len(fs), "closed_pct": 100.0*cl/len(fs),
            "looped": sum(1 for f in fs if os.path.getsize(f) > 35*1024),
            "avg_kb": sum(os.path.getsize(f) for f in fs)/len(fs)/1024}

rows = []
for d in sorted(glob.glob("results/tsweep_*/*")):
    if not os.path.isdir(d): continue
    tag = os.path.basename(os.path.dirname(d)).replace("tsweep_", "")
    temp, seed = parse_tag(tag)
    if temp is None: continue
    h = health(d)
    if h.get("n", 0) < 250:
        print(f"  SKIP {tag} ({h.get('n',0)} files)", flush=True); continue
    s = score(d)
    if s is None: continue
    rows.append({"temp": temp, "seed": seed, **h, **s})

rows.sort(key=lambda r: (r["temp"], r["seed"]))
print("\n=== per run ===")
print(f"{'temp':>5s} {'seed':>4s} {'F1':>6s} {'P':>6s} {'R':>6s} {'closed%':>8s} {'loop':>5s} {'KB':>6s}")
for r in rows:
    print(f"{r['temp']:5.1f} {r['seed']:4d} {r['F1']:6.3f} {r['P']:6.3f} {r['R']:6.3f} "
          f"{r['closed_pct']:7.0f}% {r['looped']:5d} {r['avg_kb']:6.1f}")

by = {}
for r in rows: by.setdefault(r["temp"], []).append(r)
def agg(v): return (statistics.mean(v), statistics.stdev(v) if len(v) > 1 else 0.0)

print("\n=== aggregated across seeds ===")
print(f"{'temp':>5s} {'n':>3s} {'F1 mean':>9s} {'sd':>7s} {'P':>7s} {'R':>7s} {'closed%':>8s} {'loop':>6s}")
summ = []
for t in sorted(by):
    g = by[t]
    f1m, f1s = agg([x["F1"] for x in g])
    pm, _ = agg([x["P"] for x in g]); rm, _ = agg([x["R"] for x in g])
    cm, _ = agg([x["closed_pct"] for x in g]); lm, _ = agg([float(x["looped"]) for x in g])
    summ.append({"temp": t, "n": len(g), "F1_mean": f1m, "F1_sd": f1s,
                 "P": pm, "R": rm, "closed": cm, "loop": lm})
    print(f"{t:5.1f} {len(g):3d} {f1m:9.3f} {f1s:7.3f} {pm:7.3f} {rm:7.3f} {cm:7.0f}% {lm:6.1f}")

if summ:
    best = max(summ, key=lambda x: x["F1_mean"])
    spread = max(x["F1_mean"] for x in summ) - min(x["F1_mean"] for x in summ)
    noise = max(x["F1_sd"] for x in summ)
    print(f"\nbest temperature : {best['temp']}  (F1 {best['F1_mean']:.3f})")
    print(f"spread across temps : {spread:.3f}")
    print(f"largest within-temp sd : {noise:.3f}")
    print("verdict:", "temperature effect exceeds sampling noise"
          if spread > 2*noise else
          "temperature effect within sampling noise — inconclusive")

os.makedirs("results", exist_ok=True)
with open(a.csv, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["temp","seed","n","F1","P","R","fail","closed_pct","looped","avg_kb"], extrasaction="ignore")
    w.writeheader(); [w.writerow(r) for r in rows]

with open(a.md, "w", encoding="utf-8") as fh:
    fh.write("# Temperature sweep\n\nQwen3-8B, thinking mode, v3 prompts, 267 papers, "
             "top_p=0.95, top_k=20. Three seeds per temperature.\n\n")
    fh.write("| Temp | Seeds | F1 mean | F1 sd | Precision | Recall | Thought closed | Looped |\n")
    fh.write("|---|---|---|---|---|---|---|---|\n")
    for s in summ:
        fh.write(f"| {s['temp']} | {s['n']} | **{s['F1_mean']:.3f}** | {s['F1_sd']:.3f} | "
                 f"{s['P']:.3f} | {s['R']:.3f} | {s['closed']:.0f}% | {s['loop']:.1f} |\n")
print(f"\nCSV -> {a.csv}\nMarkdown -> {a.md}")
