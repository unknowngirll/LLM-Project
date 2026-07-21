#!/bin/bash
#SBATCH --job-name=q35_think
#SBATCH --time=20:00:00
#SBATCH --mem=40G
#SBATCH --partition=gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --output=logs/infer_q35_think_%j.out
#SBATCH --error=logs/infer_q35_think_%j.err

cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache

python infer_think_script.py \
    --model models/Qwen3.5-4B \
    --dataset data/eval_v3_dataset \
    --split validation \
    --max_new_tokens 12000 \
    --out_dir results/dev_think_35
