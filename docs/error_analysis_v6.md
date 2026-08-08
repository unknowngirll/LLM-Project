# Error analysis — prompt v6 (full + lite), Magistral-Small-2509 and Qwen3-8B

Follows `error_analysis_magistral_v5.md`. Sources: `results/magistral_v6full_table.csv`,
`results/magistral_v6lite_table.csv`, the `*_raw.csv` (pre-`normalise_genes.py`)
counterparts, `results/qwen3-8b_v6{full,lite}_table_raw.csv`, and the four v6
trace files in `reasoning_traces/`. HGNC table read from
`/home/njs289/CBF/llm_ripple/hgnc_complete_set.txt`.

All figures below are recomputed from the tables with the same row-counting used
in the v5 doc, so v5 and v6 are directly comparable.

## 1. Headline

| Run | Prompt | norm | TP | FP | FN | P | R | **F1** |
|---|---|---|---|---|---|---|---|---|
| Magistral | v5 | hgnc | 243 | 100 | 42 | 0.708 | 0.853 | 0.774 |
| Magistral | **v6 full** | hgnc | 233 | 63 | 52 | **0.787** | 0.818 | **0.802** |
| Magistral | v6 full | none | 217 | 82 | 68 | 0.726 | 0.761 | 0.743 |
| Magistral | **v6 lite** | hgnc | 227 | 56 | 58 | **0.802** | 0.796 | 0.799 |
| Magistral | v6 lite | none | 206 | 77 | 79 | 0.728 | 0.723 | 0.725 |
| Qwen3-8B | v6 full | none | 191 | 79 | 94 | 0.707 | 0.670 | 0.688 |
| Qwen3-8B | v6 lite | none | 184 | 78 | 101 | 0.702 | 0.646 | 0.673 |

v6 bought **+0.028 F1** on Magistral, entirely through precision (+0.079), and
gave back 0.035 of recall. Sampling is `temperature=0.7, top_p=0.95`, so treat a
single run's few-point delta as provisional.

**v6 full and v6 lite are indistinguishable on Magistral** (0.802 vs 0.799; lite
is actually the more precise of the two). The four extra worked examples buy
nothing measurable. On Qwen3-8B full is ahead by 0.015, also within noise. The
lite prompt is the better default.

## 2. What worked

**2.1 The X1–X8 eligibility gate — the whole of the gain.** Papers with zero gold
observations that the model extracted from anyway:

| Run | over-extracted no-gold papers |
|---|---|
| Magistral v5 | 31 |
| Magistral v6 full | **9** |
| Magistral v6 lite | **4** |
| Qwen3-8B v6 full / lite | 2 / 4 |

25 of the 31 v5 eligibility errors are gone; 3 new ones appeared (10806052,
11677139, 20621685). This is the single most successful change in the revision
and should be carried forward untouched. The Qwen traces show the rules being
cited by number, so they transfer across models.

**2.2 De-guessing symbols worked exactly as designed.** The HGNC post-processing
gain was +0.01 F1 under v5 because the model had already written a confidently
wrong symbol. Under v6 it is **+0.059** (full) and **+0.074** (lite) — the model
now hands the mapper recoverable tokens. This was diagnostic #3 in the v5 doc's
proposed ablation and it passes.

**2.3 Abstains fell.** Induction `Not stated` 36 → 16, species 11 → 4 (Magistral
full). RULE 4 and the COMMIT TO A VALUE block did their job.

**2.4 Markdown fences fell**, contrary to the concern in the v5 doc: counting
only what follows `--- FINAL JSON ---`, 18/267 under v5 → **2/267** under v6 full,
3/267 lite, 0/267 for both Qwen runs. RULE 6 works; keep it.

**2.5 `target_is_official_symbol` is well calibrated and currently unused.**
Of Magistral's 243 observations flagged `true`, 239 really are official HGNC
symbols (98.4% precision); only RAGE, CD59A, OPG and ZCCHC6 are misflagged. Qwen
is noisier (196/216, 90.7%). Nothing in the pipeline reads this field.

## 3. What the FP and FN rows actually are

The headline P/R hides the fact that **most errors are a single mistake counted
twice**. When the model finds the right experiment but writes an identifier that
does not match gold, the gold row becomes an FN *and* the predicted row becomes
an FP. Splitting the rows by whether they are paired that way:

