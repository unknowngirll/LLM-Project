#!/usr/bin/env python3
"""
infer_think_simple.py - plain thinking-mode inference.
Same as infer_think_script.py but with three fixes:
  1. proper sampling (greedy makes Qwen3 loop forever in thinking mode)
  2. skips files that already exist  -> safe to resubmit after TIMEOUT
  3. unbuffered logging + unsloth backend for the 27B multimodal checkpoint
"""
import sys
_BACKEND = "transformers"
if "--backend" in sys.argv:
    _BACKEND = sys.argv[sys.argv.index("--backend") + 1]
if _BACKEND == "unsloth":
    import unsloth
    from unsloth import FastModel

import os, argparse, time
import torch
from datasets import load_from_disk

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--dataset", default="data/eval_v3_dataset")
ap.add_argument("--split", default="validation")
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--backend", choices=["transformers", "unsloth"], default="transformers")
ap.add_argument("--load_in_4bit", action="store_true")
ap.add_argument("--max_seq_length", type=int, default=24000)
ap.add_argument("--max_new_tokens", type=int, default=20000)
ap.add_argument("--temperature", type=float, default=0.6)
ap.add_argument("--top_p", type=float, default=0.95)
ap.add_argument("--top_k", type=int, default=20)
ap.add_argument("--out_dir", default="results")
args = ap.parse_args()

def log(*a): print(*a, flush=True)

model_tag = os.path.basename(args.model.rstrip("/"))
out_dir = os.path.join(args.out_dir, model_tag)
os.makedirs(out_dir, exist_ok=True)

log(f"Loading {args.model}  backend={args.backend}  4bit={args.load_in_4bit}")
if args.backend == "unsloth":
    model, tok = FastModel.from_pretrained(
        model_name=args.model, max_seq_length=args.max_seq_length,
        load_in_4bit=args.load_in_4bit, load_in_8bit=False, full_finetuning=False)
    try:
        FastModel.for_inference(model)
    except Exception as e:
        log(f"(for_inference skipped: {e})")
else:
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.bfloat16, device_map="auto")
model.eval()
text_tok = getattr(tok, "tokenizer", tok)
PAD = text_tok.pad_token_id if text_tok.pad_token_id is not None else text_tok.eos_token_id
log("Model loaded.")

SPECIALS = ["<|im_end|>", "<|im_start|>", "<|endoftext|>", "<|end_of_text|>"]

ds = load_from_disk(args.dataset)[args.split]
if args.limit > 0:
    ds = ds.select(range(min(args.limit, len(ds))))
log(f"Running on {len(ds)} records. max_new_tokens={args.max_new_tokens} temp={args.temperature}")

for i, ex in enumerate(ds):
    pmid = ex["metadata"]["pmid"]
    out_path = os.path.join(out_dir, f"{pmid}.txt")
    if os.path.exists(out_path):
        log(f"[{i+1}/{len(ds)}] {pmid} already done, skipping")
        continue

    msgs = [m for m in ex["messages"] if m["role"] != "assistant"]
    try:
        prompt = tok.apply_chat_template(msgs, tokenize=False,
                                         add_generation_prompt=True,
                                         enable_thinking=True)
    except TypeError:
        prompt = tok.apply_chat_template(msgs, tokenize=False,
                                         add_generation_prompt=True)
    ids = text_tok(prompt, return_tensors="pt").input_ids.to(model.device)

    t0 = time.time()
    with torch.no_grad():
        out = model.generate(
            input_ids=ids, attention_mask=torch.ones_like(ids),
            max_new_tokens=args.max_new_tokens, pad_token_id=PAD,
            do_sample=True, temperature=args.temperature,
            top_p=args.top_p, top_k=args.top_k)
    gen = out[0][ids.shape[1]:]

    text = text_tok.decode(gen, skip_special_tokens=False)
    for sp in SPECIALS:
        text = text.replace(sp, "")
    text = text.strip()

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

    dt = time.time() - t0
    closed = "</think>" in text
    hit_cap = int(gen.shape[0]) >= args.max_new_tokens
    log(f"[{i+1}/{len(ds)}] {pmid} {dt:.0f}s {int(gen.shape[0])}tok "
        f"think_closed={closed} hit_cap={hit_cap}")

log(f"All outputs saved to {out_dir}")
