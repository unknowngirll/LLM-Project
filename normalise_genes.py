#!/usr/bin/env python3
"""
normalise_genes.py - post-hoc gene-symbol normalisation before scoring.
Reads model output dirs, rewrites the `target` field to an official HGNC
symbol where possible, writes a parallel dir. Originals untouched.

Rules, applied in order (each tracked so contributions can be reported):
  R1 split   - "A + B" / "A/B" / "A and B"  -> one observation per gene
  R2 mirna   - strip species prefix + arm suffix (mmu-miR-204-5p -> MIR-204)
  R3 format  - uppercase, strip Greek letters, punctuation, spaces
  R4 hgnc    - alias / previous symbol / gene name -> official symbol
  R5 ortholog- strip a mouse/rat suffix when the stem is itself official
  R6 context - resolve an alias HGNC calls ambiguous, or an NCBI-only
               synonym, by scoring each candidate gene's names against the
               paper's own text. Needs --abstracts; off otherwise.

R6 exists because the OA literature's commonest aliases are exactly the ones
a bare lookup cannot decide: RAGE is {AGER, MOK}, PAR2 is {F2RL1, NR1I2,
SLC52A1}, ST2 is {IL1RL1, SDCBP2, SULT2A1}. Dropping them (the old
`len(v)==1` rule) loses the record; picking arbitrarily invents one. The
paper itself says which is meant - it spells the name out - so the tie-break
is read from the abstract rather than from a hand-written list.
"""
import os, re, csv, gzip, json, glob, argparse, unicodedata
from collections import Counter, defaultdict

ap = argparse.ArgumentParser()
ap.add_argument("--pred_dirs", nargs="+", required=True)
ap.add_argument("--hgnc", default=os.path.expanduser("~/scratch/ref/hgnc_complete_set.txt"))
ap.add_argument("--ncbi_gene_info", default=None,
                help="Homo_sapiens.gene_info.gz; adds synonyms, only trusted "
                     "when the abstract confirms them")
ap.add_argument("--abstracts", default=None,
                help="JSONL/TSV of pmid -> title+abstract text; enables R6")
ap.add_argument("--out_root", default="results_norm")
ap.add_argument("--report", default="results/normalisation_report.csv")
ap.add_argument("--no_split", action="store_true", help="disable R1")
args = ap.parse_args()

GREEK = {"α":"A","β":"B","γ":"G","δ":"D","ε":"E","κ":"K","λ":"L","μ":"M",
         "σ":"S","τ":"T","ω":"W","ζ":"Z","η":"H","θ":"T","ι":"I","ν":"N","ρ":"R"}
GREEK_WORD = [("alpha","A"),("beta","B"),("gamma","G"),("delta","D"),
              ("epsilon","E"),("kappa","K"),("lambda","L"),("sigma","S"),("zeta","Z")]

CODING = {"protein-coding gene", "non-coding RNA"}

def is_codingish(row):
    """Pseudogenes and Ig/TCR segments share aliases with real genes and never
    appear in this corpus, so they only create false ambiguity (OPG collides
    with the pseudogene BTF3P11, A20 with IGKV1-27)."""
    lt = row.get("locus_type") or ""
    return (row.get("locus_group") in CODING
            and not lt.startswith("immunoglobulin")
            and not lt.startswith("T cell receptor"))

def load_hgnc(path):
    """Return (alias -> {symbols}, official, symbol -> {descriptive names}).

    Candidates are kept as sets rather than collapsed: an alias with several
    candidates is R6's job, not a reason to discard it. The `name` columns
    matter because papers write "sclerostin", "opticin", "perforin",
    "tenascin C" - HGNC gene NAMES, not alias symbols.
    """
    cand, names = defaultdict(set), defaultdict(set)
    official = set()
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            sym = (row.get("symbol") or "").strip()
            if not sym or not is_codingish(row):
                continue
            official.add(sym.upper())
            keys = [sym]
            for col in ("alias_symbol", "prev_symbol", "alias_name",
                        "prev_name", "name"):
                v = (row.get(col) or "").strip().strip('"')
                if v:
                    parts = [x for x in v.split("|") if x]
                    keys += parts
                    if col != "alias_symbol" and col != "prev_symbol":
                        names[sym] |= set(parts)
            for k in keys:
                cand[squash(k)].add(sym)
    return cand, official, names

