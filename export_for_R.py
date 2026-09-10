#!/usr/bin/env python3
"""
export_for_R.py - score every run needed for the figures and write tidy CSVs.

Scoring stays in Python so that score_v2.py remains the single source of
truth; plotting is done separately in R from these files.
"""
import os, re, sys, csv, json, glob, subprocess
from collections import Counter, defaultdict
from pathlib import Path

OUT = "figdata"
os.makedirs(OUT, exist_ok=True)

GOLD_DEV  = "data/gold_answers_norm.jsonl"
GOLD_DEV_RAW = "data/gold_answers.jsonl"
GOLD_HO   = "data/gold_final_eval_norm.jsonl"
GOLD_HO_RAW = "data/gold_final_eval.jsonl"

def score(d, gold):
    if not os.path.isdir(d):
        return None
    n = len([f for f in glob.glob(d + "/*.txt") if not f.endswith("_raw.txt")])
    if n < 50:
        return None
    r = subprocess.run([sys.executable, "score_v2.py", "--gold", gold,
                        "--pred_dir", d], capture_output=True, text=True,
                       timeout=1800)
    t = r.stdout
    def g(p, c=float):
        m = re.search(p, t)
        return c(m.group(1)) if m else None
    o = {"n": n,
         "F1": g(r"F1\s*=\s*([\d.]+)"), "precision": g(r"Precision.*?=\s*([\d.]+)"),
         "recall": g(r"Recall.*?=\s*([\d.]+)"), "TP": g(r"TP=(\d+)", int),
         "FP": g(r"FP=(\d+)", int), "FN": g(r"FN=(\d+)", int),
         "TN": g(r"TN=(\d+)", int), "parse_fail": g(r"parse failures:\s*(\d+)", int)}
    for f in ("outcome", "induction", "species"):
        o[f] = g(rf"{f}\s+accuracy=([\d.]+)")
    return o if o["F1"] is not None else None

def rejected(sub):
    fs = glob.glob(os.path.join("results", sub) + "/*.txt")
    if not fs:
        return None
    return sum(1 for f in fs
               if '"result"' in open(f, encoding="utf-8", errors="ignore").read())

def seconds(sub):
    fs = glob.glob(os.path.join("results", sub) + "/*.txt")
    if len(fs) < 20:
        return None
    ts = sorted(Path(f).stat().st_mtime for f in fs)
    gaps = sorted(b - a for a, b in zip(ts, ts[1:]) if 0 < b - a < 7200)
    return gaps[len(gaps) // 2] if gaps else None

def write(name, rows, cols):
    p = os.path.join(OUT, name)
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"  {p}  ({len(rows)} rows)", flush=True)

# ---------------------------------------------------------------- fig 2
print("\n=== fig2: normalisation on prompt v1 ===", flush=True)
F2 = [("Qwen3-8B", "instruct", "v1", "psweep_v1/Qwen3-8B"),
      ("Qwen3-8B", "reasoning", "v1", "qthink_v1/Qwen3-8B"),
      ("Magistral-Small", "reasoning", "v1", "magi_think_v1/Magistral-Small-2509"),
      ("Qwen3-8B", "instruct", "v2", "psweep_v2/Qwen3-8B"),
      ("Qwen3-8B", "reasoning", "v2", "qthink_v2/Qwen3-8B"),
      ("Magistral-Small", "reasoning", "v2", "magi_think_v2/Magistral-Small-2509")]
rows = []
for model, mode, version, sub in F2:
    for norm, root, gold in (("raw", "results", GOLD_DEV_RAW),
                             ("HGNC", "results_norm2", GOLD_DEV)):
        s = score(os.path.join(root, sub), gold)
        if not s:
            print(f"  missing: {root}/{sub}", flush=True); continue
        for metric in ("F1", "precision", "recall"):
            rows.append({"model": model, "mode": mode, "version": version,
                         "normalisation": norm, "metric": metric,
                         "value": s[metric]})
write("fig2_normalisation.csv", rows,
      ["model", "mode", "version", "normalisation", "metric", "value"])

