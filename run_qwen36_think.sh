#!/bin/bash
#SBATCH --job-name=qwen36_th
#SBATCH --time=12:00:00
#SBATCH --mem=80G
#SBATCH --partition=gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/qwen36_think_%j.out
#SBATCH --error=logs/qwen36_think_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_unsloth.py --model unsloth/Qwen3.6-27B --load_in_4bit --dataset data/eval_v3_dataset --split validation --max_new_tokens 16000 --max_seq_length 20000 --out_dir results/qwen36_think
