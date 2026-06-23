#!/bin/bash
#SBATCH --job-name=infer_q8b
#SBATCH --time=03:00:00
#SBATCH --mem=40G
#SBATCH --partition=gpu-a-lowsmall
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --output=logs/infer_q8b_%j.out
#SBATCH --error=logs/infer_q8b_%j.err
cd ~/LLM_Project
source py311/bin/activate
python infer.py \
    --model models/Qwen3-8B \
    --dataset data/split_dataset \
    --split validation \
    --max_new_tokens 4000 \
    --out_dir results/dev
