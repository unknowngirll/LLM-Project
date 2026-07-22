#!/bin/bash
#SBATCH --job-name=dl_mag_fix
#SBATCH --time=02:00:00
#SBATCH --mem=12G
#SBATCH --output=slurm_download_%j.out

echo "=== Activating Environment ==="
cd ~/LLM_Project
source py311/bin/activate

echo "=== Starting Safe Download ==="
mkdir -p data/models/Magistral-Small-2509

# اجرای دانلود در محیط پایتون اکتیو شده
huggingface-cli download "Magistral-Small-2509" --local-dir "data/models/Magistral-Small-2509" --local-dir-use-symlinks False

echo "=== Process Finished ==="
