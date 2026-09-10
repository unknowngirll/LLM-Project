#!/usr/bin/env python3
"""
audit_runs.py - health check across every result directory.
Flags incomplete runs, parse failures, reasoning loops, truncated files,
and thinking/instruct mismatches.
"""
import os, re, json, glob

EXPECTED = 267

def verdict(n, closed, looped, tiny, parse_fail, empty):
    if n == 0:                      return "EMPTY", "no files"
    if n < EXPECTED * 0.94:         return "INCOMPLETE", f"{n}/{EXPECTED}"
    if parse_fail > n * 0.05:       return "BROKEN", f"{parse_fail} parse failures"
    if looped > n * 0.10:           return "BROKEN", f"{looped} looped files"
    if empty:                       return "BROKEN", f"{empty} empty files"
    if 0 < closed < n * 0.90:       return "SUSPECT", f"only {closed}/{n} closed <think>"
    return "OK", ""

rows = []
for d in sorted(glob.glob("results/*/*")):
    if not os.path.isdir(d):
        continue
    fs = [f for f in glob.glob(d + "/*.txt") if not f.endswith("_raw.txt")]
    if not fs:
        continue
    n = len(fs)
    closed = looped = tiny = empty = pf = 0
    total = 0
    for f in fs:
        sz = os.path.getsize(f); total += sz
        if sz == 0: empty += 1
        if sz > 35 * 1024: looped += 1
        if sz < 40: tiny += 1
        t = open(f, encoding="utf-8", errors="ignore").read()
        if "</think>" in t: closed += 1
        body = t.rsplit("</think>", 1)[1] if "</think>" in t else \
               re.sub(r"<think>.*", "", t, flags=re.DOTALL)
        ok = False
        for pat in (r"\{.*\}", r"\{.*?\}"):
            m = re.search(pat, body, re.DOTALL)
            if m:
                try: json.loads(m.group(0)); ok = True; break
                except Exception: pass
        if not ok: pf += 1
    mode = "Think" if closed > n * 0.5 else "Instr"
    v, note = verdict(n, closed, looped, tiny, pf, empty)
    rows.append({"dir": d.replace("results/", ""), "n": n, "mode": mode,
                 "closed": closed, "loop": looped, "pf": pf, "empty": empty,
                 "kb": total / n / 1024, "v": v, "note": note})

order = {"OK": 0, "SUSPECT": 1, "INCOMPLETE": 2, "BROKEN": 3, "EMPTY": 4}
rows.sort(key=lambda r: (order[r["v"]], r["dir"]))

hdr = f"{'run':42s} {'n':>4s} {'mode':>6s} {'closed':>7s} {'loop':>5s} {'pfail':>6s} {'KB':>6s}  verdict"
print(hdr); print("-" * len(hdr))
for r in rows:
    mark = {"OK": "OK", "SUSPECT": "?", "INCOMPLETE": "..", "BROKEN": "XX", "EMPTY": "--"}[r["v"]]
    print(f"{r['dir'][:42]:42s} {r['n']:4d} {r['mode']:>6s} {r['closed']:7d} "
          f"{r['loop']:5d} {r['pf']:6d} {r['kb']:6.1f}  {mark} {r['v']:10s} {r['note']}")

print("\n=== usable for the comparison figure ===")
for r in rows:
    if r["v"] == "OK":
        print(f"  {r['dir']}  ({r['mode']})")
print("\n=== exclude ===")
for r in rows:
    if r["v"] != "OK":
        print(f"  {r['dir']:42s} {r['v']} — {r['note']}")
