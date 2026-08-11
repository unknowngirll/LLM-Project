#!/usr/bin/env python3
"""
consensus.py - combine two models' JSON outputs per paper.

intersection : keep a gene only if both models found it   -> favours precision
union        : keep a gene either model found              -> favours recall
Attribute fields are taken from model A where both agree on the gene.
"""
import os, re, sys, json, glob, argparse

ap = argparse.ArgumentParser()
ap.add_argument("--dir_a", required=True)
ap.add_argument("--dir_b", required=True)
ap.add_argument("--mode", choices=["intersection", "union"], default="intersection")
ap.add_argument("--out_dir", required=True)
a = ap.parse_args()

def extract(text):
    body = text.rsplit("</think>", 1)[1] if "</think>" in text else \
           re.sub(r"<think>.*", "", text, flags=re.DOTALL)
    for pat in (r"\{.*\}", r"\{.*?\}"):
        m = re.search(pat, body, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                continue
    return None

def obs_of(d):
    if d is None:
        return None                      # unparseable
    if isinstance(d, dict) and d.get("result"):
        return []                        # explicit negative
    return d.get("observations", []) if isinstance(d, dict) else []

def key(o):
    return (o.get("target") or "").strip().upper()

os.makedirs(a.out_dir, exist_ok=True)
files = sorted(os.path.basename(f) for f in glob.glob(a.dir_a + "/*.txt"))
stats = {"papers": 0, "both_negative": 0, "agreed": 0,
         "only_a": 0, "only_b": 0, "kept": 0}

for fn in files:
    pa, pb = os.path.join(a.dir_a, fn), os.path.join(a.dir_b, fn)
    if not os.path.exists(pb):
        continue
    oa = obs_of(extract(open(pa, encoding="utf-8", errors="ignore").read()))
    ob = obs_of(extract(open(pb, encoding="utf-8", errors="ignore").read()))
    if oa is None: oa = []
    if ob is None: ob = []
    stats["papers"] += 1

    ka, kb = {key(o) for o in oa if key(o)}, {key(o) for o in ob if key(o)}
    stats["agreed"] += len(ka & kb)
    stats["only_a"] += len(ka - kb)
    stats["only_b"] += len(kb - ka)

    keep = (ka & kb) if a.mode == "intersection" else (ka | kb)
    out, seen = [], set()
    for o in oa + ob:                    # A first, so A wins on shared genes
        k = key(o)
        if k in keep and k not in seen:
            seen.add(k)
            out.append(dict(o))
    for i, o in enumerate(out, 1):
        o["observation_number"] = i
    stats["kept"] += len(out)

    if not out:
        stats["both_negative"] += 1
        payload = {"result": "No valid OA animal model perturbations found"}
    else:
        payload = {"observations": out}
    json.dump(payload, open(os.path.join(a.out_dir, fn), "w"), ensure_ascii=False)

print(f"mode: {a.mode}")
for k, v in stats.items():
    print(f"  {k:14s} {v}")
print(f"-> {a.out_dir}")
