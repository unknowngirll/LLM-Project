#!/bin/bash
#SBATCH --job-name=abl
#SBATCH --time=06:00:00
#SBATCH --mem=48G
#SBATCH --partition=gpu-l40s,gpu-a-lowsmall,gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/abl_%j.out
#SBATCH --error=logs/abl_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python jamie_normalise_adapted.py --pre_rules --pred_dirs results/nothink_8b/Qwen3-8B results/nothink_35/Qwen3.5-4B results/llama31_v3/Llama-3.1-8B-Instruct results/qwen36_v3/Qwen3.6-27B --model models/Qwen3-8B --out_root results_jamie_fair --report results/abl_fair.csv
python jamie_normalise_adapted.py --pred_dirs results_norm/nothink_8b/Qwen3-8B results_norm/nothink_35/Qwen3.5-4B results_norm/llama31_v3/Llama-3.1-8B-Instruct results_norm/qwen36_v3/Qwen3.6-27B --model models/Qwen3-8B --out_root results_cascade --report results/abl_cascade.csv
python jamie_normalise_adapted.py --pre_rules --pred_dirs results/simple_8b/Qwen3-8B results/simple_36/Qwen3.6-27B results/v5_think_8b/Qwen3-8B --model models/Qwen3-8B --out_root results_jamie_think --report results/abl_think.csv
