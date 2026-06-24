#!/bin/bash
#SBATCH --job-name=test_unsloth
#SBATCH --time=00:30:00
#SBATCH --mem=40G
#SBATCH --partition=gpu-a-lowsmall
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --output=logs/test_unsloth_%j.out
#SBATCH --error=logs/test_unsloth_%j.err
cd ~/LLM_Project
source py311/bin/activate
python infer_unsloth.py \
    --model models/Qwen3-8B \
    --dataset data/split_dataset \
    --split validation \
    --limit 3 \
    --max_new_tokens 2000 \
    --out_dir results/test_unsloth
