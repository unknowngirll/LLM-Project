#!/usr/bin/env python3
"""consensus3.py - majority vote across three models, with a per-tier breakdown."""
import os, re, sys, json, glob, argparse
from collections import Counter

ap = argparse.ArgumentParser()
ap.add_argument("--dirs", nargs=3, required=True)
ap.add_argument("--names", nargs=3, default=["A", "B", "C"])
ap.add_argument("--min_votes", type=int, default=2)
ap.add_argument("--out_dir", required=True)
ap.add_argument("--gold", default="data/gold_answers_norm.jsonl")
a = ap.parse_args()

def genes_and_obs(path):
    try:
        t = open(path, encoding="utf-8", errors="ignore").read()
    except FileNotFoundError:
        return {}, []
    body = t.rsplit("</think>", 1)[1] if "</think>" in t else \
           re.sub(r"<think>.*", "", t, flags=re.DOTALL)
    d = None
    for pat in (r"\{.*\}", r"\{.*?\}"):
        m = re.search(pat, body, flags=re.DOTALL)
        if m:
            try:
                d = json.loads(m.group(0)); break
            except Exception:
                continue
    if d is None or (isinstance(d, dict) and d.get("result")):
        return {}, []
    obs = d.get("observations", []) if isinstance(d, dict) else []
    return {(o.get("target") or "").strip().upper(): o
            for o in obs if o.get("target")}, obs

gold = {}
for l in open(a.gold, encoding="utf-8"):
    if l.strip():
        r = json.loads(l)
        gold[r["pmid"]] = {(o["gene"] or "").strip().upper()
                           for o in r["gold_observations"]}

os.makedirs(a.out_dir, exist_ok=True)
tier = {1: [0, 0], 2: [0, 0], 3: [0, 0]}
kept = 0

for f in sorted(glob.glob(a.dirs[0] + "/*.txt")):
    fn = os.path.basename(f)
    maps = [genes_and_obs(os.path.join(d, fn))[0] for d in a.dirs]
    votes = Counter()
    for m in maps:
        votes.update(m.keys())

    pmid = fn[:-4]
    if pmid in gold:
        for g, v in votes.items():
            tier[v][0] += 1
            tier[v][1] += (g in gold[pmid])

    keep = [g for g, v in votes.items() if v >= a.min_votes]
    out, seen = [], set()
    for m in maps:
        for g in keep:
            if g in m and g not in seen:
                seen.add(g); out.append(dict(m[g]))
    for i, o in enumerate(out, 1):
        o["observation_number"] = i
    kept += len(out)
    payload = {"observations": out} if out else \
              {"result": "No valid OA animal model perturbations found"}
    json.dump(payload, open(os.path.join(a.out_dir, fn), "w"), ensure_ascii=False)

print(f"min_votes={a.min_votes}  kept={kept}")
print(f"\n{'votes':>6s} {'genes':>6s} {'correct':>8s} {'precision':>10s}")
for v in (3, 2, 1):
    n, c = tier[v]
    print(f"{v:6d} {n:6d} {c:8d} {c/n if n else 0:10.3f}")
print(f"\n-> {a.out_dir}")