def load_ncbi(path, official, names):
    """NCBI synonyms are broader than HGNC's and noisier - "FSH" is listed for
    BRD2. They are kept in a separate tier that R6 only accepts with textual
    support from the paper."""
    syn = defaultdict(set)
    if not path:
        return syn
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8", errors="ignore") as fh:
        for row in csv.DictReader(fh, delimiter="\t"):
            if row.get("#tax_id") != "9606":
                continue
            sym = (row.get("Symbol") or "").strip()
            if sym.upper() not in official:
                continue
            for col in ("Full_name_from_nomenclature_authority", "Other_designations"):
                names[sym] |= {x for x in (row.get(col) or "").split("|") if x and x != "-"}
            for k in (row.get("Synonyms") or "").split("|"):
                if k and k != "-":
                    syn[squash(k)].add(sym)
    return syn

def squash(s):
    """Deterministic key: uppercase, Greek -> Latin, drop non-alphanumerics."""
    s = unicodedata.normalize("NFKC", s or "")
    for g, l in GREEK.items():
        s = s.replace(g, l).replace(g.upper(), l)
    low = s.lower()
    for w, l in GREEK_WORD:
        low = low.replace("-" + w, l.lower()).replace(w, l.lower())
    return re.sub(r"[^A-Za-z0-9]", "", low).upper()

MIRNA = re.compile(r"^(?:mmu|hsa|rno|has)?-?(?:micro-?rna|mirna|mir)-?([0-9]+[a-z]?)"
                   r"(?:-[0-9])?(?:-[35]p)?$", re.I)

# Words too generic to distinguish one gene's description from another's.
STOP = set("the a an of and or for to in with by protein receptor gene family "
           "member type factor human like associated".split())

def content_words(s):
    return {w for w in re.findall(r"[a-z]{4,}", (s or "").lower()) if w not in STOP}

def best_by_context(cands, ctx_words, names):
    """Score each candidate gene by how much of its descriptive naming appears
    in the paper. Returns (symbol, top, runner_up); symbol is None on a tie."""
    scored = sorted(((len(content_words(" ".join(names.get(c, ()))) & ctx_words), c)
                     for c in cands), reverse=True)
    top, sym = scored[0]
    runner = scored[1][0] if len(scored) > 1 else -1
    return (sym if top > 0 and top > runner else None), top, runner

def norm_one(raw, maps, stats, ctx_words=None):
    """Return normalised symbol for a single gene token."""
    cand, official, names, ncbi = maps
    t = (raw or "").strip()
    if not t:
        return t
    m = MIRNA.match(t.replace(" ", ""))
    if m:
        stats["R2_mirna"] += 1
        return "MIR-" + m.group(1).upper()
    key = squash(t)
    if not key:
        return t.upper()
    if key in official:
        stats["R3_format"] += 1
        return key
    hits = cand.get(key, set())
    if len(hits) == 1:
        stats["R4_hgnc"] += 1
        return next(iter(hits))
    if len(hits) > 1 and ctx_words:                       # R6, trusted tier
        sym, _, _ = best_by_context(hits, ctx_words, names)
        if sym:
            stats["R6_context"] += 1
            return sym
    if not hits and ctx_words:                            # R6, NCBI-only tier
        syn = ncbi.get(key, set())
        if syn:
            sym, _, _ = best_by_context(syn, ctx_words, names)
            if sym:
                stats["R6_ncbi"] += 1
                return sym
    # R5: mouse/rat ortholog suffix. "Cd59a"/"Nos2a" carry a trailing letter the
    # human symbol lacks. Only strip it when the stem is itself official, so
    # real family members (PPARG, FOXO3, ADAMTS5) are untouched.
    if len(key) > 3 and key[-1].isalpha() and not raw.strip()[-1].isupper():
        stem = key[:-1]
        if stem in official:
            stats["R5_ortholog"] += 1
            return stem
        if len(cand.get(stem, set())) == 1:
            stats["R5_ortholog"] += 1
            return next(iter(cand[stem]))
    stats["R3_format"] += 1
    return key

SPLIT = re.compile(r"\s*(?:\+|;|\band\b|&)\s*")

def split_target(raw):
    parts = [p for p in SPLIT.split(raw or "") if p.strip()]
    return parts if len(parts) > 1 else [raw]

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

