#!/usr/bin/env python3
"""Combine abstracts + gold answers + prompts into a HF dataset."""
import json, argparse
from pathlib import Path
from datasets import Dataset, DatasetDict

def load_gold(path):
    gold = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            gold[rec["pmid"]] = rec["gold_observations"]
    return gold

def gold_to_answer(observations):
    return json.dumps({"observations": observations}, ensure_ascii=False, indent=2)

def build(abstract_dir, gold_file, system_file, user_file, out_path,
          training, seed, val_frac, test_frac):
    system_prompt = Path(system_file).read_text(encoding="utf-8").strip()
    user_template = Path(user_file).read_text(encoding="utf-8").strip()
    gold = load_gold(gold_file)
    records = []
    abstract_dir = Path(abstract_dir)
    for pmid, obs in gold.items():
        af = abstract_dir / f"{pmid}.txt"
        if not af.exists():
            continue
        abstract_text = af.read_text(encoding="utf-8").strip()
        user_prompt = user_template.replace("{abstract}", abstract_text)
        records.append({
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": gold_to_answer(obs)},
            ],
            "metadata": {"pmid": pmid},
        })
    print(f"Built {len(records)} records (abstract + gold paired)")
    ds = Dataset.from_list(records)
    if training:
        ds = ds.shuffle(seed=seed)
        n = len(ds)
        n_test = int(n * test_frac)
        n_val = int(n * val_frac)
        test = ds.select(range(n_test))
        val = ds.select(range(n_test, n_test + n_val))
        train = ds.select(range(n_test + n_val, n))
        dd = DatasetDict({"train": train, "validation": val, "test": test})
        print(f"train={len(train)} val={len(val)} test={len(test)}")
    else:
        dd = DatasetDict({"validation": ds})
        print(f"validation-only: {len(ds)}")
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    dd.save_to_disk(out_path)
    print(f"Saved dataset to {out_path}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--abstract_dir", default="data/abstracts")
    ap.add_argument("--gold_file", default="data/gold_answers.jsonl")
    ap.add_argument("--system_file", default="Prompts_v2/system_prompt.txt")
    ap.add_argument("--user_file", default="Prompts_v2/user_prompt.txt")
    ap.add_argument("--out", default="data/eval_dataset")
    ap.add_argument("--training", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--val_frac", type=float, default=0.15)
    ap.add_argument("--test_frac", type=float, default=0.15)
    args = ap.parse_args()
    build(args.abstract_dir, args.gold_file, args.system_file, args.user_file,
          args.out, args.training, args.seed, args.val_frac, args.test_frac)
