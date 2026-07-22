#!/bin/bash
#SBATCH --job-name=v5_q8b
#SBATCH --time=20:00:00
#SBATCH --mem=64G
#SBATCH --partition=gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/v5_q8b_%j.out
#SBATCH --error=logs/v5_q8b_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_think_simple.py --model models/Qwen3-8B --backend transformers --dataset data/eval_v5_dataset --split validation --max_new_tokens 20000 --max_seq_length 32000 --out_dir results/v5_think_8b
