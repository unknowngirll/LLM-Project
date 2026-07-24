#!/bin/bash
#SBATCH --job-name=jamie_ins
#SBATCH --time=04:00:00
#SBATCH --mem=48G
#SBATCH --partition=gpu-l40s,gpu-a-lowsmall,gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/jamie_ins_%j.out
#SBATCH --error=logs/jamie_ins_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python jamie_normalise_adapted.py --pred_dirs results/nothink_8b/Qwen3-8B results/nothink_35/Qwen3.5-4B results/llama31_v3/Llama-3.1-8B-Instruct results/qwen36_v3/Qwen3.6-27B --model models/Qwen3-8B --out_root results_jamie --report results/jamie_norm_instruct.csv
