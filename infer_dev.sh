#!/bin/bash
#SBATCH --job-name=infer_dev
#SBATCH --time=02:00:00
#SBATCH --mem=30G
#SBATCH --partition=gpu-a-lowsmall
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --output=logs/infer_dev_%j.out
#SBATCH --error=logs/infer_dev_%j.err
cd ~/LLM_Project
source py311/bin/activate
python infer.py \
    --model models/Qwen3-4B-Instruct-2507 \
    --dataset data/split_dataset \
    --split validation \
    --out_dir results/dev
