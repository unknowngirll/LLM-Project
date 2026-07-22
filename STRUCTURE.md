# Repository Structure

Scripts for benchmarking open-weight LLMs on structured data extraction
from osteoarthritis abstracts, scored against the OATargets database.

All scripts live in the repository root and are invoked with relative
paths from Slurm jobs (`python infer_unsloth.py ...`).

---

## Data preparation

| Script | Purpose |
|---|---|
| `prepare_gold.py` | Build `gold_answers.jsonl` from OATargets |
| `add_negatives.py` | Add the 92 true-negative papers |
| `build_hf_dataset.py` | Original dataset builder (shuffles with `seed=42`) |
| `build_v3_eval.py` | 267-paper evaluation set, v3 prompts |
| `build_v4_eval.py` | 267-paper evaluation set, v4 prompts (rejected) |
| `build_v5_dataset.py` | 267-paper evaluation set, v5 prompts; reuses the v3 PMID list, no reshuffle |

---

## Inference

| Script | Purpose | Status |
|---|---|---|
| `infer_unsloth.py` | unsloth backend; `enable_thinking=False` | **Current** — instruct runs |
| `infer_think_simple.py` | Thinking mode with `do_sample=True`, `temp=0.6`, `top_p=0.95`, `top_k=20` | **Current** — thinking runs |
| `infer_think_script.py` | Thinking mode with greedy decoding | Superseded — caused reasoning loops |
| `infer_think.py` | Intermediate thinking version | Superseded |
| `infer.py` | Early transformers version | Superseded |
| `run_model.py` | First script written for the project | Superseded |
| `infer_magistral.py` | Magistral with a hand-written chat template | Unresolved — CUDA device-side assert |

### Note on thinking mode

`infer_unsloth.py` hard-codes `enable_thinking=False`. Any job calling it
runs without reasoning regardless of the job name — this is why
`run_qwen36_think.sh` never actually enabled thinking.

Greedy decoding (`do_sample=False`) makes Qwen3 loop indefinitely in
thinking mode. `infer_think_simple.py` fixes this with Qwen's recommended
sampling parameters. Note that generation is therefore **not
deterministic**.

---

## Scoring

| Script | Purpose |
|---|---|
| `score_v2.py` | **Current scorer.** Fixes the `align_paper` pairing bug |
| `score.py` | Original scorer, kept unchanged for reference |
| `score_v4.py` | Variant used for the v4 prompt experiment |
| `normalise_genes.py` | HGNC gene-symbol normalisation of model predictions |
| `normalise_gold.py` | Same rules applied to gold, for symmetric matching |
| `schema_crosswalk_v4.py` | Maps prompt vocabulary to gold vocabulary |

### The align_paper fix

The original scorer paired each gold observation with the *first*
prediction matching only on `manipulation_direction`. When one paper had
two observations with the same direction, it selected the wrong one.

`score_v2.py` scores direction, induction and outcome together and uses
each prediction once. Induction accuracy rose from 0.735 to 0.853 and
outcome from 0.905 to 0.945, with TP/FP/FN/TN unchanged.

### Gene normalisation

Models output the gene name as written in the abstract; OATargets uses
official HGNC symbols, so correct biology scored as a miss
(`SDF-1` vs `CXCL12`, `Rip3` vs `RIPK3`).

Four rules, applied in order:

1. **Split** — multi-gene targets become one observation per gene
2. **miRNA** — strip species prefixes and arm suffixes (`mmu-miR-204-5p` → `MIR-204`)
3. **Format** — uppercase, remove Greek letters and punctuation
4. **HGNC** — map aliases to official symbols (unambiguous mappings only)

The mapping comes from the official HGNC file, never from the gold
answers. Both raw and normalised scores are reported.

---

## Analysis

| Script | Purpose |
|---|---|
| `make_table.py` | Per-observation CSV (TP/FP/FN rows) for error analysis |
| `make_table_v4.py` | Variant for the v4 experiment |
| `analyze_fn.py` | False-negative analysis |
| `compare_all.py` | Score every result directory into one table |
| `compare_pairs.py` | Thinking vs instruct, paired by model family |

---

## Slurm jobs

### Current runs

| Script | Model | Mode | Prompt | Outcome |
|---|---|---|---|---|
| `run_s_q8b.sh` | Qwen3-8B | Thinking | v3 | Complete, 267/267 |
| `run_s_q36.sh` | Qwen3.6-27B | Thinking | v3 | Complete, 267/267 |
| `run_s_q35.sh` | Qwen3.5-4B | Thinking | v3 | Failed — reasoning loop |
| `run_n_q8b.sh` | Qwen3-8B | Instruct | v3 | — |
| `run_n_q35.sh` | Qwen3.5-4B | Instruct | v3 | — |
| `run_llama31.sh` | Llama-3.1-8B | Instruct | v3 | — |
| `run_v5_q8b.sh` | Qwen3-8B | Thinking | v5 | — |

### Earlier runs

| Script | Note |
|---|---|
| `run_qwen36_v3.sh`, `run_qwen36_v3_h100.sh` | 27B non-thinking, F1 = 0.592 |
| `run_qwen36_v4.sh` | v4 prompt experiment |
| `run_qwen36_full.sh` | Run on `negatives_dataset` |
| `run_qwen36_negatives.sh` | Negatives only |
| `run_qwen36_think.sh` | Named "think" but called `infer_unsloth.py` — thinking was never enabled |
| `run_q8b_think.sh`, `run_q35_think.sh` | Thinking with greedy decoding |
| `infer_dev*.sh` | v2 prompt runs on the 175-paper set |
| `run_magistral.sh` | Never ran successfully |
| `run_model.sh` | First job script |

### Test and download

`test_llama.sh` · `test_gemma4.sh` · `test_qwen36.sh` · `test_unsloth.sh` ·
`test_infer.sh` · `dl_magistral.sh` · `dl_magistral_fixed.sh`

---

## Prompts

| Directory | Status |
|---|---|
| `Prompts_v2/` | Used for the four smaller models on the 175-paper set |
| `Prompts_v3/` | Best baseline prompt — F1 0.592, TN 88 |
| `Prompts_v4/` | Rejected — F1 dropped to 0.558 |
| `Prompts_v5/` | Supervisor's revision: splits `target` into `target` + `target_raw` |

---

## Cluster notes

- Build Slurm scripts with `printf`, not heredoc — a pasted heredoc leaves a blank first line and sbatch rejects the file
- Write the python command on one line
- Verify with `head -1` and `wc -l` before submitting
- Do not set `--cpus-per-task` for GPU jobs
- Python logging is buffered; judge progress by counting output files
- `infer_*.py` skips existing files, so resubmitting resumes a timed-out job
- Models live in `~/scratch/models/`, symlinked as `models/`
- Always `export HF_HOME=~/scratch/hf_cache`
