# Automated Metadata Extraction for Osteoarthritis Research
 Project Overview by Nilla Rezaei

This repository contains a specialized pipeline designed to automate the extraction of structured metadata from Osteoarthritis (OA) literature. As part of a bioinformatics research initiative at the University of Liverpool, this project leverages Large Language Models (LLMs) to transform unstructured PubMed abstracts into a structured knowledge base, specifically aimed at expanding the OA Target database.
Key Goals:

    Automation: Minimize manual curation of OA animal model studies.

    Benchmarking: Comparing commercial (GPT-4o, Claude 3.5, Gemini Pro) vs. local open-weight models (Qwen, Llama, Gemma).

    Scalability: Processing a corpus of 11,839 unique PMIDs (Mouse, Rat, Rabbit, Pig) identified via NCBI Entrez.

Workflow

The extraction process follows a rigorous validation-first approach:

    Literature Mining: Systematic retrieval of PMIDs using NCBI E-utilities.

    Prompt Engineering: Implementation of a strict, rule-based JSON extraction prompt.

    LLM Inference: Data extraction across multiple LLM architectures.

    Validation: Scoring outputs against the OA Target gold standard.

    Visualization: Performance metrics analyzed and plotted using R (ggplot2).

 Benchmarking Results (Commercial Baseline)

Preliminary results using commercial APIs showed high fidelity across four critical features:

    Target Gene: >80% accuracy.

    Animal Species: 100% accuracy.

    Perturbation Type: High precision in identifying Genetic vs. Pharmacological models.

    Phenotype Outcome: Claude and Gemini demonstrated superior reasoning in biological effect deduction.

Next Steps: Local Deployment (Barkla2)

The next phase involves transitioning from commercial APIs to local deployment on the Barkla2 High-Performance Computing (HPC) cluster.

    Local Models: Testing Qwen3.6-35B-A3B, Llama 3, and Gemma.

    Quantization: Utilizing 4-bit and 8-bit precision for efficient resource management.

    Scale: Expanding the OA Target database using the optimal localized pipeline.
