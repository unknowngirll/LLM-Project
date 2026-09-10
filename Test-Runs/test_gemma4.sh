#!/bin/bash
#SBATCH --job-name=t_gem4
#SBATCH --time=01:30:00
#SBATCH --mem=64G
#SBATCH --partition=gpu-h100,gpu-l40s,gpu-a-lowsmall
#SBATCH --gres=gpu:1
#SBATCH --output=logs/t_gem4_%j.out
#SBATCH --error=logs/t_gem4_%j.err
cd ~/LLM_Project
source py311_gemma/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_think_simple.py --model models/gemma-4-12B-it --backend transformers --dataset data/eval_v6_dataset --split validation --limit 3 --max_new_tokens 12000 --max_seq_length 24000 --temperature 1.0 --top_p 0.95 --top_k 64 --out_dir results/TEST_gemma4
