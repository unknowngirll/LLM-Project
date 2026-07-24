#!/bin/bash
#SBATCH --job-name=magi_t
#SBATCH --time=01:00:00
#SBATCH --mem=96G
#SBATCH --partition=gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/magi_t_%j.out
#SBATCH --error=logs/magi_t_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
export CUDA_LAUNCH_BLOCKING=1
python infer_magistral.py --model models/Magistral-Small-2509 --load_in_4bit --dataset data/eval_v3_dataset --split validation --limit 2 --max_new_tokens 2048 --max_seq_length 8192 --out_dir results/TEST_magistral
