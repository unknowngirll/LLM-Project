#!/bin/bash
#SBATCH --job-name=casc_all
#SBATCH --time=04:00:00
#SBATCH --mem=48G
#SBATCH --partition=gpu-l40s,gpu-a-lowsmall,gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/casc_all_%j.out
#SBATCH --error=logs/casc_all_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python jamie_normalise_adapted.py --pred_dirs results_norm/magi_think_v6/Magistral-Small-2509 results_norm/magi_think_v5/Magistral-Small-2509 results_norm/magistral_v3_new/Magistral-Small-2509 results_norm/simple_8b/Qwen3-8B results_norm/v5_think_8b/Qwen3-8B results_norm/q8b_think_v6lite/Qwen3-8B results_norm/nothink_8b/Qwen3-8B results_norm/dev_think_8b/Qwen3-8B results_norm/simple_36/Qwen3.6-27B results_norm/qwen36_v3/Qwen3.6-27B results_norm/nothink_35/Qwen3.5-4B results_norm/llama31_v3/Llama-3.1-8B-Instruct --model models/Qwen3-8B --out_root results_cascade_all --report results/cascade_all_report.csv