| Class | What it is | v5 | **v6 full** | v6 lite | Qwen v6 full |
|---|---|---|---|---|---|
| **A** eligibility | paper has zero gold rows; model extracted anyway | 47 FP | **14 FP** | 6 FP | 5 FP |
| **B** paired identity | right paper, right experiment, wrong identifier ⇒ FP+FN from one mistake | 38 FP / 37 FN | **38 FP / 32 FN** | 36 / 33 | 64 / 65 |
| **C** extra gene | all gold genes found, plus a spurious extra molecule | 15 FP | **11 FP** | 14 FP | 10 FP |
| **D** pure miss | gene absent from output, nothing emitted in its place | 5 FN | **20 FN** | 25 FN | 29 FN |
| | **FP total / FN total** | 100 / 42 | **63 / 52** | 56 / 58 | 79 / 94 |

So for v6 full: **60% of FP rows and 62% of FN rows are the same 24 papers'
class-B errors.** Precision and recall are not two independent problems here;
one identity mistake moves both.

**Row counts overstate the number of distinct mistakes.** `make_table.py` emits
one row per *gold observation*, so missing a gene that has three gold rows
produces three FNs. The 63 FP rows are 46 distinct (paper, gene) pairs (1.37×)
and the 52 FN rows are 41 (1.27×). Read the taxonomy above as rows; read the
paper counts below as mistakes.

### 3A. Eligibility (class A) — the v6 win

Papers with no gold observations that the model extracted from anyway fell from
**31 papers (47 FP rows) under v5 to 9 papers (14 FP rows)**, and to 4 papers
under v6 lite. This is where the +0.079 precision came from, and it is the one
result that transfers cleanly across models (Qwen: 2 papers). Carry X1–X8
forward untouched.

### 3B. Paired identity errors (class B) — 24 papers, and only 10 are normalisation

This is the class the v5 doc called "the dominant failure", and it is worth
separating properly, because the two halves need different fixes. Running the
improved normaliser (§8) over what the model actually emitted:

**Recovered — 10 papers, 12 FN rows. Pure normalisation, now fixed:**

| PMID | model emitted | resolves to | gold |
|---|---|---|---|
| 17326835 | `GAL3` | LGALS3 | LGALS3 |
| 19342682 | `RAGE` | AGER | AGER |
| 25200274 | `PAR1`, `PAR2` | F2R, F2RL1 | F2R, F2RL1 |
| 26698846, 31841119 | `PAR2` | F2RL1 | F2RL1 |
| 27541035 | `OPG` | TNFRSF11B | TNFRSF11B |
| 29219023 | `TENASCINC` | TNC | TNC |
| 33133598 | `ST2` | IL1RL1 | IL1RL1 |
| 33827816 | `SPLA2` | PLA2G2A | PLA2G2A |
| 34463587 | `A20` | TNFAIP3 | TNFAIP3 |

The model was right in every one of these. v6 successfully taught it to emit a
recoverable alias and the mapper could not finish the job.

**Not recovered — 14 papers, 20 FN rows. Real errors, needing prompt rules:**

| Sub-class | Papers | Detail |
|---|---|---|
| Ligand/receptor or signalling partner | 4 | 34136574 `CXCR4` for CXCL12; 37144868 `GAS6` for AXL; 31901095 `FGFR` for FGF2; 25969431 `TLR4` for S100A9 |
| Wrong family sibling or bare stem | 4 | 30144298 `KDR` for FLT4; 34987154 `PPARA` for PPARG; 27681622 `NFKB1` for RELA; 24757033 `GSK3` for GSK3B |
| Model guessed a symbol it did not know | 2 | 24966136 `MDFIC` for Mig-6/ERRFI1; 29622035 `CSF2` for PTGS2 |
| Normaliser resolved to the wrong gene | 2 | 34176242 `FSH`→BRD2; 37462629 `PERF`→FABP9 |
| Gold convention, not recoverable from the abstract | 2 | 33109602 gold merges a cluster as `MIR141200C`, model correctly split `MIR-141`/`MIR-200C`; 22057346 `CD59A` (mouse suffix, blocked because the target field is already uppercase) |

v7 rules 7 and 7b target the first two sub-classes, which are 8 of the 14.

### 3C. Extra genes (class C) — 11 FP rows, 8 papers

Papers where every gold gene was found, plus a spurious extra: mechanism
partners and assay readouts emitted as perturbations. Down from 15 rows under
v5. This is X2's residue and is the smallest of the three FP classes.

