#!/bin/bash
#SBATCH --job-name=s_q35
#SBATCH --time=20:00:00
#SBATCH --mem=32G
#SBATCH --partition=gpu-l40s,gpu-a-lowsmall,gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/s_q35_%j.out
#SBATCH --error=logs/s_q35_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_think_simple.py --model models/Qwen3.5-4B --backend transformers --dataset data/eval_v3_dataset --split validation --max_new_tokens 20000 --max_seq_length 24000 --out_dir results/simple_35
