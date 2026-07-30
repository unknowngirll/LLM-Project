# Error analysis — OA extraction prompts on the 267-paper dev set

Part 1: Magistral-Small-2509 / prompt v5. Part 6: cross-model check against
Qwen3.6-27B and Qwen3-8B / prompt v3, and the pan-model prompt design.

Sources: `Prompts_v5/`, `results/magistral_v5_table.csv`,
`reasoning_traces/magistral_thinking_v5_267.txt`, abstracts re-fetched from
PubMed E-utilities. Per-row classification written to
`results/magistral_v5_error_modes.csv`.

Baseline (HGNC-normalised, matches `RESULTS_magistral.md`):
TP 178 / FP 81 / FN 33 → P 0.687, R 0.844, **F1 0.757**.
Attribute accuracy on matched pairs: induction 0.792, outcome 0.938, species 0.978.

The headline finding is that **precision, not recall, is the bottleneck, and the
single largest cause of both FP and FN is the `target` normalisation step — not
comprehension.** In the traces the model repeatedly identifies the right molecule
and then writes the wrong symbol into `target`.

---

## 1. Error taxonomy (100 FP rows, 42 FN rows)

| Class | FP rows | FN rows | What it is |
|---|---|---|---|
| **A — eligibility** | 47 | – | Paper has zero gold observations; model extracted anyway |
| **B — naming / entity** | 38 | 37 | Right paper, right experiment, wrong identifier ⇒ paired FP+FN |
| **C — extra gene** | 15 | – | All gold genes found, plus a spurious secondary molecule |
| **D — pure miss** | – | 5 | Gene genuinely absent from output |

Class B is the important one: **37 of 42 FN rows are accompanied by an FP in the
same paper.** These are not recall failures. The model found the experiment and
then mislabelled the molecule.

### 1A. Eligibility errors (47 FP rows across 31 papers)

Verified against the fetched abstracts:

| Sub-class | Papers | Example |
|---|---|---|
| Non-gene perturbagen | 19 | 27845067 chondroitin/glucosamine → `CHONDROITINSULFATE`, `GLUCOSAMINESULFATE`; 27703516 → `SHIKONIN`; 33880054 hydrogen gas → `H2`; 34490639 → `CISSUSQUADRANGULARIS`; 29039501 isoimperatorin → `NOTSTATED` |
| Cell / gene-therapy vehicle | 3 | 19404941 MDSCs expressing sFlt-1+BMP-4 → `FLT1`,`BMP4`; 31164994 adipose-derived stem cells → `NFKB1`,`AGER`,`MMP1`,`MMP13` |
| Downstream readout as target | — (overlaps) | 31164994, 29766025: molecules that were only *measured* emitted as perturbations |
| Wrong disease | 5 | 33408335, 18501644 collagen-induced arthritis (RA); 23666827 arthritis; 34490639 osteoporosis |
| Wrong structure | 1 | 33499145 intervertebral disc degeneration |
| Pain-only endpoint | 4 | 34396019 (abstract states *"Trpv4 gene deletion did not suppress the development of osteoarthritis pathologically"*), 28835277, 19376109, 33946919 |
| In vitro perturbation credited to in vivo model | 4 | 31186141 METTL3 shRNA in ATDC5 cells; in vivo arm used cycloleucine/betaine |
| Descriptive / method paper, human trial | 5 | 15607881 imaging method; 29708818 human RCT |

A minority (e.g. 19293161, an anti-TNF scFv that does protect cartilage) are
OATargets annotation-convention exclusions rather than model errors — those are
irreducible from the abstract.

### 1B. Naming errors — the dominant failure

`target_raw` is almost always right; `target` is where it breaks. From the traces:

