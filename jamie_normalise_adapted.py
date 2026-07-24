#!/usr/bin/env python3
"""
jamie_normalise_adapted.py

Supervisor's normalisation pipeline, adapted from TSV/GEO input to this
project's JSON model outputs.

Per extracted gene:
  1. direct lookup in symbol_lookup.pkl        (exact, free)
  2. rapidfuzz over synonyms -> top-k candidates
  3. LLM adjudicates between candidates        (only when 1 fails)

Decisions are cached per unique gene string, so the LLM runs once per
distinct name rather than once per observation.
Original outputs are never modified; normalised copies go to --out_root.
"""
import sys, os, re, json, glob, csv, pickle, argparse
from pathlib import Path
from collections import Counter, defaultdict

ap = argparse.ArgumentParser()
ap.add_argument("--pred_dirs", nargs="+", required=True)
ap.add_argument("--gene_db",
                default=os.path.expanduser("~/scratch/ref/jamie_normalisation/gene_database"))
ap.add_argument("--model", default="models/Qwen3-8B")
ap.add_argument("--out_root", default="results_jamie")
ap.add_argument("--report", default="results/jamie_normalisation_report.csv")
ap.add_argument("--top_k", type=int, default=5)
ap.add_argument("--score_cutoff", type=int, default=70)
ap.add_argument("--load_in_4bit", action="store_true")
ap.add_argument("--max_seq_length", type=int, default=8192)
ap.add_argument("--dry_run", action="store_true",
                help="direct + fuzzy only; no LLM, no GPU needed")
ap.add_argument("--pre_rules", action="store_true",
                help="apply split + miRNA rules before lookup, so this pipeline "
                     "and the HGNC one differ only in alias resolution")
args = ap.parse_args()

if not args.dry_run:
    import unsloth
    from unsloth import FastModel
    import torch
from rapidfuzz import process, fuzz


# ---------------- gene database ----------------
class OfflineGeneDB:
    def __init__(self, path):
        p = Path(path)
        self.genes  = pickle.load(open(p / "genes.pkl", "rb"))
        self.lookup = pickle.load(open(p / "symbol_lookup.pkl", "rb"))
        self.syn = {}
        for g in self.genes:
            for s in (g.get("synonyms") or []):
                if s:
                    self.syn.setdefault(s, g)
        self.syn_keys = list(self.syn.keys())
        print(f"gene DB: {len(self.genes)} genes, {len(self.lookup)} symbols, "
              f"{len(self.syn)} synonyms", flush=True)

    def direct(self, q):
        return self.lookup.get((q or "").strip().upper())

    def fuzzy(self, q, limit, cutoff):
        hits = process.extract(q, self.syn_keys, scorer=fuzz.token_set_ratio,
                               limit=limit, score_cutoff=cutoff)
        out = []
        for match, score, _ in hits:
            g = dict(self.syn[match])
            g["matched_synonym"] = match
            g["fuzzy_score"] = score
            out.append(g)
        return out


