#!/bin/bash
#SBATCH --job-name=q36_neg
#SBATCH --time=03:00:00
#SBATCH --mem=64G
#SBATCH --partition=gpu-h100,gpu-l40s
#SBATCH --gres=gpu:1
#SBATCH --output=logs/q36_neg_%j.out
#SBATCH --error=logs/q36_neg_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/data/hf_cache
python infer_unsloth.py \
    --model unsloth/Qwen3.6-27B \
    --load_in_4bit \
    --dataset data/negatives_dataset \
    --split validation \
    --max_new_tokens 12000 \
    --max_seq_length 16384 \
    --out_dir results/qwen36_full
