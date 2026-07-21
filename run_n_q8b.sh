#!/bin/bash
#SBATCH --job-name=n_q8b
#SBATCH --time=06:00:00
#SBATCH --mem=48G
#SBATCH --partition=gpu-l40s,gpu-a-lowsmall,gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/n_q8b_%j.out
#SBATCH --error=logs/n_q8b_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_unsloth.py --model models/Qwen3-8B --dataset data/eval_v3_dataset --split validation --max_new_tokens 4096 --max_seq_length 8192 --out_dir results/nothink_8b
