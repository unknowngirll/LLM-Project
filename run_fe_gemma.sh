#!/bin/bash
#SBATCH --job-name=fe_gem
#SBATCH --time=20:00:00
#SBATCH --mem=64G
#SBATCH --partition=gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/fe_gem_%j.out
#SBATCH --error=logs/fe_gem_%j.err
cd ~/LLM_Project
source py311_gemma/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_think_simple.py --model models/gemma-4-12B-it --backend transformers --dataset data/final_eval_v7_dataset --split validation --max_new_tokens 12000 --max_seq_length 24000 --temperature 0.7 --top_p 0.95 --top_k 64 --out_dir results/final_eval_gemma
