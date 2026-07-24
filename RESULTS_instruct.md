# Gene normalisation comparison (instruct models)

All runs on the 267-paper evaluation set (175 positives + 92 true negatives), v3 prompts, non-thinking mode, scored with `score_v2.py`.

| Method | Description |
|---|---|
| `none` | Raw model output, no normalisation |
| `hgnc` | Deterministic HGNC alias mapping (`normalise_genes.py`), scored against normalised gold |
| `jamie` | Fuzzy matching over an NCBI gene database plus LLM adjudication (`jamie_normalise_adapted.py`) |

## F1 by normalisation method

| Model | none | hgnc | jamie |
|---|---|---|---|
| Qwen3-8B | 0.522 | 0.695 | 0.567 |
| Qwen3.5-4B | 0.451 | 0.647 | 0.514 |
| Llama-3.1-8B | 0.384 | 0.524 | 0.418 |
| Qwen3.6-27B | 0.592 | 0.754 | 0.640 |

## Full results

| Model | Norm | F1 | P | R | TP | FP | FN | TN | Induction | Outcome | Species | Parse fail |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Qwen3-8B | `none` | **0.522** | 0.544 | 0.502 | 106 | 89 | 105 | 78 | 0.798 | 0.953 | 0.993 | 0 |
| Qwen3-8B | `hgnc` | **0.695** | 0.723 | 0.668 | 141 | 54 | 70 | 78 | 0.821 | 0.958 | 0.994 | 0 |
| Qwen3-8B | `jamie` | **0.567** | 0.590 | 0.545 | 115 | 80 | 96 | 78 | 0.817 | 0.948 | 0.993 | 0 |
| Qwen3.5-4B | `none` | **0.451** | 0.456 | 0.445 | 94 | 112 | 117 | 79 | 0.858 | 0.932 | 0.991 | 2 |
| Qwen3.5-4B | `hgnc` | **0.647** | 0.655 | 0.640 | 135 | 71 | 76 | 79 | 0.865 | 0.952 | 0.981 | 2 |
| Qwen3.5-4B | `jamie` | **0.514** | 0.522 | 0.507 | 107 | 98 | 104 | 79 | 0.863 | 0.939 | 0.984 | 2 |
| Llama-3.1-8B | `none` | **0.384** | 0.300 | 0.531 | 112 | 261 | 99 | 27 | 0.802 | 0.921 | 0.971 | 1 |
| Llama-3.1-8B | `hgnc` | **0.524** | 0.410 | 0.725 | 153 | 220 | 58 | 27 | 0.800 | 0.923 | 0.967 | 1 |
| Llama-3.1-8B | `jamie` | **0.418** | 0.327 | 0.578 | 122 | 251 | 89 | 27 | 0.828 | 0.919 | 0.973 | 1 |
| Qwen3.6-27B | `none` | **0.592** | 0.592 | 0.592 | 125 | 86 | 86 | 88 | 0.853 | 0.945 | 0.975 | 0 |
| Qwen3.6-27B | `hgnc` | **0.754** | 0.754 | 0.754 | 159 | 52 | 52 | 88 | 0.855 | 0.941 | 0.975 | 0 |
| Qwen3.6-27B | `jamie` | **0.640** | 0.640 | 0.640 | 135 | 76 | 76 | 88 | 0.865 | 0.942 | 0.976 | 0 |
