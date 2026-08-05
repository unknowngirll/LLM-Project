# Model comparison — full results

All runs on the OATargets evaluation set (267 papers: 175 positives + 92 true negatives), scored with `score_v2.py`. Rows sorted by best F1.

Earlier v2 runs used a 175-paper positives-only set and are marked accordingly; their TN is 0 by construction and they are not directly comparable with the 267-paper rows.

## Headline: F1 under each normalisation condition

| Model | Params | Mode | Prompt | none | fuzzy+LLM | HGNC | cascade |
|---|---|---|---|---|---|---|---|
| Magistral-Small | 24B | Thinking | v6full | 0.729 | 0.771 | 0.796 | **0.838** |
| Qwen3-8B | 8B | Thinking | v3 | 0.598 | 0.646 | 0.761 | **0.810** |
| Gemma-4-12B | 12B | Thinking | v6full | 0.621 | 0.706 | 0.745 | **0.807** |
| Qwen3.6-27B | 27B | Instruct | v3 | 0.592 | 0.640 | 0.754 | **0.806** |
| Qwen3-8B | 8B | Thinking | v6lite | 0.625 | 0.695 | 0.739 | **0.799** |
| Qwen3.6-27B | 27B | Thinking | v3 | 0.526 | 0.604 | 0.728 | **0.792** |
| Qwen3-8B | 8B | Thinking | v5 | 0.677 | 0.731 | 0.753 | **0.789** |
| Magistral-Small | 24B | Thinking | v6lite | 0.700 | – | **0.786** | – |
| Qwen3-8B | 8B | Thinking | v6full | 0.642 | – | **0.760** | – |
| Magistral-Small | 24B | Thinking | v5 | 0.746 | 0.742 | **0.757** | **0.757** |
| Qwen3-8B | 8B | Thinking | v4 | 0.595 | – | **0.756** | – |
| Qwen3-8B | 8B | Thinking | v2 | 0.544 | – | **0.737** | – |
| Qwen3-8B | 8B | Instruct | v5 | 0.643 | – | **0.736** | – |
| Qwen3-4B-Thinking | 4B | Thinking | v2 | 0.544 | – | **0.731** | – |
| Magistral-Small | 24B | Instruct | v3 | 0.532 | 0.580 | 0.681 | **0.731** |
| Qwen3-8B | 8B | Thinking | v1 | 0.517 | – | **0.711** | – |
| Qwen3-8B | 8B | Instruct | v6full | 0.565 | – | **0.709** | – |
| Qwen3.5-4B | 4B | Instruct | v3 | 0.451 | 0.514 | 0.647 | **0.705** |
| Qwen3-8B | 8B | Instruct | v3 | 0.518 | – | **0.692** | – |
| Qwen3-8B | 8B | Instruct | v4 | 0.510 | – | **0.683** | – |
| Qwen3-8B | 8B | Instruct | v1 | 0.443 | – | **0.681** | – |
| Qwen3-8B | 8B | Instruct | v2 | 0.469 | – | **0.634** | – |
| Qwen3-4B-Instruct | 4B | Instruct | v2 | 0.422 | – | **0.593** | – |
| Llama-3.1-8B | 8B | Instruct | v3 | 0.384 | 0.418 | 0.524 | **0.568** |
| Qwen3-8B | 8B | Instruct | v6lite | 0.481 | – | **0.543** | – |

## Detail (HGNC-normalised scoring)

