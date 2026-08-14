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

## Compute cost

| File | Contents |
|---|---|
| `cost_accuracy_vs_speed.png` | F1 against median seconds per abstract, log x-axis; point size scales with parameter count, marker shape distinguishes instruct from thinking mode |
| `cost_gpu_hours.png` | Projected single-GPU hours to process the full 11,000-abstract corpus |

Throughput is estimated from the gaps between consecutive output-file
timestamps, taking the median so that queue stalls and the initial model load
do not dominate. Jobs were scheduled across three GPU classes on the cluster
(H100, L40S, and the a-lowsmall partition), marked on each point, so these
figures indicate relative cost rather than a controlled benchmark. Gemma-4-12B
ran on the fastest available hardware and was still the slowest configuration
tested.

## Consensus (revised normalisation)

| File | Contents |
|---|---|
| `consensus_ladder.png` | Proportion of extracted genes matching the gold standard, grouped by how many of the three models extracted that gene |
| `consensus_scores.png` | Precision, recall and F1 for each single model and each consensus rule |

Three models contribute: Magistral-Small and Gemma-4-12B on the full v6 prompt,
and Qwen3-8B on v6 full. All outputs are scored after the revised HGNC
normalisation, so these figures are comparable with the main results tables.
The ladder panel is not a measure of the consensus rules themselves — it asks
how often an individual extracted gene is correct given the number of models
that agreed on it.
