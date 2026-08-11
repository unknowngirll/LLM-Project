#!/usr/bin/env python3
"""build_dynamic_dataset.py - few-shot examples retrieved per abstract."""
import json, os, re, argparse
from pathlib import Path
from datasets import Dataset, DatasetDict, load_from_disk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

ap = argparse.ArgumentParser()
ap.add_argument("--like_dataset", default="data/eval_v3_dataset")
ap.add_argument("--split", default="validation")
ap.add_argument("--system_file", default="Prompts_v5/system_prompt.txt")
ap.add_argument("--reject_source", default="Prompts_v5/user_prompt.txt")
ap.add_argument("--pool_file", default="data/splits/pool_pmids.txt")
ap.add_argument("--abstracts", default="data/abstracts")
ap.add_argument("--gold", default="data/gold_answers.jsonl")
ap.add_argument("--k", type=int, required=True)
ap.add_argument("--no_rejects", action="store_true")
ap.add_argument("--out", required=True)
a = ap.parse_args()

NEG = {"result": "No valid OA animal model perturbations found"}

gold = {}
for l in open(a.gold, encoding="utf-8"):
    if l.strip():
        r = json.loads(l)
        gold[r["pmid"]] = r["gold_observations"]

def abstract(pmid):
    return Path(a.abstracts, pmid + ".txt").read_text(encoding="utf-8").strip()

ref = load_from_disk(a.like_dataset)[a.split]
targets = [e["metadata"]["pmid"] for e in ref]
system_prompt = Path(a.system_file).read_text(encoding="utf-8").strip()

pool = [p.strip() for p in open(a.pool_file) if p.strip()]
if set(pool) & set(targets):
    raise SystemExit("ERROR: pool overlaps the evaluation set")
print("pool", len(pool), "papers, evaluating", len(targets), "k=", a.k)

reject_blocks = []
if not a.no_rejects and os.path.exists(a.reject_source):
    txt = Path(a.reject_source).read_text(encoding="utf-8")
    for chunk in re.split(r"={20,}\s*\nEXAMPLE ", txt)[1:]:
        head = chunk.split("\n", 1)[0]
        if "REJECT" in head.upper():
            body = chunk.split("\n", 1)[1] if "\n" in chunk else chunk
            body = re.split(r"={20,}\s*\nNOW EXTRACT", body)[0]
            reject_blocks.append(body.rstrip())
print("carried over", len(reject_blocks), "REJECT examples")

nearest = {}
if a.k > 0:
    vec = TfidfVectorizer(stop_words="english", min_df=2, max_df=0.7,
                          ngram_range=(1, 2), sublinear_tf=True)
    P = vec.fit_transform([abstract(p) for p in pool])
    T = vec.transform([abstract(p) for p in targets])
    sim = cosine_similarity(T, P)
    for i, pmid in enumerate(targets):
        order = sim[i].argsort()[::-1][:a.k]
        nearest[pmid] = [(pool[j], float(sim[i][j])) for j in order]
    tops = [n[0][1] for n in nearest.values()]
    print("nearest similarity: mean %.3f min %.3f max %.3f"
          % (sum(tops)/len(tops), min(tops), max(tops)))

def worked_example(pmid):
    obs = gold.get(pmid) or []
    ans = json.dumps({"observations": obs} if obs else NEG,
                     ensure_ascii=False, indent=2)
    return 'INPUT ABSTRACT:\n"' + abstract(pmid) + '"\n\nCORRECT OUTPUT:\n' + ans

BAR = "=" * 69
records = []
for pmid in targets:
    parts, n = [], 0
    for ex, _ in nearest.get(pmid, []):
        n += 1
        parts.append(BAR + "\nEXAMPLE " + str(n) + "\n" + BAR + "\n"
                     + worked_example(ex))
    for blk in reject_blocks:
        n += 1
        parts.append(BAR + "\nEXAMPLE " + str(n) + " - REJECT\n" + BAR + "\n"
                     + blk.strip())
    parts.append(BAR + "\nNOW EXTRACT DATA FROM THE FOLLOWING ABSTRACT.\n"
                 "Output only JSON. Do not include explanations.\n" + BAR
                 + "\n" + abstract(pmid))
    obs = gold.get(pmid) or []
    records.append({
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "\n\n".join(parts)},
            {"role": "assistant", "content": json.dumps(
                {"observations": obs} if obs else NEG,
                ensure_ascii=False, indent=2)},
        ],
        "metadata": {"pmid": pmid},
    })

if len(records) != len(targets):
    raise SystemExit("record count mismatch - refusing to save")

Path(a.out).parent.mkdir(parents=True, exist_ok=True)
DatasetDict({"validation": Dataset.from_list(records)}).save_to_disk(a.out)
lens = [len(r["messages"][1]["content"]) for r in records]
print("built %d records, user prompt %d-%d chars (mean %d)"
      % (len(records), min(lens), max(lens), sum(lens)//len(lens)))
print("saved ->", a.out)
