#!/bin/bash
#SBATCH --job-name=magi_t5
#SBATCH --time=01:30:00
#SBATCH --mem=96G
#SBATCH --partition=gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/magi_t5_%j.out
#SBATCH --error=logs/magi_t5_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_magistral_think.py --model models/Magistral-Small-2509 --load_in_4bit --dataset data/eval_v5_dataset --split validation --limit 3 --max_new_tokens 12000 --max_seq_length 16000 --out_dir results/TEST_magi_v5
