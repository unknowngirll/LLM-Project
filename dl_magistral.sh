#!/bin/bash
#SBATCH --job-name=dl_mag
#SBATCH --time=02:00:00
#SBATCH --mem=8G

echo "=== Starting download on a compute node ==="
mkdir -p data/models/Magistral-Small-2509

# دستور مستقیم دانلود از هاگینگ‌فیس
huggingface-cli download "Magistral-Small-2509" --local-dir "data/models/Magistral-Small-2509" --local-dir-use-symlinks False

echo "=== Download Completed! ==="
