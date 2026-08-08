#!/bin/bash
#SBATCH --job-name=dyn_k5
#SBATCH --time=06:00:00
#SBATCH --mem=48G
#SBATCH --partition=gpu-l40s,gpu-a-lowsmall,gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/dyn_k5_%j.out
#SBATCH --error=logs/dyn_k5_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_unsloth.py --model models/Qwen3-8B --dataset data/eval_dyn_k5_dataset --split validation --max_new_tokens 4096 --max_seq_length 32000 --out_dir results/dyn_k5
