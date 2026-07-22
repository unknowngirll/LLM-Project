#!/usr/bin/env python3
"""
build_v5_dataset.py - rebuild the evaluation set with a new prompt pair,
keeping EXACTLY the same papers as an existing dataset.

Does not touch build_hf_dataset.py. No reshuffling: the PMID list is read
from --like_dataset, so v3 and v5 are directly comparable.
"""
import json, argparse
from pathlib import Path
from datasets import Dataset, DatasetDict, load_from_disk

ap = argparse.ArgumentParser()
ap.add_argument("--like_dataset", default="data/eval_v3_dataset",
                help="existing dataset whose PMID list is reused")
ap.add_argument("--split", default="validation")
ap.add_argument("--abstract_dir", default="data/abstracts")
ap.add_argument("--gold_file", default="data/gold_answers.jsonl")
ap.add_argument("--system_file", default="Prompts_v5/system_prompt.txt")
ap.add_argument("--user_file", default="Prompts_v5/user_prompt.txt")
ap.add_argument("--out", default="data/eval_v5_dataset")
args = ap.parse_args()

NEGATIVE = {"result": "No valid OA animal model perturbations found"}

gold = {}
with open(args.gold_file, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            r = json.loads(line)
            gold[r["pmid"]] = r["gold_observations"]
print(f"gold file: {len(gold)} PMIDs")

ref = load_from_disk(args.like_dataset)[args.split]
pmids = [ex["metadata"]["pmid"] for ex in ref]
print(f"reference set: {len(pmids)} PMIDs (from {args.like_dataset})")

system_prompt = Path(args.system_file).read_text(encoding="utf-8").strip()
user_template = Path(args.user_file).read_text(encoding="utf-8").strip()
if "{abstract}" not in user_template:
    raise SystemExit("ERROR: user prompt has no {abstract} placeholder")

abs_dir = Path(args.abstract_dir)
records, missing_abs, missing_gold, n_neg = [], [], [], 0
for pmid in pmids:                      # order preserved, no shuffle
    af = abs_dir / f"{pmid}.txt"
    if not af.exists():
        missing_abs.append(pmid); continue
    if pmid not in gold:
        missing_gold.append(pmid); continue
    obs = gold[pmid]
    if obs:
        answer = json.dumps({"observations": obs}, ensure_ascii=False, indent=2)
    else:
        answer = json.dumps(NEGATIVE, ensure_ascii=False); n_neg += 1
    records.append({
        "messages": [
            {"role": "system",    "content": system_prompt},
            {"role": "user",      "content": user_template.replace(
                                      "{abstract}", af.read_text(encoding="utf-8").strip())},
            {"role": "assistant", "content": answer},
        ],
        "metadata": {"pmid": pmid},
    })

print(f"built {len(records)} records  ({n_neg} negatives)")
if missing_abs:  print(f"  WARNING missing abstract: {len(missing_abs)} -> {missing_abs[:5]}")
if missing_gold: print(f"  WARNING missing gold:     {len(missing_gold)} -> {missing_gold[:5]}")
if len(records) != len(pmids):
    raise SystemExit(f"ERROR: {len(records)} != {len(pmids)} — refusing to save")

Path(args.out).parent.mkdir(parents=True, exist_ok=True)
DatasetDict({"validation": Dataset.from_list(records)}).save_to_disk(args.out)
print(f"saved -> {args.out}")