| Model | Mode | Prompt | F1 | P | R | TP | FP | FN | TN | Induction | Outcome | Species | Parse fail |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Magistral-Small | Thinking | v6full | 0.796 | 0.787 | 0.806 | 170 | 46 | 41 | 83 | 0.881 | 0.968 | 0.972 | 1 |
| Qwen3-8B | Thinking | v3 | 0.761 | 0.775 | 0.749 | 158 | 46 | 53 | 83 | 0.852 | 0.942 | 0.969 | 0 |
| Gemma-4-12B | Thinking | v6full | 0.745 | 0.742 | 0.749 | 158 | 55 | 53 | 90 | 0.868 | 0.942 | 0.985 | 1 |
| Qwen3.6-27B | Instruct | v3 | 0.754 | 0.754 | 0.754 | 159 | 52 | 52 | 88 | 0.855 | 0.941 | 0.975 | 0 |
| Qwen3-8B | Thinking | v6lite | 0.739 | 0.776 | 0.706 | 149 | 43 | 62 | 88 | 0.871 | 0.931 | 0.984 | 0 |
| Qwen3.6-27B | Thinking | v3 | 0.728 | 0.704 | 0.754 | 159 | 67 | 52 | 80 | 0.843 | 0.937 | 0.973 | 0 |
| Qwen3-8B | Thinking | v5 | 0.753 | 0.715 | 0.796 | 168 | 67 | 43 | 73 | 0.871 | 0.940 | 0.970 | 0 |
| Magistral-Small | Thinking | v6lite | 0.786 | 0.789 | 0.782 | 165 | 44 | 46 | 88 | 0.849 | 0.945 | 0.972 | 0 |
| Qwen3-8B | Thinking | v6full | 0.760 | 0.794 | 0.730 | 154 | 40 | 57 | 90 | 0.878 | 0.936 | 0.980 | 0 |
| Magistral-Small | Thinking | v5 | 0.757 | 0.687 | 0.844 | 178 | 81 | 33 | 61 | 0.874 | 0.951 | 0.977 | 0 |
| Qwen3-8B | Thinking | v4 | 0.756 | 0.779 | 0.735 | 155 | 44 | 56 | 82 | 0.837 | 0.952 | 0.979 | 0 |
| Qwen3-8B | Thinking | v2 | 0.737 | 0.730 | 0.744 | 157 | 58 | 54 | 77 | 0.876 | 0.943 | 0.969 | 1 |
| Qwen3-8B | Instruct | v5 | 0.736 | 0.687 | 0.791 | 167 | 76 | 44 | 64 | 0.934 | 0.928 | 0.976 | 0 |
| Qwen3-4B-Thinking | Thinking | v2 | 0.731 | 0.794 | 0.678 | 143 | 37 | 68 | 0 | 0.860 | 0.951 | 0.978 | 2 |
| Magistral-Small | Instruct | v3 | 0.681 | 0.665 | 0.697 | 147 | 74 | 64 | 76 | 0.846 | 0.929 | 0.973 | 0 |
| Qwen3-8B | Thinking | v1 | 0.711 | 0.665 | 0.763 | 161 | 81 | 50 | 64 | 0.857 | 0.935 | 0.000 | 0 |
| Qwen3-8B | Instruct | v6full | 0.709 | 0.738 | 0.682 | 144 | 51 | 67 | 88 | 0.831 | 0.932 | 0.990 | 0 |
| Qwen3.5-4B | Instruct | v3 | 0.647 | 0.655 | 0.640 | 135 | 71 | 76 | 79 | 0.865 | 0.952 | 0.981 | 2 |
| Qwen3-8B | Instruct | v3 | 0.692 | 0.708 | 0.678 | 143 | 59 | 68 | 77 | 0.821 | 0.952 | 0.994 | 1 |
| Qwen3-8B | Instruct | v4 | 0.683 | 0.693 | 0.673 | 142 | 63 | 69 | 72 | 0.851 | 0.945 | 0.994 | 0 |
| Qwen3-8B | Instruct | v1 | 0.681 | 0.695 | 0.668 | 141 | 62 | 70 | 69 | 0.844 | 0.946 | 0.000 | 7 |
| Qwen3-8B | Instruct | v2 | 0.634 | 0.701 | 0.578 | 122 | 52 | 89 | 78 | 0.895 | 0.960 | 0.980 | 2 |
| Qwen3-4B-Instruct | Instruct | v2 | 0.593 | 0.743 | 0.493 | 104 | 36 | 107 | 0 | 0.813 | 0.909 | 0.977 | 1 |
| Llama-3.1-8B | Instruct | v3 | 0.524 | 0.410 | 0.725 | 153 | 220 | 58 | 27 | 0.800 | 0.923 | 0.967 | 1 |
| Qwen3-8B | Instruct | v6lite | 0.543 | 0.779 | 0.417 | 88 | 25 | 123 | 92 | 0.862 | 0.928 | 0.992 | 0 |

