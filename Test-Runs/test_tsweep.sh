#!/bin/bash
#SBATCH --job-name=ts_t06_s1
#SBATCH --time=01:00:00
#SBATCH --mem=48G
#SBATCH --partition=gpu-l40s,gpu-a-lowsmall,gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/ts_t06_s1_%j.out
#SBATCH --error=logs/ts_t06_s1_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_think_seed.py --model models/Qwen3-8B --backend transformers --dataset data/eval_v3_dataset --split validation --temperature 0.6 --seed 1 --max_new_tokens 20000 --max_seq_length 24000 --limit 4 --out_dir results/TEST_tsweep
