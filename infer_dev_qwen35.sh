#!/bin/bash
#SBATCH --job-name=infer_q35
#SBATCH --time=02:00:00
#SBATCH --mem=30G
#SBATCH --partition=gpu-a-lowsmall
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --output=logs/infer_q35_%j.out
#SBATCH --error=logs/infer_q35_%j.err
cd ~/LLM_Project
source py311/bin/activate
python infer.py \
    --model models/Qwen3.5-4B \
    --dataset data/split_dataset \
    --split validation \
    --max_new_tokens 2000 \
    --out_dir results/dev
