# Figures

All figures were generated from the 267-paper OATargets evaluation set
(175 positives + 92 true negatives) unless noted otherwise.

## Prompt development

| File | Contents |
|---|---|
| `prompt_two_models_f1.png` | F1 across prompt versions v1–v6full for Qwen3-8B and Magistral-Small, both in thinking mode |
| `prompt_two_models_rejection.png` | Abstracts rejected outright by each model and prompt version |
| `prompt_sweep_instruct_f1.png` | Qwen3-8B instruct: F1 across prompt versions, raw and HGNC-normalised |
| `prompt_sweep_instruct_rejection.png` | Qwen3-8B instruct: rejection counts |
| `prompt_sweep_thinking_f1.png` | Qwen3-8B thinking: F1 across prompt versions |
| `prompt_sweep_thinking_rejection.png` | Qwen3-8B thinking: rejection counts |

## Model comparison

| File | Contents |
|---|---|
| `model_comparison_A_recovery.png` | Gene-level recovery: correct and incorrect predictions per model |
| `model_comparison_B_normalisation.png` | Effect of each gene-normalisation method |
| `model_comparison_C_attributes.png` | Attribute annotation accuracy (induction, outcome, species) |
| `model_comparison_D_precision_recall.png` | Precision against recall across models |

## Consensus

| File | Contents |
|---|---|
| `consensus_ladder.png` | Proportion of genes matching the gold standard, by how many models extracted them |
| `consensus_scores.png` | Precision, recall and F1 for single models and consensus rules |

## Decoding parameters

| File | Contents |
|---|---|
| `temperature_A_f1.png` | F1 against temperature, three seeds per setting |
| `temperature_B_pr.png` | Precision against recall by temperature and seed |

## Note on the rejection panels

The dashed line marks the 92 true negatives in the evaluation set. It is a
reference point rather than a target: rejecting 92 abstracts does not
guarantee rejecting the correct 92. Counts well above the line indicate
over-rejection at the cost of recall.