### 3D. Pure misses (class D) — 20 FN rows, 14 papers

Grew from 5 rows under v5, and splits two ways:

- **9 papers (13 rows) where the model output nothing at all** — 27345362,
  29205898, 30972197, 31084709, 32938794, 34982732, 35061535, 35145063,
  37681413. These are the cost of the eligibility gate: X1–X8 over-firing on
  papers that do have gold. 4 of the 9 are new since v5.
- **5 papers (7 rows) where the model found other genes but dropped one** —
  31160553 (found WWP2, missed MIR-140), 31424112 (CCR2, missed CCL2), 32858189
  (EDN1/EDNRB, missed EDNRA), 33441426 (EGFR/HBEGF, missed TGFA), 34039624
  (RIC8A, missed CIRCPDE4B). Three of these are ligand/receptor or
  ligand/ligand pairs where only one arm was extracted — the same weakness as
  class B's first sub-class.

**So the ~13-row cost of the exclusion gate is real but is roughly a quarter of
the FN total**, and it bought a 33-row reduction in FP. The trade is favourable;
the remaining question in §8 is whether the class-B half can be recovered
without giving any of it back.

Reading the traces for those 9 drops, one is not an exclusion error at all
(32938794 produced no reasoning block — a truncated generation), and the rest
divide into two groups. Six are X1 firing on a drug whose target is named only
as a pathway or a class ("PI3K pathway inhibitor", "HDAC class I inhibitor")
where gold is more permissive than the prompt; **this is left alone**, since
loosening X1 is the most likely way to give back the class-A gain. The other two
are correctable mis-specifications rather than judgement calls, and are fixed in
v7 (§7, items 5 and 6).

## 4. The reported induction accuracy is wrong — `make_table.py` mispairs

`make_table.py:109-130` matches each gold observation to a prediction using
`manipulation_direction` only, and **never marks a prediction as consumed**. On a
paper where gold has one Surgical row and one Ageing row for the same gene, both
gold rows are scored against `plist[0]`. The table therefore reports an induction
error that the model did not make.

Recovering the actual JSON from the traces shows the models are splitting
correctly. 23233270, whose table rows read "Surgical → Spontaneous":

```
Magistral v6 full:  SOST/Spontaneous, SOST/Spontaneous, SOST/Surgical
Qwen3-8B  v6 full:  SCLEROSTIN/Spontaneous, /Chemical, /Surgical, /Surgical
```

Scoring the model's *set* of induction values per paper against gold's set:

| Run | table-reported induction acc. | true coverage of gold induction values |
|---|---|---|
| Magistral v6 full | 0.704 | **0.831** |
| Magistral v6 lite | 0.665 | 0.811 |
| Qwen3-8B v6 full | 0.634 | 0.806 |

**~13 points of the apparent induction error is a harness artifact.** This also
means the v5 doc's "under-splitting is the dominant attribute bug — 32 of 43
wrong rows" was measured with the same broken pairing and overstates the case;
STEP 2 was already working better than it looked. `score_v2.py` does greedy
induction-aware matching with a `used` set and is the more trustworthy of the
two, but the published tables come from `make_table.py`.

## 5. The real induction problem: the prompt's vocabulary is not gold's

Gold uses six values. The model was asked for a different, more abstract set:

```
gold : Surgical(376) Ageing(140) Protease(24) Exercise(14) MIA(14) High Fat Diet(2)
model: Surgical(263) Spontaneous(159) Chemical(65) Not stated(55)
       Transgenic(12) Metabolic(6) Mechanical(6)
```

Every value the model emits except `Surgical` needs a lossy crosswalk, and
`Spontaneous` has become a catch-all — it is the single largest confusion
(Surgical → Spontaneous, 29 rows) and the traces show why it is a category error:

> *"it might be best to consider it as 'Transgenic' or 'Spontaneous' since it's
> not a standard induction model"*

The model is putting the **genotype** in a field that describes the **challenge**.
`Transgenic` is never a gold value at all. v7 removes the abstraction layer and
asks for gold's own six words, with an explicit translate-away list.

The second-largest induction failure is genuine abstention on generic wording —
*"'experimental OA,' which could be surgical or chemical … we will need to use
'Not stated'"*. Since no gold row is `Not stated` and Surgical is 66% of gold,
v7 makes generic experimental induction default to Surgical.

