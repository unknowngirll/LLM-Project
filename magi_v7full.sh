#!/bin/bash
#SBATCH --job-name=magi_v7full
#SBATCH --time=20:00:00
#SBATCH --mem=96G
#SBATCH --partition=gpu-h100,gpu-l40s,gpu-a-lowsmall
#SBATCH --gres=gpu:1
#SBATCH --output=logs/magi_v7full_%j.out
#SBATCH --error=logs/magi_v7full_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_magistral_think.py --model models/Magistral-Small-2509 --load_in_4bit --dataset data/eval_v7full_dataset --split validation --max_new_tokens 12000 --max_seq_length 24000 --temperature 0.7 --top_p 0.95 --out_dir results/magi_think_v7full
