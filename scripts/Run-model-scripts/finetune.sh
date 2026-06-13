#!/bin/bash
#SBATCH --job-name=finetune
#SBATCH --mem=40G
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=2
#SBATCH --array 10%1    # 12 total combinations

# Define all combinations:
# Format: "seed rank lr"
COMBINATIONS=(
  "12345 16 2e-4"
  "12345 16 5e-5"
  "12345 32 2e-4"
  "12345 32 5e-5"
  "2024 16 2e-4"
  "2024 16 5e-5"
  "2024 32 2e-4"
  "2024 32 5e-5"
  "3407 16 2e-4"
  "3407 16 5e-5"
  "3407 32 2e-4"
  "3407 32 5e-5"
)

# Extract parameters for this array task
PARAMS=(${COMBINATIONS[$SLURM_ARRAY_TASK_ID]})
SEED=${PARAMS[0]}
RANK=${PARAMS[1]}
LR=${PARAMS[2]}



echo ">>> Running combination $SLURM_ARRAY_TASK_ID: SEED=$SEED | RANK=$RANK | LR=$LR"



# Run training
singularity exec \
  -B "$(pwd -P)" \
  -B "/mnt/hc-storage/modules/compiler/gcc/12.1.0/bin/" \
  --env CC=/usr/bin/gcc \
  --env CXX=/usr/bin/g++ \
  --nv \
  Singularity_unsloth.img \
  python finetune_batch.py \
    --model_name "./Qwen3-30B-A3B-Instruct-2507" \
    --lora_rank $RANK \
    --lora_alpha $RANK \
    --learning_rate $LR \
    --seed $SEED \
    --num_epochs 3 \
    --per_device_batch_size 1 \
    --gradient_accumulation_steps 16 \
    --load_in_4bit