## 6. Qwen3-8B specifics

- It **narrates X1–X8 serially on every paper** ("X1: … X2: … X7: …"), spending
  reasoning budget on a checklist that mostly does not fire. v7 tells it to apply
  the exclusions as a silent filter.
- STEP 3's *"if the alias carries a family number or letter, DO NOT MAP IT"*
  over-generalises and blocks legitimate case-normalisation. The trace shows it
  stuck on whether `Col2a1` → `COL2A1` is allowed, across several paragraphs. v7
  states that cleaning is not mapping and that uppercasing the abstract's own
  symbol is always correct.
- Qwen is scored **without** `normalise_genes.py` (only `*_raw` tables exist), so
  the normaliser fixes in §8 matter more for it than for Magistral — or it
  should be scored through `normalise_genes.py` like Magistral is.

## 7. v7 prompt changes

`Prompts_v7/` and `Prompts_v7_lite/`:

1. **X1–X8 kept verbatim** (proven, +0.079 precision), plus one line telling the
   model not to narrate them.
2. **No gene lists.** The alias problem is a normalisation problem and is fixed
   in `normalise_genes.py` (§8). The prompt keeps only the general principle:
   emit the cleaned alias, flag it `false`, let the table resolve it.
3. **"Cleaning is not mapping"** — fixes the Qwen `Col2a1` hesitation and the
   over-broad family-number ban, which now applies only to *substituting* a
   different symbol.
4. **Rule 7 — ligand/receptor, applied per arm rather than as a choice.** The
   §3 breakdown changed this rule's design. An earlier draft framed it purely as
   a precision fix ("extract the perturbed molecule, and ONLY that one"), which
   targets class B's 4 substitution errors — but §3D shows three class-D papers
   failing the *opposite* way, extracting one arm when both were perturbed
   (31424112 CCR2 without CCL2, 32858189 EDN1/EDNRB without EDNRA, 33441426
   EGFR/HBEGF without TGFA). A precision-only rule would have made those worse.
   Rule 7 now says to run the X2 test on each molecule independently and spells
   out that all three outcomes — ligand only, receptor only, both — are common,
   with the "both" case flagged as the easier one to miss. Rule 7b keeps the
   sibling discipline; 5b bans bare `NFKB` in favour of the named subunit.
5. **Rule 6b — an administered protein is its own target.** From 27345362
   (whole paper dropped, gold CALCA): the model saw an administered hormone,
   applied the drug rule, looked for a downstream gene it acts on, found none
   and rejected the paper. Rule 6's small-molecule framing was overriding STEP
   1(a)'s "recombinant protein". 6b states that a hormone, peptide, cytokine or
   growth factor IS its own gene's perturbation, direction Gain, and that this
   does not reopen X1 — a protein is a gene product, glucosamine is not.
6. **X4 narrowed to the intervertebral disc, and made per-observation.** v6
   added spine, growth plate, TMJ, tendon and ligament to X4 on no evidence; the
   v5 analysis had only ever justified intervertebral disc. Two papers show the
   cost: 30972197 (gold DNMT3B) was dropped for being TMJ, and 16947423 was
   dropped although it reported knee joints *and* TMJs. The TMJ is a synovial
   joint and gold treats it as in scope. STEP 1(d) now says so explicitly, and
   X4 states that it drops an observation rather than a paper.
7. **`oa_induction` switched to gold's own six values** — Surgical, Ageing,
   Protease, MIA, Exercise, High Fat Diet — with `Spontaneous`/`Transgenic`/
   `Chemical`/`Mechanical`/`Metabolic` explicitly banned and a translate-away
   list. Removes the crosswalk and the `Spontaneous` catch-all.
8. **"Several rows for one gene must differ"** — a direct check against emitting
   two identical `Ageing` rows for a paper that aged *and* operated on a KO.
9. **"A shared result sentence is reported once per model"** — the traces show
   the model seeing both models and choosing one because it felt "safer".

Sizes: v7 full ≈ 11.3k tokens (v6 full 9.7k), v7 lite ≈ 7.4k (v6 lite 6.5k).
`--max_seq_length 24000` remains sufficient for Magistral.

**Scorer change made:** `INDUCTION_TO_GOLD` in `score.py`, `score_v2.py`,
`score_v4.py`, `make_table.py`, `make_table_v4.py` now also accepts gold's own
vocabulary. The addition is a no-op for v5/v6 runs — no earlier run ever emitted
`protease`, `mia`, `exercise` or `high fat diet`.

