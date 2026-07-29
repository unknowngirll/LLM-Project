# Magistral-Small-2509

267-paper OATargets evaluation set (175 positives + 92 true negatives), scored with `score_v2.py`.

Reasoning mode is triggered by the model's own `SYSTEM_PROMPT.txt`, which requests a `[THINK]` block; Magistral ignores the `enable_thinking` flag used by the Qwen models. Markers are rewritten to `<think>` on save so the scorer can separate reasoning from the JSON answer.

| Mode | Prompt | Normalisation | F1 | P | R | TP | FP | FN | TN | Induction | Outcome | Species | Parse fail |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Instruct | v3 | none | **0.532** | 0.520 | 0.545 | 115 | 106 | 96 | 76 | 0.836 | 0.932 | 0.980 | 0 |
| Thinking | v5 | none | **0.746** | 0.678 | 0.829 | 175 | 83 | 36 | 61 | 0.877 | 0.950 | 0.976 | 0 |
| Thinking | v5 | HGNC | **0.757** | 0.687 | 0.844 | 178 | 81 | 33 | 61 | 0.874 | 0.951 | 0.977 | 0 |

## Notes

- The instruct run used v3 prompts and the thinking run used v5, so the two differ in prompt as well as mode; the comparison is not a clean pair.
- Normalisation gains little here (~0.01) because the model already emits official symbols under v5 — only 12 HGNC alias substitutions were needed across all 267 papers.
- Getting this model to run required tokenizer files from the unsloth mirror; the official Mistral repository ships only the raw `tekken.json`, so token IDs never matched the model vocabulary and generation failed with a CUDA device-side assert.

Full reasoning traces: [`reasoning_traces/magistral_thinking_v5_267.txt`](reasoning_traces/magistral_thinking_v5_267.txt)

## Per-observation table

Gene-level detail for every paper — model prediction, OATargets gold entry, and
whether each row is a true positive, false positive, or false negative:
[`results/magistral_v5_table.csv`](results/magistral_v5_table.csv)
