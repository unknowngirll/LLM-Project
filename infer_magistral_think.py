#!/usr/bin/env python3
"""
infer_magistral_think.py - Magistral in reasoning mode.

Magistral ignores the `enable_thinking` flag. Reasoning is triggered by its own
system prompt, which asks for a [THINK]...[/THINK] block; that prompt ships with
the checkpoint as SYSTEM_PROMPT.txt and is prepended to the task system message.

On save, [THINK]/[/THINK] are rewritten to <think>/</think> so that score_v2.py
can separate reasoning from the JSON answer. The reasoning text is untouched.
"""
import unsloth
from unsloth import FastModel
import os, argparse, time
import torch
from datasets import load_from_disk

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--dataset", default="data/eval_v5_dataset")
ap.add_argument("--split", default="validation")
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--max_new_tokens", type=int, default=12000)
ap.add_argument("--max_seq_length", type=int, default=16000)
ap.add_argument("--load_in_4bit", action="store_true")
ap.add_argument("--temperature", type=float, default=0.7)
ap.add_argument("--top_p", type=float, default=0.95)
ap.add_argument("--out_dir", default="results")
args = ap.parse_args()

def log(*a): print(*a, flush=True)

model_tag = os.path.basename(args.model.rstrip("/"))
out_dir = os.path.join(args.out_dir, model_tag)
os.makedirs(out_dir, exist_ok=True)

sp_path = os.path.join(args.model, "SYSTEM_PROMPT.txt")
if os.path.exists(sp_path):
    MAGISTRAL_SP = open(sp_path, encoding="utf-8").read().strip()
    log(f"loaded SYSTEM_PROMPT.txt ({len(MAGISTRAL_SP)} chars)")
else:
    MAGISTRAL_SP = (
        "First draft your thinking process (inner monologue) until you arrive at "
        "a response. Write both your thoughts and the response in the same "
        "language as the input.\n\n"
        "Your thinking process must follow the template below:\n"
        "[THINK]\nYour thoughts or/and draft, like working through an exercise on "
        "scratch paper. Be as casual and as long as you want until you are "
        "confident to generate the response.\n[/THINK]\n\n"
        "Here, provide a self-contained response."
    )
    log("SYSTEM_PROMPT.txt not found; using the documented fallback")

log(f"Loading {args.model}  4bit={args.load_in_4bit}")
model, tok = FastModel.from_pretrained(
    model_name=args.model, max_seq_length=args.max_seq_length,
    load_in_4bit=args.load_in_4bit, load_in_8bit=False, full_finetuning=False)
try:
    FastModel.for_inference(model)
except Exception as e:
    log(f"(for_inference skipped: {e})")
text_tok = getattr(tok, "tokenizer", tok)
PAD = text_tok.pad_token_id if text_tok.pad_token_id is not None else text_tok.eos_token_id
log("Model loaded.")

ds = load_from_disk(args.dataset)[args.split]
if args.limit > 0:
    ds = ds.select(range(min(args.limit, len(ds))))
log(f"Running on {len(ds)} records. temp={args.temperature} "
    f"max_new_tokens={args.max_new_tokens}")

for i, ex in enumerate(ds):
    pmid = ex["metadata"]["pmid"]
    out_path = os.path.join(out_dir, f"{pmid}.txt")
    if os.path.exists(out_path):
        log(f"[{i+1}/{len(ds)}] {pmid} already done, skipping")
        continue

    msgs = [dict(m) for m in ex["messages"] if m["role"] != "assistant"]
    if msgs and msgs[0]["role"] == "system":
        msgs[0]["content"] = MAGISTRAL_SP + "\n\n" + msgs[0]["content"]
    else:
        msgs.insert(0, {"role": "system", "content": MAGISTRAL_SP})

    prompt = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
    ids = text_tok(prompt, return_tensors="pt").input_ids.to(model.device)

    t0 = time.time()
    with torch.no_grad():
        out = model.generate(
            input_ids=ids, attention_mask=torch.ones_like(ids),
            max_new_tokens=args.max_new_tokens, pad_token_id=PAD,
            do_sample=True, temperature=args.temperature, top_p=args.top_p)
    gen = out[0][ids.shape[1]:]

    text = text_tok.decode(gen, skip_special_tokens=False)
    for sp in ["<s>", "</s>", "<unk>", "<pad>"]:
        text = text.replace(sp, "")
    had_think = "[/THINK]" in text
    text = text.replace("[THINK]", "<think>").replace("[/THINK]", "</think>")
    text = text.strip()

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)

    dt = time.time() - t0
    log(f"[{i+1}/{len(ds)}] {pmid} {dt:.0f}s {int(gen.shape[0])}tok "
        f"think_closed={had_think} "
        f"hit_cap={int(gen.shape[0]) >= args.max_new_tokens}")

log(f"All outputs saved to {out_dir}")
