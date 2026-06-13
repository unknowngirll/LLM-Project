#!/usr/bin/env python3
"""
prepare_gold.py
From the OATargets xlsx: build gold answers (JSON) per PMID and fetch
each paper's title+abstract from PubMed.
Outputs:
  data/gold_answers.jsonl     one line per PMID
  data/abstracts/<pmid>.txt   one file per PMID
  data/missing_pmids.txt      PMIDs with no abstract
"""
import os, json, time, argparse
from pathlib import Path
import pandas as pd
from Bio import Entrez

def row_to_observation(row, n):
    return {
        "observation_number": n,
        "gene": str(row["Gene"]).strip(),
        "effect_on_gene_product": str(row["Effect on gene product"]).strip(),
        "type": str(row["Type"]).strip(),
        "simple_model": str(row["simpleModel"]).strip(),
        "susceptibility_observed": str(row["Susceptibility observed"]).strip(),
        "inferred_gene_effect": str(row["Inferred gene effect"]).strip(),
        "delivery": str(row["Delivery"]).strip(),
        "species": str(row["Species"]).strip(),
    }

def build_gold(xlsx_path, out_jsonl):
    df = pd.read_excel(xlsx_path, sheet_name="All Data")
    df = df.dropna(subset=["PMID"])
    df["PMID"] = df["PMID"].astype(int).astype(str)
    pmids = []
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for pmid, g in df.groupby("PMID"):
            obs = [row_to_observation(r, i)
                   for i, (_, r) in enumerate(g.iterrows(), start=1)]
            f.write(json.dumps({"pmid": pmid, "gold_observations": obs},
                               ensure_ascii=False) + "\n")
            pmids.append(pmid)
    print(f"Gold built for {len(pmids)} PMIDs -> {out_jsonl}")
    return pmids

def fetch_abstracts(pmids, out_dir, email, api_key=None, batch=200):
    Entrez.email = email
    if api_key:
        Entrez.api_key = api_key
    out_dir = Path(out_dir); out_dir.mkdir(parents=True, exist_ok=True)
    todo = [p for p in pmids if not (out_dir / f"{p}.txt").exists()]
    print(f"{len(pmids)} total, {len(todo)} to fetch")
    missing = []
    for start in range(0, len(todo), batch):
        chunk = todo[start:start+batch]
        try:
            h = Entrez.efetch(db="pubmed", id=",".join(chunk),
                              rettype="xml", retmode="xml")
            records = Entrez.read(h); h.close()
        except Exception as e:
            print(f"batch {start} failed: {e}"); missing += chunk; continue
        for art in records.get("PubmedArticle", []):
            cit = art["MedlineCitation"]
            pmid = str(cit["PMID"])
            artinfo = cit["Article"]
            title = str(artinfo.get("ArticleTitle", "")).strip()
            abs = artinfo.get("Abstract", {}).get("AbstractText", [])
            parts = []
            for a in abs:
                label = a.attributes.get("Label") if hasattr(a, "attributes") else None
                parts.append(f"{label}: {a}" if label else str(a))
            abstract = "\n".join(parts).strip()
            if not abstract:
                missing.append(pmid); continue
            (out_dir / f"{pmid}.txt").write_text(
                f"TITLE: {title}\n\nABSTRACT: {abstract}", encoding="utf-8")
        time.sleep(0.4 if api_key else 1.0)
        print(f"  fetched up to {start+len(chunk)}/{len(todo)}")
    if missing:
        Path(out_dir.parent / "missing_pmids.txt").write_text("\n".join(missing))
        print(f"WARNING: {len(missing)} PMIDs had no abstract (see missing_pmids.txt)")
    return missing

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--gold_out", default="data/gold_answers.jsonl")
    ap.add_argument("--abstract_dir", default="data/abstracts")
    ap.add_argument("--email", required=True)
    ap.add_argument("--api_key", default=None)
    args = ap.parse_args()
    Path(args.gold_out).parent.mkdir(parents=True, exist_ok=True)
    pmids = build_gold(args.xlsx, args.gold_out)
    fetch_abstracts(pmids, args.abstract_dir, args.email, args.api_key)
