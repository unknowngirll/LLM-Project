# Master results table

Every run scored under every normalisation condition. All runs use the 267-paper OATargets evaluation set (175 positives + 92 true negatives) and `score_v2.py`, except the two v2 rows, which predate the true negatives and used a 175-paper positives-only set - their TN is 0 by construction and they are not comparable with the rest.

## Scoring conditions

| Condition | Description |
|---|---|
| `none` | Raw model output against the unmodified gold |
| `fuzzy+LLM` | Fuzzy matching over an NCBI gene database with a language model adjudicating between candidates |
| `HGNC v1` | Deterministic alias mapping, first implementation |
| `HGNC v2` | Revised mapping: indexes HGNC gene names as well as alias symbols, filters pseudogenes, strips mouse/rat ortholog suffixes, and resolves ambiguous aliases against the paper's own text |
| `cascade` | `HGNC v1` followed by fuzzy+LLM on whatever it left unresolved |

## F1 by condition

| Model | Params | Mode | Prompt | none | fuzzy+LLM | HGNC v1 | HGNC v2 | cascade |
|---|---|---|---|---|---|---|---|---|
| Magistral-Small | 24B | Thinking | v7full | 0.704 | -- | -- | **0.856** | -- |
| Magistral-Small | 24B | Thinking | v4 | 0.597 | -- | 0.782 | **0.848** | -- |
| Magistral-Small | 24B | Thinking | v7lite | 0.692 | -- | -- | **0.839** | -- |
| Magistral-Small | 24B | Thinking | v6full | 0.729 | 0.771 | 0.796 | 0.834 | **0.838** |
| Qwen3-8B | 8B | Thinking | v6full | 0.642 | -- | 0.760 | **0.832** | -- |
| Magistral-Small | 24B | Thinking | v6lite | 0.700 | -- | 0.786 | **0.829** | -- |
| Qwen3.6-27B | 27B | Instruct | v3 | 0.592 | 0.640 | 0.754 | **0.825** | 0.806 |
| Qwen3-8B | 8B | Thinking | v4 | 0.595 | -- | 0.756 | **0.824** | -- |
| Magistral-Small | 24B | Thinking | v3 | 0.620 | -- | 0.764 | **0.821** | -- |
| Qwen3.6-27B | 27B | Thinking | v3 | 0.526 | 0.604 | 0.728 | **0.815** | 0.792 |
| Qwen3-8B | 8B | Thinking | v6lite | 0.625 | 0.695 | 0.739 | **0.814** | 0.799 |
| Gemma-4-12B | 12B | Thinking | v6full | 0.621 | 0.706 | 0.745 | **0.811** | 0.807 |
| Qwen3-8B | 8B | Thinking | v3 | 0.598 | 0.646 | 0.761 | **0.810** | **0.810** |
| Qwen3-8B | 8B | Thinking | v2 | 0.544 | -- | 0.737 | **0.808** | -- |
| Qwen3-4B-Thinking | 4B | Thinking | v2 | 0.544 | -- | 0.731 | **0.803** | -- |
| Qwen3-8B | 8B | Thinking | v7full | 0.606 | -- | -- | **0.798** | -- |
| Magistral-Small | 24B | Thinking | v2 | 0.536 | -- | 0.731 | **0.795** | -- |
| Magistral-Small | 24B | Thinking | v1 | 0.554 | -- | 0.738 | **0.794** | -- |
| Qwen3-8B | 8B | Thinking | v5 | 0.677 | 0.731 | 0.753 | 0.780 | **0.789** |
| Qwen3-8B | 8B | Thinking | v7lite | 0.619 | -- | -- | **0.789** | -- |
| Qwen3-8B | 8B | Thinking | v1 | 0.517 | -- | 0.711 | **0.777** | -- |
| Magistral-Small | 24B | Thinking | v5 | 0.746 | 0.742 | 0.757 | **0.766** | 0.757 |
| Qwen3-8B | 8B | Instruct | v5 | 0.643 | -- | 0.736 | **0.762** | -- |
| Qwen3-8B | 8B | Instruct | v3 | 0.518 | -- | 0.692 | **0.760** | -- |
| Qwen3-8B | 8B | Instruct | v6full | 0.565 | -- | 0.709 | **0.754** | -- |
| Qwen3-8B | 8B | Instruct | v4 | 0.510 | -- | 0.683 | **0.750** | -- |
| Magistral-Small | 24B | Instruct | v3 | 0.532 | 0.580 | 0.681 | **0.749** | 0.731 |
| Qwen3.5-4B | 4B | Instruct | v3 | 0.451 | 0.514 | 0.647 | **0.739** | 0.705 |
| Qwen3-8B | 8B | Instruct | v1 | 0.443 | -- | 0.681 | **0.739** | -- |
| Qwen3-8B | 8B | Instruct | v5 k=0 | 0.538 | -- | 0.692 | **0.726** | -- |
| Qwen3-8B | 8B | Instruct | v5 k=3 | 0.565 | -- | 0.696 | **0.722** | -- |
| Qwen3-8B | 8B | Instruct | v5 k=5 | 0.536 | -- | 0.679 | **0.699** | -- |
| Qwen3-8B | 8B | Instruct | v2 | 0.469 | -- | 0.634 | **0.696** | -- |
| Qwen3-4B-Instruct | 4B | Instruct | v2 | 0.422 | -- | 0.593 | **0.667** | -- |
| Qwen3-8B | 8B | Instruct | v6lite | 0.481 | -- | 0.543 | **0.580** | -- |
| Llama-3.1-8B | 8B | Instruct | v3 | 0.384 | 0.418 | 0.524 | **0.576** | 0.568 |