| PMID | target_raw (correct) | `target` emitted | gold |
|---|---|---|---|
| 33133598 | IL-33 | `IL1F9` → IL36G | IL33 |
| 32550912 | RSK-3 | `RPS6KA5` | RPS6KA2 |
| 28716756 | Alk5 | `ACVR1B` | TGFBR1 |
| 16087873 | Mig-6 | `MDFIC` | ERRFI1 |
| 29622035 | Jmjd3 | `KDM3B` | KDM6B |
| 26698846, 31841119 | PAR2 | `F2R` | F2RL1 |
| 29219023 | tenascin-C | `TNNC` → TNNC1 | TNC |
| 29323130 | OPTC | `OPTICIN` | OPTC |
| 22057346 | Cd59a | `CD59A` | CD59 |
| 34176242 | FSH | `FSH` | FSHB |
| 30287418 / 30731321 / 34102226 | miR-181a-5p / miR-10a-5p / miR-892b | `MIR-181` / `MIR-10` / `MIR-892` | MIR-181A / MIR-10A / MIR-892B |
| 31653858 | tankyrase | `TANKYRASE` | TNKS + TNKS2 |
| 35061535 | ERAD | `ERAD` | SEL1L |
| 29524442 | PH797804 | `PH797804` | MAPK14 |

Four mechanisms:

1. **Overconfident alias→symbol recall.** v5 STEP 3 rule 2 says *"if you are NOT
   confident, output the raw name"*, but the model never judges itself
   unconfident. 33133598 is the clearest case: the reasoning trace says "IL-33"
   correctly five times, then writes `IL1F9`. Aliases carrying a family
   number/letter (RSK-**3**, ALK-**5**, PAR-**2**, JMJD-**3**) are where it
   picks the wrong sibling.
2. **The miRNA rule is actively harmful.** v5 says strip `-5p`/`-3p`; the model
   strips the family letter with it. Note `normalise_genes.py`'s `MIRNA` regex
   *keeps* the letter — had the model emitted `miR-10a-5p` verbatim, the
   downstream mapper would have produced `MIR-10A` correctly. The prompt
   pre-destroys information the pipeline could have recovered.
3. **Non-gene tokens in `target`**: pathways (`ERAD`), family names
   (`TANKYRASE`), drugs (`PH797804`, `BORTEZOMIB`, `3MA`), phenotypes
   (`MASTCELLDEFICIENCY`), and one literal `NOTSTATED`.
4. **Ligand/receptor substitution**: 34136574 (drug blocks CXCR4, gold annotates
   ligand CXCL12) and 37144868 (`GAS6` emitted, gold `AXL`).

Recoverability of the 75 B-class rows: **43 recoverable** by a naming-rule fix
alone, 6 need a drug→target rule, 6 a family-expansion rule, 3 a pathway ban,
4 ligand/receptor, 13 not recoverable from the abstract.

Because the model has already written a confidently wrong symbol, the existing
HGNC post-processing can only add +0.01 F1 — the correct `target_raw` is
discarded before it reaches the mapper.

### 1C. Extra genes (15 FP rows)

Secondary molecules extracted alongside the correct targets: `ADAMTS4`
(17968948), `SIRT1` (28627522), `HMGA2` (36026443), `PDK1` (37344157), `SDC1`
(32377874), `TGM2` (31511053), `FGFR1` (31901095), plus bare compounds `3MA`,
`BORTEZOMIB`. These are mechanism partners or assay readouts, not perturbations.

---

## 2. Attribute errors are mostly one bug: under-splitting

Induction accuracy is 0.792 (43 wrong, 36 abstain). But **32 of the 43 wrong
rows come from genes where gold has 2–5 model rows and the model emitted fewer
distinct observations**; `make_table.py` then re-uses the single prediction
against every gold row. Same for outcome: **12 of 15 wrong rows**.

41 genes are affected. Worst cases:

- 29444976 / 31980519 (FoxO1/3/4): gold = 3 genes × 3 models (ageing, surgical,
  treadmill). Model emitted 1 observation per gene, `Spontaneous`. The abstract
  says *"led to spontaneous cartilage degradation and increased OA severity in a
  surgical model or treadmill running"* — all three models are in one sentence.
- 31424112 (CCL2/CCR2), 27965260, 33109602, 35608871, 29247173: same pattern.

