from datasets import load_from_disk, DatasetDict, concatenate_datasets
from pathlib import Path

print("Loading existing datasets...")
ds_pos = load_from_disk("data/split_dataset")["validation"]
ds_neg = load_from_disk("data/negatives_dataset")["validation"]
ds_all = concatenate_datasets([ds_pos, ds_neg])

sys_prompt = Path("Prompts_v4/system_prompt.txt").read_text(encoding="utf-8").strip()
user_tmpl = Path("Prompts_v4/user_prompt.txt").read_text(encoding="utf-8").strip()

def update_prompts(ex):
    pmid = ex["metadata"]["pmid"]
    abs_text = Path(f"data/abstracts/{pmid}.txt").read_text(encoding="utf-8").strip()
    user_prompt = user_tmpl.replace("{abstract}", abs_text)
    
    asst = [m for m in ex["messages"] if m["role"] == "assistant"][0]
    ex["messages"] = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": user_prompt},
        asst
    ]
    return ex

print("Applying V3 prompts to all 267 abstracts...")
ds_v3 = ds_all.map(update_prompts)
out_path = "data/eval_v4_dataset"
DatasetDict({"validation": ds_v3}).save_to_disk(out_path)
print(f"Saved {len(ds_v3)} records to {out_path}")