## Detail under the revised normalisation (`HGNC v2`)

| Model | Mode | Prompt | F1 | P | R | TP | FP | FN | TN | Rejected | Induction | Outcome | Species | Parse fail |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Magistral-Small | Thinking | v7full | 0.856 | 0.837 | 0.877 | 185 | 36 | 26 | 89 | 93 | 0.888 | 0.941 | 0.974 | 2 |
| Magistral-Small | Thinking | v4 | 0.848 | 0.848 | 0.848 | 179 | 32 | 32 | 85 | 92 | 0.876 | 0.946 | 0.981 | 0 |
| Magistral-Small | Thinking | v7lite | 0.839 | 0.839 | 0.839 | 177 | 34 | 34 | 89 | 98 | 0.907 | 0.969 | 0.965 | 0 |
| Magistral-Small | Thinking | v6full | 0.834 | 0.824 | 0.844 | 178 | 38 | 33 | 83 | 91 | 0.886 | 0.969 | 0.973 | 1 |
| Qwen3-8B | Thinking | v6full | 0.832 | 0.870 | 0.796 | 168 | 25 | 43 | 90 | 108 | 0.887 | 0.941 | 0.982 | 0 |
| Magistral-Small | Thinking | v6lite | 0.829 | 0.833 | 0.825 | 174 | 35 | 37 | 88 | 102 | 0.856 | 0.947 | 0.973 | 0 |
| Qwen3.6-27B | Instruct | v3 | 0.825 | 0.825 | 0.825 | 174 | 37 | 37 | 88 | 98 | 0.861 | 0.941 | 0.968 | 0 |
| Qwen3-8B | Thinking | v4 | 0.824 | 0.849 | 0.801 | 169 | 30 | 42 | 82 | 99 | 0.848 | 0.950 | 0.980 | 0 |
| Magistral-Small | Thinking | v3 | 0.821 | 0.805 | 0.839 | 177 | 43 | 34 | 83 | 91 | 0.834 | 0.941 | 0.977 | 0 |
| Qwen3.6-27B | Thinking | v3 | 0.815 | 0.788 | 0.844 | 178 | 48 | 33 | 80 | 85 | 0.855 | 0.939 | 0.976 | 0 |
| Qwen3-8B | Thinking | v6lite | 0.814 | 0.854 | 0.777 | 164 | 28 | 47 | 88 | 106 | 0.882 | 0.937 | 0.985 | 0 |
| Gemma-4-12B | Thinking | v6full | 0.811 | 0.808 | 0.815 | 172 | 41 | 39 | 90 | 104 | 0.878 | 0.946 | 0.986 | 1 |
| Qwen3-8B | Thinking | v3 | 0.810 | 0.824 | 0.796 | 168 | 36 | 43 | 83 | 93 | 0.860 | 0.940 | 0.970 | 0 |
| Qwen3-8B | Thinking | v2 | 0.808 | 0.800 | 0.815 | 172 | 43 | 39 | 77 | 89 | 0.886 | 0.943 | 0.971 | 1 |
| Qwen3-4B-Thinking | Thinking | v2 | 0.803 | 0.872 | 0.744 | 157 | 23 | 54 | 0 | 18 | 0.872 | 0.955 | 0.979 | 2 |
| Qwen3-8B | Thinking | v7full | 0.798 | 0.854 | 0.749 | 158 | 27 | 53 | 90 | 113 | 0.910 | 0.946 | 0.995 | 0 |
| Magistral-Small | Thinking | v2 | 0.795 | 0.767 | 0.825 | 174 | 53 | 37 | 71 | 78 | 0.888 | 0.950 | 0.986 | 0 |
| Magistral-Small | Thinking | v1 | 0.794 | 0.725 | 0.877 | 185 | 70 | 26 | 62 | 65 | 0.882 | 0.948 | 0.000 | 0 |
| Qwen3-8B | Thinking | v5 | 0.780 | 0.740 | 0.825 | 174 | 61 | 37 | 73 | 75 | 0.875 | 0.942 | 0.971 | 0 |
| Qwen3-8B | Thinking | v7lite | 0.789 | 0.864 | 0.725 | 153 | 24 | 58 | 90 | 117 | 0.843 | 0.942 | 0.984 | 0 |
| Qwen3-8B | Thinking | v1 | 0.777 | 0.727 | 0.834 | 176 | 66 | 35 | 64 | 67 | 0.868 | 0.930 | 0.000 | 0 |
| Magistral-Small | Thinking | v5 | 0.766 | 0.695 | 0.853 | 180 | 79 | 31 | 61 | 63 | 0.876 | 0.951 | 0.977 | 0 |
| Qwen3-8B | Instruct | v5 | 0.762 | 0.712 | 0.820 | 173 | 70 | 38 | 64 | 70 | 0.935 | 0.930 | 0.977 | 0 |
| Qwen3-8B | Instruct | v3 | 0.760 | 0.777 | 0.744 | 157 | 45 | 54 | 77 | 100 | 0.834 | 0.950 | 0.989 | 1 |
| Qwen3-8B | Instruct | v6full | 0.754 | 0.785 | 0.725 | 153 | 42 | 58 | 88 | 116 | 0.835 | 0.936 | 0.985 | 0 |
| Qwen3-8B | Instruct | v4 | 0.750 | 0.761 | 0.739 | 156 | 49 | 55 | 72 | 93 | 0.863 | 0.939 | 0.989 | 0 |
| Magistral-Small | Instruct | v3 | 0.749 | 0.735 | 0.763 | 161 | 58 | 50 | 76 | 91 | 0.858 | 0.930 | 0.975 | 0 |
| Qwen3.5-4B | Instruct | v3 | 0.739 | 0.748 | 0.730 | 154 | 52 | 57 | 79 | 93 | 0.870 | 0.952 | 0.984 | 2 |
| Qwen3-8B | Instruct | v1 | 0.739 | 0.754 | 0.725 | 153 | 50 | 58 | 69 | 89 | 0.853 | 0.950 | 0.000 | 7 |
| Qwen3-8B | Instruct | v5 k=0 | 0.726 | 0.661 | 0.806 | 170 | 87 | 41 | 63 | 69 | 0.910 | 0.936 | 0.975 | 0 |
| Qwen3-8B | Instruct | v5 k=3 | 0.722 | 0.650 | 0.810 | 171 | 92 | 40 | 53 | 56 | 0.874 | 0.938 | 0.976 | 0 |
| Qwen3-8B | Instruct | v5 k=5 | 0.699 | 0.615 | 0.810 | 171 | 107 | 40 | 40 | 44 | 0.857 | 0.932 | 0.990 | 0 |
| Qwen3-8B | Instruct | v2 | 0.696 | 0.770 | 0.635 | 134 | 40 | 77 | 78 | 116 | 0.902 | 0.957 | 0.976 | 2 |
| Qwen3-4B-Instruct | Instruct | v2 | 0.667 | 0.836 | 0.555 | 117 | 23 | 94 | 0 | 58 | 0.824 | 0.918 | 0.973 | 1 |
| Qwen3-8B | Instruct | v6lite | 0.580 | 0.832 | 0.445 | 94 | 19 | 117 | 92 | 178 | 0.860 | 0.931 | 0.992 | 0 |
| Llama-3.1-8B | Instruct | v3 | 0.576 | 0.452 | 0.796 | 168 | 204 | 43 | 27 | 27 | 0.818 | 0.925 | 0.970 | 1 |

## Notes

- The rejected column counts abstracts for which the model returned the explicit rejection object. 92 of the 267 genuinely warrant rejection, so counts far above that indicate over-rejection.
- Prompt v1 emits `animal_species` rather than `species` and has no `manipulation_direction` field, so its species accuracy is zero by construction and its attribute scores are not comparable.
- Most conditions are a single run. Repeat runs at one temperature gave a standard deviation of 0.015 F1, so differences smaller than roughly 0.03 should not be read as real.
