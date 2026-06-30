#!/usr/bin/env python3
"""
add_negatives.py
Add Jamie's curated true-negative papers to the eval set.
- reads the TSV, keeps only TrueNegative == 1 (the 92 confirmed negatives)
- fetches each abstract from PubMed (reusing prepare_gold.fetch_abstracts)
- appends an EMPTY gold record {"pmid": ..., "gold_observations": []}
- idempotent: skips PMIDs already present in the gold file
"""
import argparse, json, csv
from pathlib import Path
from prepare_gold import fetch_abstracts  # reuse Jamie-style PubMed fetch

def load_existing_pmids(gold_path):
    pmids = set()
    p = Path(gold_path)
    if p.exists():
        for line in p.open(encoding="utf-8"):
            line = line.strip()
            if line:
                pmids.add(str(json.loads(line)["pmid"]))
    return pmids

def read_true_negatives(tsv_path):
    keep = []
    with open(tsv_path, encoding="utf-8") as f:
        r = csv.DictReader(f, delimiter="\t")
        for row in r:
            if (row.get("TrueNegative") or "").strip() == "1":
                keep.append(str(row["PMID"]).strip())
    return keep

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tsv", required=True)
    ap.add_argument("--gold", default="data/gold_answers.jsonl")
    ap.add_argument("--abstract_dir", default="data/abstracts")
    ap.add_argument("--email", required=True)
    ap.add_argument("--api_key", default=None)
    args = ap.parse_args()

    tn_pmids = read_true_negatives(args.tsv)
    print(f"TrueNegative==1 in TSV: {len(tn_pmids)}")

    existing = load_existing_pmids(args.gold)
    to_add = [p for p in tn_pmids if p not in existing]
    print(f"Already in gold: {len(tn_pmids) - len(to_add)} | new to add: {len(to_add)}")
    if not to_add:
        print("Nothing new to add. Done.")
        return

    # fetch abstracts for the new negatives (writes <pmid>.txt into abstract_dir)
    fetch_abstracts(to_add, args.abstract_dir, args.email, args.api_key)

    # append empty-gold records only for those that actually have an abstract file
    adir = Path(args.abstract_dir)
    added = 0
    no_abstract = []
    with open(args.gold, "a", encoding="utf-8") as f:
        for pmid in to_add:
            if (adir / f"{pmid}.txt").exists():
                f.write(json.dumps({"pmid": pmid, "gold_observations": []},
                                   ensure_ascii=False) + "\n")
                added += 1
            else:
                no_abstract.append(pmid)

    print(f"\nAdded {added} negative records to {args.gold}")
    if no_abstract:
        print(f"No abstract found for {len(no_abstract)}: {no_abstract}")

if __name__ == "__main__":
    main()