# ---------------------------------------------------------------- fig 3
print("\n=== fig3: prompt versions ===", flush=True)
VERS = ["v1", "v2", "v3", "v4", "v5", "v6lite", "v6full", "v7lite", "v7full"]
F3 = {
    "Qwen3-8B": {"v1": "qthink_v1/Qwen3-8B", "v2": "qthink_v2/Qwen3-8B",
                 "v3": "simple_8b/Qwen3-8B", "v4": "qthink_v4/Qwen3-8B",
                 "v5": "v5_think_8b/Qwen3-8B",
                 "v6lite": "q8b_think_v6lite/Qwen3-8B",
                 "v6full": "q8b_think_v6full/Qwen3-8B",
                 "v7lite": "q8b_think_v7lite/Qwen3-8B",
                 "v7full": "q8b_think_v7full/Qwen3-8B"},
    "Magistral-Small": {"v1": "magi_think_v1/Magistral-Small-2509",
                        "v2": "magi_think_v2/Magistral-Small-2509",
                        "v3": "magi_think_v3/Magistral-Small-2509",
                        "v4": "magi_think_v4/Magistral-Small-2509",
                        "v5": "magi_think_v5/Magistral-Small-2509",
                        "v6lite": "magi_think_v6lite/Magistral-Small-2509",
                        "v6full": "magi_think_v6/Magistral-Small-2509",
                        "v7lite": "magi_think_v7lite/Magistral-Small-2509",
                        "v7full": "magi_think_v7full/Magistral-Small-2509"},
}
rows = []
for model, mp in F3.items():
    for v in VERS:
        sub = mp.get(v)
        if not sub:
            continue
        s = score(os.path.join("results_norm2", sub), GOLD_DEV)
        if not s:
            print(f"  missing: {sub}", flush=True); continue
        raw = score(os.path.join("results", sub), GOLD_DEV_RAW)
        rows.append({"model": model, "version": v, "F1": s["F1"],
                     "precision": s["precision"], "recall": s["recall"],
                     "F1_raw": raw["F1"] if raw else None,
                     "precision_raw": raw["precision"] if raw else None,
                     "recall_raw": raw["recall"] if raw else None,
                     "rejected": rejected(sub), "seconds": seconds(sub)})
write("fig3_prompt.csv", rows,
      ["model", "version", "F1", "precision", "recall",
       "F1_raw", "precision_raw", "recall_raw", "rejected", "seconds"])

# ---------------------------------------------------------------- fig 5a
print("\n=== fig5a: temperature ===", flush=True)
rows = []
for d in sorted(glob.glob("results/tsweep_t*_s*")):
    m = re.search(r"tsweep_t(\d+)_s(\d+)", d)
    if not m:
        continue
    temp = int(m.group(1)) / 10.0
    seed = int(m.group(2))
    sub = os.path.relpath(glob.glob(d + "/*/")[0], "results").rstrip("/") \
          if glob.glob(d + "/*/") else None
    if not sub:
        continue
    s = score(os.path.join("results_norm2", sub), GOLD_DEV) or \
        score(os.path.join("results_norm", sub), GOLD_DEV)
    if not s:
        print(f"  missing: {sub}", flush=True); continue
    rows.append({"temperature": temp, "seed": seed, "F1": s["F1"],
                 "precision": s["precision"], "recall": s["recall"]})
write("fig5a_temperature.csv", rows,
      ["temperature", "seed", "F1", "precision", "recall"])

# ---------------------------------------------------------------- fig 5b
print("\n=== fig5b: replicates ===", flush=True)
F5B = {"Magistral-Small": ["magi_think_v6/Magistral-Small-2509",
                           "magi_v6_r2/Magistral-Small-2509",
                           "magi_v6_r3/Magistral-Small-2509"],
       "Qwen3-8B": ["q8b_think_v6full/Qwen3-8B",
                    "q8_v6_r2/Qwen3-8B", "q8_v6_r3/Qwen3-8B"]}
rows = []
for model, subs in F5B.items():
    for i, sub in enumerate(subs, 1):
        s = score(os.path.join("results_norm2", sub), GOLD_DEV)
        if not s:
            print(f"  missing: {sub}", flush=True); continue
        rows.append({"model": model, "run": i, "F1": s["F1"],
                     "precision": s["precision"], "recall": s["recall"]})
write("fig5b_replicates.csv", rows,
      ["model", "run", "F1", "precision", "recall"])

# ---------------------------------------------------------------- fig 6
print("\n=== fig6: held-out ===", flush=True)
F6 = [("Magistral-Small", "final_eval_v7/Magistral-Small-2509",
       "magi_think_v7full/Magistral-Small-2509"),
      ("Qwen3-8B", "final_eval_q8b/Qwen3-8B",
       "q8b_think_v7full/Qwen3-8B"),
      ("Gemma-4-12B", "final_eval_gemma/gemma-4-12B-it",
       "gemma4_v6/gemma-4-12B-it")]
rows = []
for model, ho_sub, dev_sub in F6:
    for setname, sub, gold in (("held-out", ho_sub, GOLD_HO),
                               ("development", dev_sub, GOLD_DEV)):
        s = score(os.path.join("results_norm2", sub), gold)
        if not s:
            print(f"  missing: {sub}", flush=True); continue
        for metric in ("F1", "precision", "recall"):
            rows.append({"model": model, "set": setname, "metric": metric,
                         "value": s[metric], "TP": s["TP"], "FP": s["FP"],
                         "FN": s["FN"], "TN": s["TN"]})
