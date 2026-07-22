# Repository structure

## Data preparation
prepare_gold.py       build gold_answers.jsonl from OATargets
add_negatives.py      add the 92 true-negative papers
build_hf_dataset.py   original dataset builder (shuffles with seed=42)
build_v3_eval.py      267-paper eval set, v3 prompts
build_v4_eval.py      267-paper eval set, v4 prompts (rejected)
build_v5_dataset.py   267-paper eval set, v5 prompts; no reshuffle

## Inference
infer_unsloth.py        unsloth backend; enable_thinking=False -> instruct runs
infer_think_simple.py   CURRENT thinking script; do_sample=True, temp=0.6
infer_think_script.py   SUPERSEDED; greedy decoding caused reasoning loops
infer_think.py          intermediate version
infer.py, run_model.py  early versions
infer_magistral.py      Magistral; unresolved CUDA device-side assert

## Scoring
score_v2.py         CURRENT scorer; fixes align_paper pairing bug
score.py            original, kept unchanged
normalise_genes.py  HGNC gene-symbol normalisation of predictions
normalise_gold.py   same rules applied to gold (symmetric matching)

## Analysis
make_table.py    per-observation CSV for error analysis
analyze_fn.py    false-negative analysis
compare_all.py   score every result directory
compare_pairs.py thinking vs instruct, paired by model family

## Slurm jobs
run_s_q8b.sh    Qwen3-8B    thinking, v3   (complete, 267/267)
run_s_q36.sh    Qwen3.6-27B thinking, v3   (complete, 267/267)
run_s_q35.sh    Qwen3.5-4B  thinking, v3   (failed: reasoning loop)
run_n_q8b.sh    Qwen3-8B    instruct, v3
run_n_q35.sh    Qwen3.5-4B  instruct, v3
run_llama31.sh  Llama-3.1-8B instruct, v3
run_v5_q8b.sh   Qwen3-8B    thinking, v5 prompts
run_qwen36_*.sh earlier 27B runs; note run_qwen36_think.sh called
                infer_unsloth.py, so thinking was never actually enabled
