#!/bin/bash
#SBATCH --job-name=s_q36
#SBATCH --time=06:00:00
#SBATCH --mem=96G
#SBATCH --partition=gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --output=logs/s_q36_%j.out
#SBATCH --error=logs/s_q36_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/scratch/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_think_simple.py --model unsloth/Qwen3.6-27B --backend unsloth --load_in_4bit --dataset data/eval_v3_dataset --split validation --max_new_tokens 16000 --max_seq_length 20000 --out_dir results/simple_36
