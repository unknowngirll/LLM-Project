import torch
import json
import random
import re
from pathlib import Path
from transformers import pipeline

# Configuration
MODEL_PATH = "./models/Qwen"
ABSTRACTS_FILE = "./Pubmed_abstracts/all_abstracts_texts.txt"
SYSTEM_PROMPT_PATH = "./Prompts/system_prompt.txt"
USER_PROMPT_PATH = "./Prompts/user_prompts.txt"
OUTPUT_FILE = "qwen_extraction_results.json"
CHECKPOINT_FILE = "qwen_results_checkpoint.jsonl"
BATCH_SIZE = 4 

def clean_json_response(text):
    return re.sub(r'```json|```', '', text).strip()

def main():
    print("Loading prompt files...")
    system_prompt = Path(SYSTEM_PROMPT_PATH).read_text(encoding="utf-8").strip()
    user_template = Path(USER_PROMPT_PATH).read_text(encoding="utf-8").strip()

    print("Initializing Model on GPU...")
    pipe = pipeline(
        "text-generation",
        model=MODEL_PATH,
        torch_dtype=torch.bfloat16,
        device_map="auto"
    )

    print("Parsing full articles (Multi-line logic)...")
    raw_text = Path(ABSTRACTS_FILE).read_text(encoding="utf-8")
    # Split by pattern: Newline followed by a number and a period (e.g., "\n184.")
    articles = [a.strip() for a in re.split(r'\n(?=\d+\.\s)', raw_text) if len(a.strip()) > 100]
    
    sample_size = min(100, len(articles))
    sampled_articles = random.sample(articles, sample_size)
    print(f"Total articles found: {len(articles)}. Processing {sample_size} samples.")

    results = []
    # Process in batches for speed
    for i in range(0, len(sampled_articles), BATCH_SIZE):
        batch = sampled_articles[i : i + BATCH_SIZE]
        batch_prompts = []
        
        for art in batch:
            msg = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_template.replace("{abstract}", art)}
            ]
            batch_prompts.append(msg)

        try:
            outputs = pipe(batch_prompts, max_new_tokens=1000, return_full_text=False)
            
            for j, out in enumerate(outputs):
                record = {
                    "id": i + j + 1,
                    "model_output": clean_json_response(out[0]['generated_text']),
                    "input_snippet": batch[j][:100] + "..." 
                }
                results.append(record)
                # Checkpoint save
                with open(CHECKPOINT_FILE, "a", encoding="utf-8") as cp_f:
                    cp_f.write(json.dumps(record, ensure_ascii=False) + "\n")

            print(f"Progress: {i + len(batch)}/{sample_size}")

        except Exception as e:
            print(f"Error in batch starting at {i}: {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    print(f"Success! Final file: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
