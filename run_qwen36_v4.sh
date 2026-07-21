#!/bin/bash
#SBATCH --job-name=q36_v4
#SBATCH --time=04:00:00
#SBATCH --mem=64G
#SBATCH --partition=gpu-h100,gpu-l40s
#SBATCH --gres=gpu:1
#SBATCH --output=logs/q36_v4_%j.out
#SBATCH --error=logs/q36_v4_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/data/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_unsloth.py --model unsloth/Qwen3.6-27B --load_in_4bit --dataset data/eval_v4_dataset --split validation --max_new_tokens 4096 --max_seq_length 8192 --out_dir results/qwen36_v4
