#!/bin/bash
#SBATCH --job-name=casc_gem
#SBATCH --time=02:00:00
#SBATCH --mem=48G
#SBATCH --partition=gpu-l40s,gpu-a-lowsmall,gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/casc_gem_%j.out
#SBATCH --error=logs/casc_gem_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python jamie_normalise_adapted.py --pred_dirs results_norm/gemma4_v6/gemma-4-12B-it --model models/Qwen3-8B --out_root results_cascade_all --report results/cascade_gemma_report.csv
