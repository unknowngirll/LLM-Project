#!/usr/bin/env python3
"""
add_rejection_precision.py - how many of the rejected papers were correctly
rejected. Adds two columns to fig3_prompt.csv so the rejection panel can
report the proportion right rather than the raw count.
"""
import csv, json, glob, os, re

GOLD = "data/gold_answers.jsonl"
gold_has = {}
for l in open(GOLD, encoding="utf-8"):
    if l.strip():
        r = json.loads(l)
        gold_has[r["pmid"]] = bool(r["gold_observations"])

SUBS = {
    ("Qwen3-8B", "v1"): "qthink_v1/Qwen3-8B",
    ("Qwen3-8B", "v2"): "qthink_v2/Qwen3-8B",
    ("Qwen3-8B", "v3"): "simple_8b/Qwen3-8B",
    ("Qwen3-8B", "v4"): "qthink_v4/Qwen3-8B",
    ("Qwen3-8B", "v5"): "v5_think_8b/Qwen3-8B",
    ("Qwen3-8B", "v6lite"): "q8b_think_v6lite/Qwen3-8B",
    ("Qwen3-8B", "v6full"): "q8b_think_v6full/Qwen3-8B",
    ("Qwen3-8B", "v7lite"): "q8b_think_v7lite/Qwen3-8B",
    ("Qwen3-8B", "v7full"): "q8b_think_v7full/Qwen3-8B",
    ("Magistral-Small", "v1"): "magi_think_v1/Magistral-Small-2509",
    ("Magistral-Small", "v2"): "magi_think_v2/Magistral-Small-2509",
    ("Magistral-Small", "v3"): "magi_think_v3/Magistral-Small-2509",
    ("Magistral-Small", "v4"): "magi_think_v4/Magistral-Small-2509",
    ("Magistral-Small", "v5"): "magi_think_v5/Magistral-Small-2509",
    ("Magistral-Small", "v6lite"): "magi_think_v6lite/Magistral-Small-2509",
    ("Magistral-Small", "v6full"): "magi_think_v6/Magistral-Small-2509",
    ("Magistral-Small", "v7lite"): "magi_think_v7lite/Magistral-Small-2509",
    ("Magistral-Small", "v7full"): "magi_think_v7full/Magistral-Small-2509",
}

def rejection_stats(sub):
    d = os.path.join("results", sub)
    n = right = 0
    for f in glob.glob(d + "/*.txt"):
        t = open(f, encoding="utf-8", errors="ignore").read()
        if '"result"' not in t:
            continue
        pmid = os.path.basename(f)[:-4]
        if pmid not in gold_has:
            continue
        n += 1
        right += (not gold_has[pmid])
    return n, right

p = "figdata/fig3_prompt.csv"
rows = list(csv.DictReader(open(p)))
for r in rows:
    n, right = rejection_stats(SUBS[(r["model"], r["version"])])
    r["rejected"] = n
    r["rejected_correct"] = right
    r["rejection_precision"] = round(right / n, 4) if n else ""
    print(f"  {r['model']:16s} {r['version']:7s} "
          f"{right:3d}/{n:3d} correctly rejected "
          f"({100*right/n:5.1f}%)" if n else "", flush=True)

cols = list(rows[0].keys())
with open(p, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow(r)
print(f"\nupdated {p}")