So the real induction error rate on single-model genes is 11/207 — the enum and
crosswalk are fine. **The fix is splitting, not relabelling.** Two genuine enum
gaps remain: treadmill/exercise → the model says `Spontaneous` or `Chemical`
(gold `Exercise`, crosswalk expects `Mechanical`), and `Ageing` → `Surgical`
where a KO also had surgery.

### The "Not stated" abstain bug

36 induction abstains (30 where gold is Surgical) and 11 species abstains. The
trace for 34463587 is explicit:

> *"oa_induction: Not stated (but since it's a DMM model as per methods, but not
> explicitly stated in results, we'll put 'Not stated')"*

The abstract's Methods sentence literally reads *"Destabilization of the medial
meniscus (DMM) surgery was used to construct the OA models"*. The model is
scoping field extraction to the sentence carrying the outcome. Same cause for
36261443 (title: *"…during surgically induced osteoarthritis"*, abstract:
*"following surgical induction"* → emitted `Not stated`). A secondary cause is
that v5's `Surgical` definition lists only *"DMM, ACLT, meniscectomy, groove"*,
with no catch-all for generic "surgically induced OA".

Species abstains (27830706, 29736207, 30944169, 33781898, 38389178, 30261507,
26837060) are the same section-scoping issue plus missing strain→species cues.

### Species confusion in multi-species papers

5 wrong (17623656 Rabbit→Rats, 20506144 Mouse→Rats, 22484689 Mouse→Rabbits,
23233270 Rat→Mice, 31108241 Mouse→Rats). All are papers using two species where
the model collapsed to one — again under-splitting.

---

## 3. Format compliance

18/267 outputs (6.7%) open with a ```json fence despite RULE 4. `score_v2.py`'s
`\{.*\}` regex recovers all of them, so parse failures are 0 — but it is a
latent failure and worth closing.

---

## 4. What v6 changes, and expected effect

`Prompts_v6/` implements:

1. **STEP 1b hard exclusions X1–X8** — non-gene perturbagens (nutraceuticals,
   natural products, probiotics, diets, cell therapy), downstream readouts,
   wrong disease (CIA/RA), wrong structure (IVD), pain-only endpoints, in-vitro-
   only perturbations, descriptive papers, human trials. Targets class A.
2. **Inverted STEP 3 default** — the safe answer is the *cleaned raw name*, not a
   recalled symbol. Explicit "do not map" list for family-numbered aliases
   (RSK-3, Alk5, PAR2, Mig-6, Jmjd3, IL-33, tenascin-C), mouse-ortholog suffix
   stripping (Cd59a→CD59), family expansion (tankyrase→TNKS+TNKS2), pathway ban,
   drug→named-target rule, ligand/receptor rule. New optional field
   `target_is_official_symbol` so the HGNC mapper knows what to resolve.
   Targets class B.
3. **Rewritten miRNA rule** — keep the family letter, strip only the arm suffix,
   with four worked examples. Targets 3 FN+3 FP directly and lets
   `normalise_genes.py` do its job.
4. **STEP 2 rewritten as "enumerate models first, then cross with genes"**, with
   a 2-gene × 3-model worked example (Example 3). Targets the 32 induction and
   12 outcome errors from under-splitting.
5. **RULE 4 "use the whole abstract"** — a field stated in the Methods sentence
   applies to every observation; `Not stated` means never stated anywhere.
   Strain→species cues listed. `Surgical` gets an explicit catch-all for
   "surgically induced OA". Targets the 36+11 abstains.
6. **RULE 6 explicitly bans markdown fences.**

Projected effect, assuming the naming fix lands on the 15 recoverable papers and
the eligibility gate removes 70% of class A:

| Scenario | P | R | F1 |
|---|---|---|---|
| v5 baseline | 0.687 | 0.844 | 0.757 |
| + naming fix only | 0.750 | 0.924 | 0.828 |
| + eligibility gate only | 0.764 | 0.844 | 0.802 |
| both | 0.833 | 0.924 | 0.876 |
| both + no extra genes | 0.867 | 0.924 | 0.894 |

These are upper bounds on the addressable error, not predictions — the model has
to actually follow the rules, and v6 is a longer prompt, which carries its own
instruction-following risk.

## 5. Suggested run

**Context budget — must change before running.** v6 is 32.7 kB vs v5's 15.9 kB
(≈8.2k vs ≈4.0k prompt tokens). `run_magi_think_v5.sh` uses
`--max_seq_length 16000 --max_new_tokens 12000`; v5 was already marginal
(4.5k input + 12k generated ≈ 16.5k) and v6 would overflow. Raise
`--max_seq_length` to 24000, or trim v6 (Example 3 is the most verbose block and
could be cut to 2 models × 2 genes).

```bash
python build_v5_dataset.py --like_dataset data/eval_v3_dataset \
  --system_file Prompts_v6/system_prompt.txt \
  --user_file   Prompts_v6/user_prompt.txt \
  --out data/eval_v6_dataset

