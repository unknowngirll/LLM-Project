#!/bin/bash
#SBATCH --job-name=q4b_think
#SBATCH --time=12:00:00
#SBATCH --mem=48G
#SBATCH --partition=gpu-l40s,gpu-a-lowsmall,gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/q4b_think_%j.out
#SBATCH --error=logs/q4b_think_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_think_simple.py --model models/Qwen3-4B-Thinking-2507 --backend transformers --dataset data/eval_v6_dataset --split validation --max_new_tokens 20000 --max_seq_length 32000 --out_dir results/q4b_think_v6