def load_abstracts(path):
    """pmid -> text, from JSONL ({"pmid":..,"abstract":..}) or a 2-column TSV."""
    out = {}
    if not path:
        return out
    with open(path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            if line.startswith("{"):
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                pmid = str(r.get("pmid") or r.get("PMID") or "")
                txt = " ".join(str(r.get(k, "")) for k in ("title", "abstract", "text"))
            else:
                parts = line.split("\t")
                if len(parts) < 2:
                    continue
                pmid, txt = parts[0], " ".join(parts[1:])
            if pmid:
                out[pmid] = txt
    return out

cand, official, names = load_hgnc(args.hgnc)
ncbi = load_ncbi(args.ncbi_gene_info, official, names)
maps = (cand, official, names, ncbi)
abstracts = load_abstracts(args.abstracts)
n_amb = sum(1 for v in cand.values() if len(v) > 1)
print(f"HGNC: {len(cand)} alias keys ({n_amb} ambiguous), {len(official)} official symbols"
      f"{f'; NCBI synonyms: {len(ncbi)}' if ncbi else ''}")
print("R6 context disambiguation: "
      + (f"ON ({len(abstracts)} abstracts)" if abstracts else "OFF (no --abstracts)"))
print()

report = []
for d in args.pred_dirs:
    files = [f for f in glob.glob(d + "/*.txt") if not f.endswith("_raw.txt")]
    if not files:
        print(f"  SKIP (empty): {d}")
        continue
    # lstrip("/") matters: os.path.join with an absolute second argument
    # discards out_root and would write the normalised files back over the
    # predictions.
    out_dir = os.path.join(args.out_root,
                           d.replace("results/", "").rstrip("/").lstrip("/"))
    os.makedirs(out_dir, exist_ok=True)
    stats = Counter()
    changes = Counter()
    for f in files:
        text = open(f, encoding="utf-8", errors="ignore").read()
        data = extract_json(text)
        if data is None:
            stats["parse_fail"] += 1
            open(os.path.join(out_dir, os.path.basename(f)), "w").write(text)
            continue
        if isinstance(data, dict) and data.get("result"):
            json.dump(data, open(os.path.join(out_dir, os.path.basename(f)), "w"))
            stats["negative"] += 1
            continue
        obs = data.get("observations", []) if isinstance(data, dict) else []
        # Context for R6: the paper's own text if supplied, else the evidence
        # snippets the model quoted out of it (thinner, but the same source).
        pmid = os.path.splitext(os.path.basename(f))[0]
        ctx = abstracts.get(pmid) or " ".join(
            str(o.get("evidence_snippet", "")) for o in obs)
        ctx_words = content_words(ctx) if ctx else None
        new_obs = []
        for o in obs:
            raw = o.get("target", "")
            parts = [raw] if args.no_split else split_target(raw)
            if len(parts) > 1:
                stats["R1_split"] += 1
            for p in parts:
                o2 = dict(o)
                o2.setdefault("target_raw", raw)
                sym = norm_one(p, maps, stats, ctx_words)
                if squash(p) != squash(sym) or len(parts) > 1:
                    changes[f"{p.strip()} -> {sym}"] += 1
                o2["target"] = sym
                new_obs.append(o2)
        for i, o in enumerate(new_obs, 1):
            o["observation_number"] = i
        json.dump({"observations": new_obs},
                  open(os.path.join(out_dir, os.path.basename(f)), "w"), ensure_ascii=False)
        stats["files"] += 1
    print(f"  {d}  -> {out_dir}")
    print(f"     files={stats['files']} negatives={stats['negative']} "
          f"parse_fail={stats['parse_fail']}")
    print(f"     R1_split={stats['R1_split']} R2_mirna={stats['R2_mirna']} "
          f"R3_format={stats['R3_format']} R4_hgnc={stats['R4_hgnc']} "
          f"R5_ortholog={stats['R5_ortholog']} "
          f"R6_context={stats['R6_context']} R6_ncbi={stats['R6_ncbi']}")
    top = changes.most_common(8)
    if top:
        print("     top changes: " + ", ".join(f"{k}({v})" for k, v in top))
    print()
    for k, v in changes.items():
        report.append({"dir": d, "change": k, "count": v})

os.makedirs(os.path.dirname(args.report) or ".", exist_ok=True)
with open(args.report, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["dir", "change", "count"])
    w.writeheader(); [w.writerow(r) for r in report]
print(f"Change log -> {args.report}")
