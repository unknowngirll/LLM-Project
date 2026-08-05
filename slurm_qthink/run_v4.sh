#!/bin/bash
#SBATCH --job-name=qt_v4
#SBATCH --time=12:00:00
#SBATCH --mem=64G
#SBATCH --partition=gpu-l40s,gpu-a-lowsmall,gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/qt_v4_%j.out
#SBATCH --error=logs/qt_v4_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_think_simple.py --model models/Qwen3-8B --backend transformers --dataset data/eval_v4_dataset --split validation --max_new_tokens 20000 --max_seq_length 24000 --out_dir results/qthink_v4
