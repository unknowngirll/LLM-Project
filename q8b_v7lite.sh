#!/bin/bash
#SBATCH --job-name=q8b_v7lite
#SBATCH --time=12:00:00
#SBATCH --mem=64G
#SBATCH --partition=gpu-l40s,gpu-a-lowsmall,gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/q8b_v7lite_%j.out
#SBATCH --error=logs/q8b_v7lite_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_think_simple.py --model models/Qwen3-8B --backend transformers --dataset data/eval_v7lite_dataset --split validation --max_new_tokens 20000 --max_seq_length 32000 --out_dir results/q8b_think_v7lite
