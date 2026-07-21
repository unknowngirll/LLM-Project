#!/bin/bash
#SBATCH --job-name=llama31
#SBATCH --time=04:00:00
#SBATCH --mem=48G
#SBATCH --partition=gpu-l40s,gpu-a-lowsmall,gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/llama31_%j.out
#SBATCH --error=logs/llama31_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_unsloth.py --model models/Llama-3.1-8B-Instruct --dataset data/eval_v3_dataset --split validation --max_new_tokens 4096 --max_seq_length 8192 --out_dir results/llama31_v3
