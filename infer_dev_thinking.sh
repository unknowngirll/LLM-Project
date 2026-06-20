#!/bin/bash
#SBATCH --job-name=infer_think
#SBATCH --time=24:00:00
#SBATCH --mem=40G
#SBATCH --partition=gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --output=logs/infer_think_%j.out
#SBATCH --error=logs/infer_think_%j.err
cd ~/LLM_Project
source py311/bin/activate
python infer.py \
    --model models/Qwen3-4B-Thinking-2507 \
    --dataset data/split_dataset \
    --split validation \
    --max_new_tokens 12000 \
    --out_dir results/dev
