#!/bin/bash
#SBATCH --job-name=eval_models
#SBATCH --time=48:00:00
#SBATCH --mem=50G
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --array=0-11%1
set -euo pipefail

models=(
"Llama-3.2-3B-Instruct"
    "phi-4"
    "Qwen3-4B-Instruct-2507"
    "Qwen3-30B-A3B-Instruct-2507"
    "Qwen3-8B"
    "Qwen3-14B"
     "Qwen3-4B-Thinking-2507"
      "gemma-3-4b-it"
"gemma-3-27b-it"
"llama-instruct-3.1-8b"
"mistral-7b-instruct-v0.3"
"Magistral-Small-2509"
)

model_idx=$SLURM_ARRAY_TASK_ID
model=${models[$model_idx]}
    # Default: no 4-bit
    load_in_4bit="no"
    case "$model" in
         *Magistral*|*magistral*|*20B*|*20b*|*27B*|*27b*|*30B*|*30b*)
            load_in_4bit="yes"
            ;;
    esac
echo "Running model: $model"
# -----------------------------
# Run Python script
# -----------------------------
singularity exec \
  -B `pwd -P` \
  -B "/mnt/hc-storage/modules/compiler/gcc/12.1.0/bin/" \
    --env CC=/usr/bin/gcc \
  --env CXX=/usr/bin/g++ \
  --nv \
  Singularity_unsloth.img \
  python runModels.py \
    --m "$model" \
    --load-in-4bit "$load_in_4bit" \
    --batch-size 1 \
    --output-dir "results/validation/$model" \
    --keep-title

