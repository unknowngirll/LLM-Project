#!/bin/bash
#SBATCH --job-name=test_q36
#SBATCH --time=01:00:00
#SBATCH --mem=80G
#SBATCH --partition=gpu-h100
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --output=logs/test_q36_%j.out
#SBATCH --error=logs/test_q36_%j.err
cd ~/LLM_Project
source py311/bin/activate
export HF_HOME=~/data/hf_cache
export PYTORCH_ALLOC_CONF=expandable_segments:True
python infer_unsloth.py \
    --model unsloth/Qwen3.6-27B \
    --dataset data/split_dataset \
    --split validation \
    --limit 3 \
    --max_new_tokens 2000 \
    --max_seq_length 4096 \
    --load_in_4bit \
    --out_dir results/test_qwen36