# ---------------- LLM adjudicator ----------------
class Adjudicator:
    def __init__(self, model_path, four_bit, max_seq):
        print(f"loading adjudicator: {model_path}", flush=True)
        self.model, self.tok = FastModel.from_pretrained(
            model_name=model_path, max_seq_length=max_seq,
            load_in_4bit=four_bit, load_in_8bit=False, full_finetuning=False)
        try:
            FastModel.for_inference(self.model)
        except Exception as e:
            print(f"(for_inference skipped: {e})", flush=True)
        self.text_tok = getattr(self.tok, "tokenizer", self.tok)
        print("adjudicator ready.", flush=True)

    def build_prompt(self, original, cands, context):
        lines = []
        for i, g in enumerate(cands[:8], 1):
            syn = ", ".join((g.get("synonyms") or [])[:12]) or "None"
            summ = (g.get("summary") or "No summary available")[:600]
            lines.append(f"{i}. Symbol: {g['symbol']}\n"
                         f"   Description: {g.get('description','No description')}\n"
                         f"   Synonyms: {syn}\n"
                         f"   Summary: {summ}")
        ctx = f"\nContext from the abstract:\n{context}\n" if context else ""
        return (
            "You are a bioinformatics expert normalising gene symbols extracted "
            "from osteoarthritis research abstracts.\n\n"
            f'Gene name as written in the abstract: "{original}"\n'
            f"{ctx}\n"
            "Candidate genes from the NCBI database:\n"
            + "\n\n".join(lines) +
            f'\n\nTask: decide which ONE candidate is the correct match for "{original}".\n\n'
            "Instructions:\n"
            f'1. Check whether "{original}" appears in any candidate\'s synonym list.\n'
            "2. Consider case-insensitive and punctuation-insensitive matches.\n"
            "3. Use the abstract context for biological plausibility.\n"
            "4. Prefer exact synonym matches over contextual ones.\n"
            "5. If none is a convincing match, answer SYMBOL: NONE.\n\n"
            "Respond ONLY in this format:\n"
            "SYMBOL: [official gene symbol or NONE]\n"
            "REASONING: [one short sentence]")

    def decide(self, original, cands, context=""):
        msgs = [{"role": "user", "content": self.build_prompt(original, cands, context)}]
        try:
            text = self.tok.apply_chat_template(msgs, tokenize=False,
                                                add_generation_prompt=True,
                                                enable_thinking=False)
        except TypeError:
            text = self.tok.apply_chat_template(msgs, tokenize=False,
                                                add_generation_prompt=True)
        ids = self.text_tok(text, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            out = self.model.generate(**ids, max_new_tokens=256, do_sample=False,
                                      pad_token_id=self.text_tok.eos_token_id)
        gen = self.text_tok.decode(out[0][ids["input_ids"].shape[1]:],
                                   skip_special_tokens=True)
        m = re.search(r"SYMBOL:\s*([A-Za-z0-9._/-]+)", gen)
        r = re.search(r"REASONING:\s*(.+?)(?:\n|$)", gen, re.DOTALL)
        sym = m.group(1).strip().upper() if m else "NONE"
        return sym, (r.group(1).strip()[:200] if r else "")


# ---------------- JSON helpers ----------------
def extract_json(text):
    body = text.rsplit("</think>", 1)[1] if "</think>" in text else \
           re.sub(r"<think>.*", "", text, flags=re.DOTALL)
    for pat in (r"\{.*\}", r"\{.*?\}"):
        m = re.search(pat, body, flags=re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                continue
    return None


# ---------------- main ----------------
db = OfflineGeneDB(args.gene_db)
adj = None if args.dry_run else Adjudicator(args.model, args.load_in_4bit,
                                            args.max_seq_length)

cache, log, stats = {}, [], Counter()

MIRNA = re.compile(r"^(?:mmu|hsa|rno|has)?-?(?:micro-?rna|mirna|mir)-?([0-9]+[a-z]?)"
                   r"(?:-[0-9])?(?:-[35]p)?$", re.I)
SPLIT = re.compile(r"\s*(?:\+|;|\band\b|&)\s*")

def split_target(raw):
    parts = [p for p in SPLIT.split(raw or "") if p.strip()]
    return parts if len(parts) > 1 else [raw]

def resolve(raw, context):
    """Return (symbol, method). Cached per distinct raw name."""
    if args.pre_rules:
        m = MIRNA.match((raw or "").strip().replace(" ", ""))
        if m:
            stats["pre_mirna"] += 1
            return "MIR-" + m.group(1).upper(), "pre_mirna"
    key = (raw or "").strip().upper()
    if not key:
        return raw, "empty"
    if key in cache:
        stats["cached"] += 1
        return cache[key]

    hit = db.direct(key)
    if hit:
        res = (hit["symbol"], "direct")
        cache[key] = res
        stats["direct"] += 1
        log.append({"original": raw, "normalised": hit["symbol"],
                    "method": "direct", "reasoning": "exact symbol match"})
        return res

    cands = db.fuzzy(f"{raw} gene human", args.top_k, args.score_cutoff)
    if not cands:
        res = (raw, "no_candidates")
        cache[key] = res
        stats["no_candidates"] += 1
        log.append({"original": raw, "normalised": raw,
                    "method": "none", "reasoning": "no fuzzy candidates"})
        return res

    if args.dry_run:
        res = (raw, "needs_llm")
        cache[key] = res
        stats["needs_llm"] += 1
        log.append({"original": raw, "normalised": "(pending)", "method": "needs_llm",
                    "reasoning": "candidates: " +
                                 ", ".join(f"{c['symbol']}({c['fuzzy_score']:.0f})"
                                           for c in cands[:args.top_k])})
        return res

    sym, why = adj.decide(raw, cands, context)
    if sym in ("NONE", "") or not db.lookup.get(sym):
        res = (raw, "llm_declined")
        stats["llm_declined"] += 1
    else:
        res = (sym, "llm")
        stats["llm"] += 1
    cache[key] = res
    log.append({"original": raw, "normalised": res[0],
                "method": res[1], "reasoning": why})
    print(f"  LLM: {raw!r} -> {res[0]}   ({why[:70]})", flush=True)
    return res


for d in args.pred_dirs:
    files = [f for f in glob.glob(d + "/*.txt") if not f.endswith("_raw.txt")]
    if not files:
        print(f"SKIP (empty): {d}", flush=True)
        continue
    out_dir = os.path.join(args.out_root, d.replace("results/", "").rstrip("/"))
    os.makedirs(out_dir, exist_ok=True)
    print(f"\n=== {d}  ({len(files)} files) ===", flush=True)

    for f in files:
        text = open(f, encoding="utf-8", errors="ignore").read()
        data = extract_json(text)
        dst = os.path.join(out_dir, os.path.basename(f))
        if data is None:
            open(dst, "w").write(text)
            stats["parse_fail"] += 1
            continue
        if isinstance(data, dict) and data.get("result"):
            json.dump(data, open(dst, "w"))
            stats["negative"] += 1
            continue
        obs = data.get("observations", []) if isinstance(data, dict) else []
        new_obs = []
        for o in obs:
            raw = o.get("target", "")
            parts = split_target(raw) if args.pre_rules else [raw]
            if len(parts) > 1:
                stats["pre_split"] += 1
            for part in parts:
                o2 = dict(o)
                o2.setdefault("target_raw", raw)
                sym, method = resolve(part, o.get("evidence_snippet", "")[:300])
                o2["target"] = sym
                o2["normalisation_method"] = method
                new_obs.append(o2)
        for k, o in enumerate(new_obs, 1):
            o["observation_number"] = k
        obs = new_obs
        json.dump({"observations": obs}, open(dst, "w"), ensure_ascii=False)
        stats["files"] += 1

print("\n=== summary ===")
for k in ["files", "negative", "parse_fail", "direct", "llm",
          "llm_declined", "needs_llm", "no_candidates", "cached"]:
    if stats[k]:
        print(f"  {k:15s} {stats[k]}")
print(f"  distinct gene names: {len(cache)}")

os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
with open(args.report, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["original", "normalised", "method", "reasoning"])
    w.writeheader()
    [w.writerow(r) for r in log]
print(f"\nlog -> {args.report}")
