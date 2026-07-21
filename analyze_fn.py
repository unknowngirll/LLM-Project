import csv, re
from pathlib import Path
from collections import Counter
TABLE = "results/qwen36_table.csv"
PRED_DIR = Path("results/qwen36_full/Qwen3.6-27B")
ABS_DIR = Path("data/abstracts")
fn_pmids = set()
for r in csv.DictReader(open(TABLE)):
    if r["row_type"] == "FN":
        fn_pmids.add(r["PMID"])
def gave_nothing(pmid):
    f = PRED_DIR / f"{pmid}.txt"
    if not f.exists():
        return False
    t = f.read_text(encoding="utf-8")
    return bool(re.search(r'"observations"\s*:\s*\[\s*\]', t)) or '"result"' in t
PATTERNS = {
    "in_vitro/cell": r"(in vitro|cell culture|cultured|chondrocyte|primary cell)",
    "inflammatory": r"(il-?1|interleukin-?1|tnf|necrosis|collagen-induced|antibody-induced|rheumatoid)",
    "pain_only": r"(pain|nocicep|hyperalgesi|allodyni|mechanosensitiv)",
    "ageing/spont": r"(aging|ageing|spontaneous|aged mice|str/ort|dunkin)",
    "collagenase": r"collagenase",
    "herbal": r"(herbal|traditional medicine|extract|decoction)",
}
full_reject = 0
partial = 0
pat = Counter()
rejected_list = []
for pmid in sorted(fn_pmids):
    af = ABS_DIR / f"{pmid}.txt"
    text = af.read_text(encoding="utf-8").lower() if af.exists() else ""
    if gave_nothing(pmid):
        full_reject += 1
        rejected_list.append(pmid)
    else:
        partial += 1
    for name, p in PATTERNS.items():
        if re.search(p, text):
            pat[name] += 1
print(f"FN papers total: {len(fn_pmids)}")
print(f"  fully rejected (observations=[]): {full_reject}")
print(f"  partial miss: {partial}")
print("\nKeyword patterns in FN papers:")
for name in PATTERNS:
    print(f"  {name:16s} {pat[name]:3d} / {len(fn_pmids)}")
print("\nFully-rejected PMIDs:")
print("  " + " ".join(rejected_list))
