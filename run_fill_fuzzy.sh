#!/bin/bash
#SBATCH --job-name=fill_fz
#SBATCH --time=03:00:00
#SBATCH --mem=48G
#SBATCH --partition=gpu-l40s,gpu-a-lowsmall,gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/fill_fz_%j.out
#SBATCH --error=logs/fill_fz_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python jamie_normalise_adapted.py --pred_dirs results/simple_8b/Qwen3-8B results/simple_36/Qwen3.6-27B results/v5_think_8b/Qwen3-8B results/magi_think_v5/Magistral-Small-2509 results/magi_think_v6/Magistral-Small-2509 results/q8b_think_v6lite/Qwen3-8B results/gemma4_v6/gemma-4-12B-it results/magistral_v3_new/Magistral-Small-2509 --model models/Qwen3-8B --out_root results_jamie --report results/fuzzy_fill_report.csv