python infer_magistral_think.py --model models/Magistral-Small-2509 --load_in_4bit \
  --dataset data/eval_v6_dataset --split validation \
  --max_new_tokens 12000 --max_seq_length 24000 \
  --temperature 0.7 --top_p 0.95 --out_dir results/magi_think_v6

python normalise_genes.py --pred_dirs results/magi_think_v6
python score_v2.py --pred_dir results_norm/magi_think_v6
python make_table.py --pred_dir results_norm/magi_think_v6 --out results/magistral_v6_table.csv
```

Two things worth checking in the v6 output before trusting the score:

- **Ablate the exclusion list separately from the naming rules.** They target
  disjoint error classes (A vs B), so running v6 as one change makes it
  impossible to attribute a gain — and X1–X8 is the part most likely to
  over-fire and cost recall on legitimate pharmacological entries (CTSK
  inhibitor, FGF18, A2M, AMD3100 are all gold TPs).
- **Check `target_is_official_symbol=false` rows actually resolve.** The gain
  depends on `normalise_genes.py` R4 finding the alias in the HGNC table. PAR2,
  ALK5, MIG6, RSK3, JMJD3 are all unambiguous HGNC aliases; TENASCINC and
  OPTICIN may not be, and would need adding to a small manual alias file.

Note the v5→v6 comparison inherits the caveat already in `RESULTS_magistral.md`:
sampling is `temperature=0.7, top_p=0.95`, so a single run's difference is not
reproducible. Repeat seeds before reporting a delta of a few points.

---

# 6. Cross-model check: Qwen3.6-27B and Qwen3-8B under prompt v3

The two Qwen thinking traces run **prompt v3**, so v3-vs-v5 is a natural
experiment on the two prompt sections that matter most: v3 has explicit
exclusion rules and no gene-normalisation instructions; v5 has the reverse.

Predictions were parsed straight out of the trace files and scored against gold
reconstructed from the union of all `results/*_table.csv` (175 positive papers,
287 observations — reproduces `comparison_all.csv` to ±0.003):

| Run | Prompt | TP | FP | FN | TN | P | R | F1 |
|---|---|---|---|---|---|---|---|---|
| Qwen3.6-27B thinking | v3 | 115 | 111 | 98 | 80 | 0.509 | 0.540 | 0.524 |
| Qwen3-8B thinking | v3 | 124 | 80 | 89 | 83 | 0.608 | 0.582 | 0.595 |
| Magistral-Small | v5 | 175 | 83 | 38 | 61 | 0.678 | 0.822 | 0.743 |

## 6.1 v3's explicit exclusions work, and v5 threw them away

Over-extraction on the 92 true-negative papers:

| Run | Papers over-extracted |
|---|---|
| Qwen3.6-27B (v3) | **12 / 92** |
| Qwen3-8B (v3) | **9 / 92** |
| Magistral (v5) | **31 / 92** |

v3 RULE 4 named three exclusions — inflammatory arthritis models, pain-only
studies, herbal/traditional medicine. v5 replaced that with *"be inclusive, not
strict"* and the eligibility error class tripled. The 27B trace for 32634440
cites the rules by number:

> *"Rule 4A says: 'Inflammatory arthritis models (e.g., collagen-induced,
> antibody-induced, IL-1b, TNF)' → IL-1b induced OA is explicitly excluded. Also,
> Rule 4C … Tripterygium wilfordii is a traditional Chinese medicine."*

Papers both Qwens rejected and Magistral did not: 18501644 and 33408335 (CIA),
29766025 and 32634440 and 33155655 (natural products), 27845067 and 29618773
(nutraceuticals), 34490639, 23666827, 26992380, 19376109, 29708818.

**Two v3 rules I had dropped from v6 and have now restored:**

- **IL-1β-induced and TNF-induced joint models are exclusions**, not "Chemical"
  induction. Gold's induction vocabulary is only `Surgical, Ageing, Protease,
  MIA, Exercise, High Fat Diet` — there is no gold row for any other chemical
  model, so emitting one is always an FP.
- **"Collagenase-induced" IS valid OA; "collagen-induced" (CIA) IS NOT.** A
  three-letter distinction that decides whether the paper is in scope. v6 now
  carries this as a callout inside X3.

Residual eligibility errors that v3 did *not* catch and v6's X1/X4/X5/X6 target:
33499145 (intervertebral disc — both Qwens emit `Panx3`), 34396019 (TRPV4 pain
paper — both Qwens emit `Trpv4`), 31186141 (METTL3 silenced only in ATDC5 cells
— all three models), 19404941 (MDSC cell therapy — all three), and the 27B still
emitting `Ascorbic acid`, `Diacerein`, `Shikonin`, `S-DCs`, `H2`,
`Lactobacillus rhamnosus` as targets.

## 6.2 The naming finding is confirmed from the opposite direction

v3 has no `target_raw`, no formatting rules, and says only *"official gene/protein
symbol perturbed"* — so the models emit **the alias as written**. That is why
HGNC post-processing is worth **+0.16 to +0.17 F1** on the Qwen runs
(`RESULTS_instruct.md`) but only **+0.01** on Magistral v5.

Head to head on the same papers:

| PMID | abstract says | Qwen 27B (v3) | Magistral (v5) | gold |
|---|---|---|---|---|
| 16087873 | Mig-6 | `mig-6` ✓ resolves | `MDFIC` ✗ | ERRFI1 |
| 28716756 | Alk5 | `alk5` ✓ | `ACVR1B` ✗ | TGFBR1 |
| 26698846 | PAR2 | `par2` ✓ | `F2R` ✗ | F2RL1 |
| 29622035 | Jmjd3 | `jmjd3` ✓ | `KDM3B` ✗ | KDM6B |
| 33133598 | IL-33 | `il-33` ✓ | `IL1F9` ✗ | IL33 |
| 30731321 | miR-10a-5p | `mir-10a-5p` ✓ | `MIR-10` ✗ | MIR-10A |

Every flagship v6 naming rule is validated by 27B behaviour the pipeline already
recovers: it emits `sclerostin`, `RAGE`, `OPG`, `p21`, `LOX-1`, `CatK`, `Ob-Rb`,
`XOR`, `galectin-3`, `p38 MAPK`, `COX2`, `IL1Ra` — all unambiguous HGNC aliases.
Of the 27B's 91 FN-paired FPs, only 9 are trivial formatting (`adamts-5`,
`il-6`); the rest are aliases the HGNC table maps.

So the two prompts fail at opposite ends: **v3 under-normalises (recoverable),
v5 over-normalises (unrecoverable)**. v6 aims at the middle — emit the cleaned
alias, flag certainty, let the deterministic table do the lookup — and v6 now
adds rule 5b saying explicitly that emitting a well-known alias is *correct*
behaviour, because that is what the best-performing model already does.

Shared naming failures across all three models, confirming they are prompt
problems rather than model quirks: pathways as targets (`autophagy` in 27B,
`ERAD` in Magistral), drug names as targets (`bortezomib` in both), nutraceutical
names (`glcn.hcl`, `mucop` in both), and the spurious `ADAMTS4` on 17968948.

## 6.3 Under-splitting is universal

Fraction of gold observations covered on genes the model *did* find:

| Run | matched genes | gold obs | covered | coverage | genes under-split |
|---|---|---|---|---|---|
| Qwen3.6-27B | 115 | 164 | 139 | 0.848 | 16 |
| Qwen3-8B | 124 | 178 | 154 | 0.865 | 19 |
| Magistral v5 | 175 | 237 | 212 | 0.895 | 18 |

All three collapse multi-model experiments at the same rate, and all three abstain
on induction at a similar rate (23 / 25 / 31). This is a prompt gap, not a model
gap — v6 STEP 2 ("enumerate models first, then cross with genes") is the highest-
confidence pan-model change in the whole revision.

The *reason* for abstaining differs by model, so v6 needs both fixes:

- **Magistral** section-scopes — it sees DMM in the Methods sentence and still
  writes `Not stated` because the result sentence does not repeat it (→ v6 RULE 4).
- **Qwen** abstains on vocabulary mismatch — *"'Not stated' if it's not
  explicitly one of the listed ones"*, and *"abstract says 'rodent', not specific
  to mice/rats"* (→ v6's new CLOSED VOCABULARIES paragraph, the "COMMIT TO A
  VALUE" block under `oa_induction`, and the strain→species table).

Since **no gold row has induction "Not stated"**, every abstain is a guaranteed
loss on that metric. v6 now says so directly.

## 6.4 Prompt size is the pan-model constraint

| Prompt | chars | ≈tokens |
|---|---|---|
| v3 | 10,922 | 2,950 |
| v5 | 15,868 | 4,290 |
| **v6** | 35,737 | **9,660** |
| **v6_lite** | 24,078 | **6,510** |

Reasoning length also varies sharply: median reasoning is 9,210 chars for the
27B, 3,281 for Magistral, 2,340 for the 8B (27B p90 = 15,400). And
`comparison_all.csv` shows the small models degenerate — Qwen3.5-4B thinking
logged 175 looped generations and 123 parse failures.

Recommendation:

- **`Prompts_v6/`** — full version, for Magistral-Small, Qwen3.6-27B and larger.
  Needs `--max_seq_length 24000`.
- **`Prompts_v6_lite/`** — same rules, 4 fewer worked examples and compact
  single-line JSON, ~6.5k tokens. Use for Qwen3-8B, Qwen3.5-4B, Llama-3.1-8B.
  Both keep the identical STEP 3 naming rules and X1–X8 exclusions, so a
  v6/v6_lite comparison also measures how much the extra examples buy.

Format compliance is model-specific and worth watching: 0/267 fenced outputs from
both Qwen models under v3, 18/267 from Magistral under v5. `score_v2.py`'s regex
recovers fences, so this costs nothing today — but v6 RULE 6 states it explicitly.

## 6.5 Suggested pan-model ablation

Run each model on v3 / v5 / v6 / v6_lite over the same 267 papers, then score with
and without `normalise_genes.py`. The informative contrasts are:

1. **v5 → v6 on Magistral** — does restoring exclusions plus de-guessing symbols
   recover the predicted precision?
2. **v3 → v6 on Qwen3.6-27B** — does adding STEP 2 splitting and the target rules
   help a model whose eligibility behaviour was already good, or does the longer
   prompt hurt it?
3. **hgnc-gain as a diagnostic** — if v6 is working, the gap between `none` and
   `hgnc` should *shrink* on the Qwen models (the model now emits cleaner tokens)
   while `hgnc` F1 itself rises. If `none` rises but `hgnc` does not, the model has
   started guessing symbols again and STEP 3 rule 3 needs strengthening.
4. **v6 vs v6_lite per model** — isolates worked-example cost/benefit against
   context-length degradation.

Reconstruction and scoring scripts for the trace files are throwaway; the
reusable path is `make_table.py` + `score_v2.py` against
`data/gold_answers.jsonl`, which is not in this working copy.