**Change still needed (not made): `make_table.py` pairing (§4).** Match on
induction as well as direction and consume each prediction once, as
`score_v2.py` does. Left alone because fixing it changes every number in
`RESULTS_*.md`; it should be a deliberate, separately-reported step.

## 8. Normalisation: resolve aliases from the paper, not from a list

§3 showed the recall regression is a mapper failure. The tempting fix — a
hand-written `alias -> symbol` table — is rejected here: every entry would have
come from inspecting a dev-set false negative, which is memorising the answer
key (§9). `normalise_genes.py` instead gains four changes, none of which names
a gene.

**Label-free, always on:**

1. **Filter HGNC to `locus_group ∈ {protein-coding gene, non-coding RNA}`** and
   drop Ig/TCR segments. Pseudogenes and Ig segments never appear in this corpus
   and only manufacture ambiguity: `OPG` collided with the pseudogene BTF3P11,
   `A20` with IGKV1-27. Both now resolve.
2. **Index the `name`, `alias_name` and `prev_name` columns.** Papers write the
   HGNC *gene name* — "sclerostin", "opticin", "perforin", "tenascin C" — which
   the loader never read. Cheapest and largest of the four.
3. **R5, mouse/rat ortholog suffix**: strip a trailing lower-case letter when the
   stem is itself official (`Cd59a`→CD59, `Nos2a`→NOS2), which leaves real family
   members (PPARG, FOXO3, ADAMTS5) untouched.

**R6 — context disambiguation, opt-in via `--abstracts`:**

The old `len(v) == 1` rule discarded any alias with more than one candidate.
That is precisely the OA literature's commonest vocabulary: `RAGE` is
{AGER, MOK}, `PAR2` is {F2RL1, NR1I2, SLC52A1}, `ST2` is {IL1RL1, SDCBP2,
SULT2A1}, `COX2` is {MT-CO2, PTGER2, PTGS2}. Dropping them loses the record;
picking arbitrarily invents one.

But the paper says which is meant — it spells the name out. R6 scores each
candidate gene's descriptive names against the paper's own text and takes the
winner if it is unique and non-zero. `RAGE` → AGER because the abstract says
"receptor for advanced glycation end products", which overlaps AGER's naming
and not MOK's. No pair is written down anywhere.

Source trust is tiered, because breadth costs precision:

| tier | accepted |
|---|---|
| HGNC, single candidate | always |
| HGNC, several candidates | only if the abstract picks a unique winner |
| NCBI `gene_info` synonyms (`--ncbi_gene_info`) | only if the abstract picks a unique winner |

NCBI synonyms are broader than HGNC's and noisier — `FSH` is listed as a synonym
of *BRD2* — so they are never trusted on their own. Adding them as a flat union
without the abstract check makes things worse, not better.

**Measured** against the class-B papers from §3B — the 24 papers where the model
found the right experiment and wrote an identifier gold did not match — each
change added cumulatively:

| configuration | B papers recovered | FN rows |
|---|---|---|
| mapper as it was (`alias_symbol` + `prev_symbol`, no locus filter) | 0 / 24 | 0 / 32 |
| + locus filter | 2 / 24 | 2 / 32 |
| + `name` / `alias_name` / `prev_name` columns | 3 / 24 | 3 / 32 |
| + R6 context disambiguation | 7 / 24 | 8 / 32 |
| + R6 with NCBI synonyms | **10 / 24** | **12 / 32** |

R6 is doing most of the work, and it is the part that needs no list. The
starting 0/24 is the point worth keeping in view: the mapper as shipped could
not recover a single one of these, which is why v6's recall fell even though the
model's behaviour improved.

Easy cases are untouched (PPARG, FOXO3, ADAMTS5, COL2A1, SOX9, IL33, SMAD3 all
still resolve to themselves). The 14 unrecovered B papers are the real model
errors itemised in §3B, not normalisation failures — except two, where the
normaliser resolves to the *wrong* gene (`FSH`→BRD2 on a coincidental word
overlap, `PERF`→FABP9). Both come from the NCBI tier, which is the row of the
table to drop first if precision suffers.

