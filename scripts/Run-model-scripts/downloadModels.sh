#!/bin/bash

# List of models to download
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
    "gpt-oss-20b-unsloth-bnb-4bit"
)

# Set and create a base directory for downloads
BASE_DIR="data/models"
mkdir -p "$BASE_DIR"

# Loop through and download each model
for model in "${models[@]}"; do

    echo "Downloading model: $model"

    local_dir="${BASE_DIR}/${model}"
    mkdir -p "$local_dir"

    huggingface-cli download "$model" --local-dir "$local_dir" --local-dir-use-symlinks False

done