write("fig6_heldout.csv", rows,
      ["model", "set", "metric", "value", "TP", "FP", "FN", "TN"])

# ---------------------------------------------------------------- fig 7
print("\n=== fig7: consensus on held-out ===", flush=True)
A = "results_norm2/final_eval_v7/Magistral-Small-2509"
B = "results_norm2/final_eval_q8b/Qwen3-8B"
C = "results_norm2/final_eval_gemma/gemma-4-12B-it"
CONS = "results_consensus_final"
RULES = [("Magistral alone", A, "single"),
         ("Qwen3-8B alone", B, "single"),
         ("Gemma-4 alone", C, "single"),
         ("Magistral + Qwen, both", f"{CONS}/MagQwen_intersection", "both"),
         ("Magistral + Gemma, both", f"{CONS}/MagGem_intersection", "both"),
         ("Qwen + Gemma, both", f"{CONS}/QwenGem_intersection", "both"),
         ("Magistral + Qwen, either", f"{CONS}/MagQwen_union", "either"),
         ("Magistral + Gemma, either", f"{CONS}/MagGem_union", "either"),
         ("Qwen + Gemma, either", f"{CONS}/QwenGem_union", "either"),
         ("Any two of three", f"{CONS}/vote2", "three"),
         ("All three", f"{CONS}/vote3", "three")]
rows = []
for label, d, cat in RULES:
    s = score(d, GOLD_HO)
    if not s:
        print(f"  missing: {d}", flush=True); continue
    rows.append({"rule": label, "category": cat, "F1": s["F1"],
                 "precision": s["precision"], "recall": s["recall"],
                 "TP": s["TP"], "FP": s["FP"], "FN": s["FN"], "TN": s["TN"]})
write("fig7_consensus_scores.csv", rows,
      ["rule", "category", "F1", "precision", "recall", "TP", "FP", "FN", "TN"])

# ---------------------------------------------------------------- ladder
print("\n=== fig7b: agreement ladder ===", flush=True)
def ladder(models, gold_path, tag):
    gold = {}
    for l in open(gold_path, encoding="utf-8"):
        if l.strip():
            r = json.loads(l)
            gold[r["pmid"]] = {(o["gene"] or "").strip().upper()
                               for o in r["gold_observations"]}
    def genes(p):
        try:
            t = open(p, encoding="utf-8", errors="ignore").read()
        except FileNotFoundError:
            return set()
        m = re.search(r"\{.*\}", t, re.DOTALL)
        if not m:
            return set()
        try:
            d = json.loads(m.group(0))
        except Exception:
            return set()
        if isinstance(d, dict) and d.get("result"):
            return set()
        return {(o.get("target") or "").strip().upper()
                for o in d.get("observations", []) if o.get("target")}
    sub = defaultdict(lambda: [0, 0])
    first = models[0][1]
    for f in sorted(glob.glob(first + "/*.txt")):
        fn = os.path.basename(f); pmid = fn[:-4]
        if pmid not in gold:
            continue
        found = {n: genes(os.path.join(d, fn)) for n, d in models}
        for g in set().union(*found.values()):
            who = frozenset(n for n in found if g in found[n])
            sub[who][0] += 1
            sub[who][1] += (g in gold[pmid])
    order = [({"Magistral", "Qwen", "Gemma"}, "All three"),
             ({"Magistral", "Gemma"}, "Magistral + Gemma"),
             ({"Magistral", "Qwen"}, "Magistral + Qwen"),
             ({"Qwen", "Gemma"}, "Qwen + Gemma"),
             ({"Magistral"}, "Magistral only"),
             ({"Qwen"}, "Qwen only"),
             ({"Gemma"}, "Gemma only")]
    out = []
    for k, lab in order:
        n, c = sub[frozenset(k)]
        if n:
            out.append({"set": tag, "subset": lab, "genes": n, "correct": c,
                        "proportion": round(c / n, 4)})
    return out

rows = []
if all(os.path.isdir(d) for d in (A, B, C)):
    rows += ladder([("Magistral", A), ("Qwen", B), ("Gemma", C)],
                   GOLD_HO, "held-out")
DA = "results_norm2/magi_think_v6/Magistral-Small-2509"
DB = "results_norm2/q8b_think_v6full/Qwen3-8B"
DC = "results_norm2/gemma4_v6/gemma-4-12B-it"
if all(os.path.isdir(d) for d in (DA, DB, DC)):
    rows += ladder([("Magistral", DA), ("Qwen", DB), ("Gemma", DC)],
                   GOLD_DEV, "development")
write("fig7b_ladder.csv", rows,
      ["set", "subset", "genes", "correct", "proportion"])

print("\ndone")
