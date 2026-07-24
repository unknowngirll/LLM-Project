#!/bin/bash
#SBATCH --job-name=jamie_n
#SBATCH --time=03:00:00
#SBATCH --mem=48G
#SBATCH --partition=gpu-l40s,gpu-a-lowsmall,gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/jamie_n_%j.out
#SBATCH --error=logs/jamie_n_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python jamie_normalise_adapted.py --pred_dirs results/simple_8b/Qwen3-8B --model models/Qwen3-8B --out_root results_jamie --report results/jamie_normalisation_report.csv
