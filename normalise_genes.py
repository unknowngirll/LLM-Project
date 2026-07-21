#!/usr/bin/env python3
"""
normalise_genes.py - post-hoc gene-symbol normalisation before scoring.
Reads model output dirs, rewrites the `target` field to an official HGNC
symbol where possible, writes a parallel dir. Originals untouched.

Rules, applied in order (each tracked so contributions can be reported):
  R1 split   - "A + B" / "A/B" / "A and B"  -> one observation per gene
  R2 mirna   - strip species prefix + arm suffix (mmu-miR-204-5p -> MIR-204)
  R3 format  - uppercase, strip Greek letters, punctuation, spaces
  R4 hgnc    - alias / previous symbol -> official symbol (unambiguous only)
"""
import os, re, csv, json, glob, argparse, unicodedata
from collections import Counter, defaultdict

ap = argparse.ArgumentParser()
ap.add_argument("--pred_dirs", nargs="+", required=True)
ap.add_argument("--hgnc", default=os.path.expanduser("~/scratch/ref/hgnc_complete_set.txt"))
ap.add_argument("--out_root", default="results_norm")
ap.add_argument("--report", default="results/normalisation_report.csv")
ap.add_argument("--no_split", action="store_true", help="disable R1")
args = ap.parse_args()

GREEK = {"α":"A","β":"B","γ":"G","δ":"D","ε":"E","κ":"K","λ":"L","μ":"M",
         "σ":"S","τ":"T","ω":"W","ζ":"Z","η":"H","θ":"T","ι":"I","ν":"N","ρ":"R"}
GREEK_WORD = [("alpha","A"),("beta","B"),("gamma","G"),("delta","D"),
              ("epsilon","E"),("kappa","K"),("lambda","L"),("sigma","S"),("zeta","Z")]

def load_hgnc(path):
    """alias/prev/symbol (upper, punctuation-free) -> official symbol; ambiguous dropped."""
    cand = defaultdict(set)
    official = set()
    with open(path, encoding="utf-8", errors="ignore") as fh:
        rd = csv.DictReader(fh, delimiter="\t")
        for row in rd:
            sym = (row.get("symbol") or "").strip()
            if not sym:
                continue
            official.add(sym.upper())
            keys = [sym]
            for col in ("alias_symbol", "prev_symbol"):
                v = (row.get(col) or "").strip().strip('"')
                if v:
                    keys += [x for x in v.split("|") if x]
            for k in keys:
                cand[squash(k)].add(sym)
    return {k: list(v)[0] for k, v in cand.items() if len(v) == 1}, official

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

def norm_one(raw, amap, official, stats):
    """Return normalised symbol for a single gene token."""
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
    if key in amap:
        stats["R4_hgnc"] += 1
        return amap[key]
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

amap, official = load_hgnc(args.hgnc)
print(f"HGNC map: {len(amap)} unambiguous keys, {len(official)} official symbols\n")

report = []
for d in args.pred_dirs:
    files = [f for f in glob.glob(d + "/*.txt") if not f.endswith("_raw.txt")]
    if not files:
        print(f"  SKIP (empty): {d}")
        continue
    out_dir = os.path.join(args.out_root, d.replace("results/", "").rstrip("/"))
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
        new_obs = []
        for o in obs:
            raw = o.get("target", "")
            parts = [raw] if args.no_split else split_target(raw)
            if len(parts) > 1:
                stats["R1_split"] += 1
            for p in parts:
                o2 = dict(o)
                o2.setdefault("target_raw", raw)
                sym = norm_one(p, amap, official, stats)
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
          f"R3_format={stats['R3_format']} R4_hgnc={stats['R4_hgnc']}")
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