## Run characteristics

Throughput is the median gap between consecutive output files. The projection is for the full ~11,000-paper corpus on one GPU.

| Model | Mode | Prompt | Papers | Reasoning closed | Avg output | Median s/paper | Projected GPU-h for 11,000 |
|---|---|---|---|---|---|---|---|
| Magistral-Small | Thinking | v6full | 267 | 100% | 5.0 KB | 112 | 343 |
| Qwen3-8B | Thinking | v3 | 267 | 100% | 4.2 KB | 31 | 96 |
| Gemma-4-12B | Thinking | v6full | 267 | 100% | 10.3 KB | 137 | 419 |
| Qwen3.6-27B | Instruct | v3 | 267 | 0% | 0.6 KB | 20 | 61 |
| Qwen3-8B | Thinking | v6lite | 267 | 100% | 5.4 KB | 45 | 139 |
| Qwen3.6-27B | Thinking | v3 | 267 | 100% | 9.6 KB | 284 | 868 |
| Qwen3-8B | Thinking | v5 | 267 | 100% | 5.2 KB | 22 | 68 |
| Magistral-Small | Thinking | v6lite | 267 | 100% | 4.9 KB | 67 | 205 |
| Qwen3-8B | Thinking | v6full | 267 | 100% | 5.5 KB | 22 | 69 |
| Magistral-Small | Thinking | v5 | 267 | 100% | 4.6 KB | 120 | 368 |
| Qwen3-8B | Thinking | v4 | 267 | 100% | 4.5 KB | 30 | 93 |
| Qwen3-8B | Thinking | v2 | 267 | 100% | 4.8 KB | 17 | 53 |
| Qwen3-8B | Instruct | v5 | 267 | 0% | 0.7 KB | 11 | 34 |
| Qwen3-4B-Thinking | Thinking | v2 | 175 | 98% | 24.8 KB | 146 | 447 |
| Magistral-Small | Instruct | v3 | 267 | 0% | 0.6 KB | 7 | 23 |
| Qwen3-8B | Thinking | v1 | 267 | 100% | 4.9 KB | 21 | 65 |
| Qwen3-8B | Instruct | v6full | 267 | 0% | 0.8 KB | 11 | 33 |
| Qwen3.5-4B | Instruct | v3 | 267 | 0% | 0.6 KB | 7 | 21 |
| Qwen3-8B | Instruct | v3 | 267 | 0% | 0.6 KB | 9 | 28 |
| Qwen3-8B | Instruct | v4 | 267 | 0% | 0.6 KB | 9 | 29 |
| Qwen3-8B | Instruct | v1 | 267 | 0% | 0.5 KB | 9 | 27 |
| Qwen3-8B | Instruct | v2 | 267 | 0% | 0.6 KB | 8 | 24 |
| Qwen3-4B-Instruct | Instruct | v2 | 175 | 0% | 0.7 KB | 7 | 22 |
| Llama-3.1-8B | Instruct | v3 | 267 | 0% | 1.0 KB | 7 | 22 |
| Qwen3-8B | Instruct | v6lite | 267 | 0% | 0.5 KB | 2 | 5 |

## Normalisation conditions

| Condition | Description |
|---|---|
| `none` | Raw model output scored against the unmodified gold |
| `fuzzy+LLM` | Fuzzy matching over an NCBI gene database, with a language model adjudicating between candidates |
| `HGNC` | Deterministic alias mapping from the HGNC complete set; the same rules are applied to the gold so matching is symmetric |
| `cascade` | HGNC first, then fuzzy+LLM over whatever the deterministic pass left unresolved |
