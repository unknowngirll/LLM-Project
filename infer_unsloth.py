#!/usr/bin/env python3
"""
infer_unsloth.py - run one model over the eval dataset, save raw outputs.
Path A: unsloth (faster inference; supports 4-bit loading for large models).
Same arguments and output format as infer.py (transformers version).
"""
import unsloth
from unsloth import FastLanguageModel

import os, json, argparse, time
import torch
from datasets import load_from_disk

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True, help="path to model dir")
ap.add_argument("--dataset", default="data/eval_dataset")
ap.add_argument("--split", default="validation")
ap.add_argument("--limit", type=int, default=0, help="0 = all; else first N records")
ap.add_argument("--max_new_tokens", type=int, default=900)
ap.add_argument("--max_seq_length", type=int, default=8192)
ap.add_argument("--load_in_4bit", action="store_true")
ap.add_argument("--out_dir", default="results")
args = ap.parse_args()

model_tag = os.path.basename(args.model.rstrip("/"))
out_dir = os.path.join(args.out_dir, model_tag)
os.makedirs(out_dir, exist_ok=True)

print(f"Loading model with unsloth: {args.model}  (4-bit={args.load_in_4bit})")
model, tok = FastLanguageModel.from_pretrained(
    model_name=args.model,
    max_seq_length=args.max_seq_length,
    dtype=None,
    load_in_4bit=args.load_in_4bit,
)
FastLanguageModel.for_inference(model)
print("Model loaded.")

ds = load_from_disk(args.dataset)[args.split]
if args.limit > 0:
    ds = ds.select(range(min(args.limit, len(ds))))
print(f"Running on {len(ds)} records.")

for i, ex in enumerate(ds):
    pmid = ex["metadata"]["pmid"]
    out_path = os.path.join(out_dir, f"{pmid}.txt")
    if os.path.exists(out_path):
        print(f"[{i+1}/{len(ds)}] PMID {pmid} already done, skipping")
        continue

    msgs = [m for m in ex["messages"] if m["role"] != "assistant"]
    try:
        prompt = tok.apply_chat_template(msgs, tokenize=False,
                                         add_generation_prompt=True,
                                         enable_thinking=False)
    except TypeError:
        prompt = tok.apply_chat_template(msgs, tokenize=False,
                                         add_generation_prompt=True)

    inputs = tok(prompt, return_tensors="pt").to(model.device)
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=args.max_new_tokens,
                             do_sample=False)
    gen = out[0][inputs["input_ids"].shape[1]:]
    text = tok.decode(gen, skip_special_tokens=True).strip()
    dt = time.time() - t0

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[{i+1}/{len(ds)}] PMID {pmid} done in {dt:.1f}s ({len(gen)} tok)")

print(f"All outputs saved to {out_dir}")
