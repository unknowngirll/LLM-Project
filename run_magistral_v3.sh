#!/bin/bash
#SBATCH --job-name=magi_v3
#SBATCH --time=08:00:00
#SBATCH --mem=96G
#SBATCH --partition=gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/magi_v3_%j.out
#SBATCH --error=logs/magi_v3_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_magistral.py --model models/Magistral-Small-2509 --load_in_4bit --dataset data/eval_v3_dataset --split validation --max_new_tokens 4096 --max_seq_length 8192 --out_dir results/magistral_v3_new
