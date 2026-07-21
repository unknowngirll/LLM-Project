#!/usr/bin/env python3
"""
infer_unsloth.py - run one model over the eval dataset, save raw outputs.
Path A: unsloth (faster inference; supports 4-bit loading for large models).
Uses FastModel (unified loader) so multimodal checkpoints (e.g. Qwen3.6-27B)
load correctly. For text-only inference we render the chat template with the
processor but tokenise with the inner text tokenizer, avoiding the vision path.
Same arguments and output format as infer.py (transformers version).
"""
import unsloth
from unsloth import FastModel
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
print(f"Loading model with unsloth FastModel: {args.model}  (4-bit={args.load_in_4bit})")
model, tok = FastModel.from_pretrained(
    model_name=args.model,
    max_seq_length=args.max_seq_length,
    load_in_4bit=args.load_in_4bit,
    load_in_8bit=False,
    full_finetuning=False,
)
try:
    FastModel.for_inference(model)
except Exception as e:
    print(f"(for_inference skipped: {e})")
print("Model loaded.")
# If tok is a multimodal processor, grab the inner text tokenizer for tensor calls.
text_tok = getattr(tok, "tokenizer", tok)

# --- Magistral fix: supply a Mistral-style chat template if none exists ---
MISTRAL_TEMPLATE = (
    "{{ bos_token }}"
    "{% for message in messages %}"
    "{% if message['role'] == 'system' %}"
    "{{ '[SYSTEM_PROMPT]' + message['content'] + '[/SYSTEM_PROMPT]' }}"
    "{% elif message['role'] == 'user' %}"
    "{{ '[INST]' + message['content'] + '[/INST]' }}"
    "{% elif message['role'] == 'assistant' %}"
    "{{ message['content'] + eos_token }}"
    "{% endif %}"
    "{% endfor %}"
)
if getattr(text_tok, "chat_template", None) is None:
    text_tok.chat_template = MISTRAL_TEMPLATE
if getattr(tok, "chat_template", None) is None:
    try:
        tok.chat_template = MISTRAL_TEMPLATE
    except Exception:
        pass
# --- end Magistral fix ---



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
    inputs = text_tok(prompt, return_tensors="pt").to(model.device)
    t0 = time.time()
    with torch.no_grad():
        out = model.generate(**inputs, max_new_tokens=args.max_new_tokens,
                             do_sample=False)
    gen = out[0][inputs["input_ids"].shape[1]:]
    text = text_tok.decode(gen, skip_special_tokens=True).strip()
    dt = time.time() - t0
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[{i+1}/{len(ds)}] PMID {pmid} done in {dt:.1f}s ({len(gen)} tok)")
print(f"All outputs saved to {out_dir}")
