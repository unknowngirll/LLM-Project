#!/usr/bin/env python3
"""
make_final_eval.py - assemble the final held-out evaluation set.

200 positive abstracts drawn from the reserved held-out split, plus the
curated negatives supplied by the supervisor. The held-out split was fixed
before any experiment and never queried, so nothing in it has been seen
during prompt development or used as a retrieval example.
"""
import csv, json, os, random, argparse

ap = argparse.ArgumentParser()
ap.add_argument("--n_pos", type=int, default=200)
ap.add_argument("--seed", type=int, default=7)
ap.add_argument("--negatives", default="data/negatives_batch2.tsv")
ap.add_argument("--out_gold", default="data/gold_final_eval.jsonl")
ap.add_argument("--out_ids", default="data/splits/final_eval_pmids.txt")
a = ap.parse_args()

def load_ids(p):
    return [l.strip() for l in open(p) if l.strip()]

gold = {}
for l in open("data/gold_answers.jsonl", encoding="utf-8"):
    if l.strip():
        r = json.loads(l)
        gold[r["pmid"]] = r["gold_observations"]

held = load_ids("data/splits/heldout_pmids.txt")
have = lambda p: os.path.exists(f"data/abstracts/{p}.txt")

# positives: held-out papers with gold observations and an abstract on disk
cand = [p for p in held if gold.get(p) and have(p)]
print(f"held-out: {len(held)}, usable positives: {len(cand)}")
if len(cand) < a.n_pos:
    raise SystemExit(f"only {len(cand)} usable, need {a.n_pos}")

rng = random.Random(a.seed)
positives = sorted(rng.sample(cand, a.n_pos))

# negatives: TrueNegative == 1, abstract present
negatives, skipped = [], []
with open(a.negatives, encoding="utf-8") as fh:
    for r in csv.DictReader(fh, delimiter="\t"):
        pmid = r["PMID"].strip()
        if r["TrueNegative"].strip() != "1":
            skipped.append((pmid, "TrueNegative=" + r["TrueNegative"].strip()))
        elif not have(pmid):
            skipped.append((pmid, "no abstract on disk"))
        else:
            negatives.append(pmid)
negatives = sorted(set(negatives))

dev = set(load_ids("data/splits/dev_pmids.txt"))
pool = set(load_ids("data/splits/pool_pmids.txt"))
both = set(positives) | set(negatives)
assert not (both & dev),  "overlaps the development set"
assert not (both & pool), "overlaps the retrieval pool"
assert not (set(positives) & set(negatives)), "a paper is in both classes"

print(f"positives {len(positives)}, negatives {len(negatives)}, "
      f"total {len(both)}")
if skipped:
    print("skipped from the negatives file:")
    for p, why in skipped:
        print(f"  {p}  {why}")

os.makedirs(os.path.dirname(a.out_ids), exist_ok=True)
with open(a.out_ids, "w") as fh:
    fh.write("\n".join(positives + negatives) + "\n")

with open(a.out_gold, "w", encoding="utf-8") as fh:
    for p in positives:
        fh.write(json.dumps({"pmid": p, "gold_observations": gold[p]},
                            ensure_ascii=False) + "\n")
    for p in negatives:
        fh.write(json.dumps({"pmid": p, "gold_observations": []},
                            ensure_ascii=False) + "\n")

n_obs = sum(len(gold[p]) for p in positives)
print(f"\nwrote {a.out_gold}: {len(both)} papers, {n_obs} gold observations")
print(f"wrote {a.out_ids}")
