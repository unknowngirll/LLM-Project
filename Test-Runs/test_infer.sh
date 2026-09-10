#!/bin/bash
#SBATCH --job-name=test_infer
#SBATCH --time=00:30:00
#SBATCH --mem=30G
#SBATCH --partition=gpu-a-lowsmall
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --output=logs/test_infer_%j.out
#SBATCH --error=logs/test_infer_%j.err

cd ~/LLM_Project
source py311/bin/activate

python infer.py \
    --model models/Qwen3-4B-Instruct-2507 \
    --dataset data/eval_dataset \
    --limit 5 \
    --out_dir results