R6 needs the abstracts, which are not in this working copy; they are re-fetchable
from PubMed E-utilities as the v5 analysis did. Without `--abstracts` the script
falls back to the model's own `evidence_snippet` text, which needs no new input
but is much thinner — on a ~40-word window of the same papers, 7/24 rather than
10/24. **Run it with and without `--abstracts` and report both**; the gap is the
value of context disambiguation, measured rather than assumed.

Also fixed: with an absolute `--pred_dirs`, `os.path.join` discarded `--out_root`
and the normalised files overwrote the input predictions.

## 9. Overfitting audit — this is a dev set

267 papers used for both development and evaluation. Every rule written by
reading an error table is a fit to that table. Measuring it: what fraction of
gold observation rows involve a gene whose symbol appears literally in the
prompt text?

| Prompt | gold genes named | % of gold rows |
|---|---|---|
| v3 | 3 / 182 | 1.8% |
| v5 | 10 / 182 | 7.4% |
| v6 full | 29 / 182 | 24.6% |
| v6 lite | 27 / 182 | 23.5% |
| **v7 full** | **24 / 182** | **21.4%** |
| **v7 lite** | **22 / 182** | **20.4%** |

The trend from v3 to v6 is the danger: each revision reads the error table and
writes more of it into the prompt. v7 reverses it slightly, and the deliberate
rule is that **anything that would be a lookup table belongs in the normaliser,
where it can be derived from a public resource and ablated** — not in prose the
model memorises.

The 24 gold genes still named in v7 are inside worked examples, or in the X2
readout list (MMP13, IL6, TNF, SOX9, RUNX2, ADAMTS5 — named as things that are
*sometimes* readouts, which injects no answer). Examples 1–5 reuse the same
dev-derived abstracts as v6, so the v6→v7 comparison stays like-for-like.
Example 6 uses a synthetic `LIGX–RECY` axis so the ligand/receptor rule teaches
the pattern rather than a specific answer.

**What this means for the numbers.** Any score on these 267 papers is an
optimistic estimate:

- **Hold out a test split.** The honest experiment is to fit on a subset and
  report on papers never used for error analysis. Nothing in v3→v7 has been
  validated this way, so the whole progression (0.524 → 0.802) is a
  development-set curve.
- **Treat the exclusion gate as the most trustworthy result.** X1–X8 are
  categorical rules about study design (cell therapy, CIA, pain-only) that name
  no dev gene and were independently validated on Qwen under v3.
- **The normaliser changes are the most trustworthy of the recall-side fixes**,
  because (1)–(3) use only public reference data and R6 uses only the paper's own
  words. They are also verifiable without running any model: re-normalise the
  existing v6 predictions and the gain should appear immediately.

## 10. Suggested run

```bash
python build_v5_dataset.py --like_dataset data/eval_v3_dataset \
  --system_file Prompts_v7/system_prompt.txt \
  --user_file   Prompts_v7/user_prompt.txt \
  --out data/eval_v7full_dataset      # and Prompts_v7_lite -> eval_v7lite_dataset

sbatch run_magi_v7full.sh   # also run_magi_v7lite.sh, run_q8b_v7{full,lite}.sh

# baseline normalisation
python normalise_genes.py --pred_dirs results/magi_think_v7full
# with context disambiguation; report both, the gap is R6's contribution
python normalise_genes.py --pred_dirs results/magi_think_v7full \
  --ncbi_gene_info ref/Homo_sapiens.gene_info.gz \
  --abstracts data/abstracts.jsonl --out_root results_norm_r6

python score_v2.py --pred_dir results_norm/magi_think_v7full
python make_table.py --pred_dir results_norm/magi_think_v7full \
  --out results/magistral_v7full_table.csv
```

What to check, in order of how much it would change the conclusion:

1. **Re-normalise the v6 predictions first.** The §8 changes are deterministic,
   so if the prediction dirs can be recovered the recall gain is confirmable
   before any inference runs. Do this before spending GPU time.
2. **Did precision hold at ~0.79?** R6 is the only change that can add false
   positives, by resolving an alias the paper did not mean. Compare against the
   run without `--abstracts`.
3. **Is `Spontaneous` gone from the output?** If it still appears, the closed
   vocabulary is not being respected and the induction gain will not materialise.
4. **Report induction accuracy from `score_v2.py`, not `make_table.py`**, until
   §4 is fixed — or quote both and say which is which.
5. **Run ≥2 seeds before reporting any delta under ~0.03 F1.**
