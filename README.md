# Automated Metadata Extraction for Osteoarthritis Research

**Project Overview**
This repository contains a specialized bioinformatics pipeline designed to automate the extraction of structured metadata from Osteoarthritis (OA) literature. By leveraging local, open-weight Large Language Models (LLMs), this project transforms unstructured PubMed abstracts into a structured knowledge base to support the assisted curation of the **OATargets** database.

Faced with a rapidly growing corpus of over 11,839 candidate papers, manual biocuration has become a significant bottleneck[cite: 1, 5]. This pipeline addresses that challenge through zero-shot extraction, rigorous prompt engineering, and a robust post-extraction gene symbol normalisation framework.

## Key Features & Pipeline Workflow

1. **Local Open-Weight LLMs:** Complete transition from commercial APIs to cost-effective, privacy-preserving local models (Magistral, Qwen, Gemma, Llama) ranging from 4B to 27B parameters, deployed on HPC clusters (e.g., Barkla2)[cite: 1, 5].
2. **Iterative Prompt Engineering (v1 to v7):** Carefully crafted instruction schemas dictating extraction targets (Gene, Species, Induction Method, Perturbation Direction, Severity Outcome) and strict rejection criteria for false positives[cite: 1, 5].
3. **Gene Symbol Normalisation (HGNC v2):** A critical post-processing engine. Since authors frequently use arbitrary aliases (e.g., *SDF-1*), this multi-step deterministic pipeline resolves raw extracted names to official HGNC symbols, filtering pseudogenes and resolving ambiguous aliases[cite: 1, 5].
4. **Ensemble Consensus:** A model-agreement evaluation technique where unanimity among different models is used to predict extraction correctness, acting as a highly reliable filter for expert human review[cite: 1, 5].

## Benchmarking Results

The pipeline was rigorously evaluated against a gold-standard development set of 267 abstracts (175 positives, 92 true negatives) from OATargets[cite: 1, 5]. 

### The Impact of Gene Normalisation
The most significant finding of this project is that extraction capability is bottlenecked by biological nomenclature, not just LLM reasoning. Standardising raw model outputs via our `HGNC v2` pipeline yielded a massive performance jump, often raising baseline F1 scores by >0.20 on identical text outputs.

**Top Performing Configurations (F1 Scores):**

| Model | Params | Mode | Prompt | Raw Output (`none`) | Normalised (`HGNC v2`) |
|---|---|---|---|---|---|
| **Magistral-Small** | 24B | Thinking | v7full | 0.704 | **0.856** |
| **Magistral-Small** | 24B | Thinking | v4 | 0.597 | **0.848** |
| **Qwen3-8B** | 8B | Thinking | v6full | 0.642 | **0.832** |
| **Qwen3.6-27B** | 27B | Instruct | v3 | 0.592 | **0.825** |
| **Gemma-4-12B** | 12B | Thinking | v6full | 0.621 | **0.811** |

### Attribute-Level Accuracy
Identifying the perturbed gene proved to be the most challenging step. However, once a gene was successfully matched and normalised, the models demonstrated exceptional accuracy in extracting secondary metadata under the `HGNC v2` normalisation:
* **Animal Species:** ~ 97 - 99%
* **Induction Method:** ~ 85 - 91%
* **Severity Outcome:** ~ 94 - 96%

## Key Conclusions

* **Prompt vs. Model Capacity:** Prompt revisions interact strongly with model capacity. Stricter exclusion rules (like `v7full`) improved the 24B Magistral model but caused the 8B Qwen model to over-reject valid papers[cite: 1, 5].
* **Assisted Curation via Consensus:** While combining models did not beat the best single model's overall F1 score, model agreement is a powerful predictor of truth. Genes identified by three models working in consensus matched curated ground truth data in **87.1%** of cases[cite: 1, 5]. This tiered approach is highly effective for triaging literature for human biocurators.

## Repository Structure
* `/prompts/` - Iterative versions (v1-v7) of system and user prompts used for zero-shot extraction.
* `/scripts/` - Inference scripts for running 4-bit quantized models locally via HuggingFace and Unsloth.
* `/normalisation/` - The `HGNC v2` mapping rules and standardisation cascade.
* `/analysis/` - R and Python scripts used for scoring (`score_v2.py`) and calculating precision, recall, and F1 metrics.
