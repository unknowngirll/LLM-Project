#!/bin/bash
#SBATCH --job-name=eval_models
#SBATCH --time=1:00:00
#SBATCH --mem=30G
#SBATCH --partition=gpu-a100-lowbig
#SBATCH --gres=gpu:1

python run_model.py

