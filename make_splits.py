#!/usr/bin/env python3
"""
make_splits.py - fix the held-out test set and the retrieval pool.

The 267-paper dev set stays untouched. The remaining annotated papers are
split once, with a fixed seed, into a held-out test set and a pool that may
be queried for k-nearest examples. Writing the lists to disk means the split
cannot drift between experiments.

Note: all 92 true negatives currently sit in the dev set, so both the
held-out set and the pool are positives only until curated negatives are
added.
"""
import json, os, random, argparse
from datasets import load_from_disk

ap = argparse.ArgumentParser()
ap.add_argument("--dev_dataset", default="data/eval_v3_dataset")
ap.add_argument("--gold", default="data/gold_answers.jsonl")
ap.add_argument("--abstracts", default="data/abstracts")
ap.add_argument("--n_heldout", type=int, default=400)
ap.add_argument("--seed", type=int, default=42)
ap.add_argument("--out_dir", default="data/splits")
a = ap.parse_args()

dev = {e["metadata"]["pmid"] for e in load_from_disk(a.dev_dataset)["validation"]}
gold = {}
for l in open(a.gold, encoding="utf-8"):
    if l.strip():
        r = json.loads(l)
        gold[r["pmid"]] = r["gold_observations"]
have = {f[:-4] for f in os.listdir(a.abstracts) if f.endswith(".txt")}

rest = sorted((set(gold) - dev) & have)
if len(rest) < a.n_heldout:
    raise SystemExit(f"only {len(rest)} papers available, need {a.n_heldout}")

pos = [p for p in rest if gold[p]]
neg = [p for p in rest if not gold[p]]
rng = random.Random(a.seed)
rng.shuffle(pos); rng.shuffle(neg)

frac = a.n_heldout / len(rest)
n_pos = min(len(pos), round(len(pos) * frac))
n_neg = min(len(neg), a.n_heldout - n_pos)
n_pos = a.n_heldout - n_neg          # top back up if there are few negatives
heldout = sorted(pos[:n_pos] + neg[:n_neg])
pool = sorted(pos[n_pos:] + neg[n_neg:])

assert not (set(heldout) & set(pool))
assert not (set(heldout) & dev) and not (set(pool) & dev)
assert len(heldout) == a.n_heldout, f"got {len(heldout)}, wanted {a.n_heldout}"

os.makedirs(a.out_dir, exist_ok=True)
for name, ids in (("dev", sorted(dev)), ("heldout", heldout), ("pool", pool)):
    with open(os.path.join(a.out_dir, f"{name}_pmids.txt"), "w") as fh:
        fh.write("\n".join(ids) + "\n")
    n_p = sum(1 for p in ids if gold.get(p))
    print(f"{name:9s} {len(ids):4d} papers  ({n_p} with observations, "
          f"{len(ids)-n_p} negatives)")

with open(os.path.join(a.out_dir, "README.txt"), "w") as fh:
    fh.write(f"Splits fixed with seed={a.seed} over the papers that have both a\n"
             f"gold record and an abstract on disk.\n\n"
             f"dev      {len(dev):4d}  evaluation set used throughout the project\n"
             f"heldout  {len(heldout):4d}  reserved for final evaluation, never queried\n"
             f"pool     {len(pool):4d}  may be queried for k-nearest examples\n\n"
             f"The three sets are disjoint. All true negatives are currently in\n"
             f"dev, so heldout and pool contain positives only; curated negatives\n"
             f"will need adding before the held-out evaluation can measure\n"
             f"specificity.\n")
print(f"\nwritten to {a.out_dir}/")
