#!/usr/bin/env python3
"""build_final_dataset.py - HF dataset for the final held-out evaluation."""
import json, argparse
from pathlib import Path
from datasets import Dataset, DatasetDict

ap = argparse.ArgumentParser()
ap.add_argument("--ids", default="data/splits/final_eval_pmids.txt")
ap.add_argument("--gold", default="data/gold_final_eval.jsonl")
ap.add_argument("--abstracts", default="data/abstracts")
ap.add_argument("--system_file", required=True)
ap.add_argument("--user_file", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()

NEG = {"result": "No valid OA animal model perturbations found"}

gold = {}
for l in open(a.gold, encoding="utf-8"):
    if l.strip():
        r = json.loads(l)
        gold[r["pmid"]] = r["gold_observations"]

ids = [l.strip() for l in open(a.ids) if l.strip()]
system_prompt = Path(a.system_file).read_text(encoding="utf-8").strip()
user_tpl = Path(a.user_file).read_text(encoding="utf-8")
if user_tpl.count("{abstract}") != 1:
    raise SystemExit("user prompt must contain exactly one {abstract}")

records = []
for pmid in ids:
    p = Path(a.abstracts, pmid + ".txt")
    if not p.exists():
        raise SystemExit("missing abstract: " + pmid)
    obs = gold.get(pmid) or []
    records.append({
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",
             "content": user_tpl.replace("{abstract}",
                                         p.read_text(encoding="utf-8").strip())},
            {"role": "assistant", "content": json.dumps(
                {"observations": obs} if obs else NEG,
                ensure_ascii=False, indent=2)},
        ],
        "metadata": {"pmid": pmid},
    })

if len(records) != len(ids):
    raise SystemExit("record count mismatch - refusing to save")

Path(a.out).parent.mkdir(parents=True, exist_ok=True)
DatasetDict({"validation": Dataset.from_list(records)}).save_to_disk(a.out)
n_neg = sum(1 for p in ids if not gold.get(p))
print("built %d records (%d negatives) -> %s" % (len(records), n_neg, a.out))
