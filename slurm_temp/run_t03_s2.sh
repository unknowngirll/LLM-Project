#!/bin/bash
#SBATCH --job-name=ts_t03_s2
#SBATCH --time=10:00:00
#SBATCH --mem=48G
#SBATCH --partition=gpu-l40s,gpu-a-lowsmall,gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/ts_t03_s2_%j.out
#SBATCH --error=logs/ts_t03_s2_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_think_seed.py --model models/Qwen3-8B --backend transformers --dataset data/eval_v3_dataset --split validation --temperature 0.3 --seed 2 --max_new_tokens 20000 --max_seq_length 24000 --out_dir results/tsweep_t03_s2
