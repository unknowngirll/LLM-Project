import os
import re
import csv
import argparse
from datasets import load_from_disk
from unsloth import FastModel
from unsloth.chat_templates import get_chat_template, standardize_data_formats
from transformers import GenerationMixin, AutoTokenizer

print("Loaded libraries")

# -----------------------------
# Argument parsing
# -----------------------------


parser = argparse.ArgumentParser(description="Run inference on eval dataset.")
parser.add_argument("-m", "--model", type=str, required=True, help="Path to model directory")
parser.add_argument("--dataset", type=str, required=True, help="Path to the Hugging Face dataset (load_from_disk format)")
parser.add_argument("--batch-size", type=int, default=1, help="Batch size for inference")
parser.add_argument("--load-in-4bit", type=str, default="yes", choices=["yes","no"], help="Load model in 4bit quantization")
parser.add_argument("--keep-title", action="store_true", help="Keep '# title:' lines in user messages (default removes them)")
parser.add_argument("--keep-summary", action="store_true", help="Keep '# summary:' lines in user messages (default removes them)")
parser.add_argument("--output-dir", type=str, default="validation_results", help="Directory where validation results (TSV + raw) will be saved")
args = parser.parse_args()

print(args.model)

# -----------------------------
# Patch transformers caching (needed for Unsloth)
# -----------------------------
original_f = GenerationMixin._prepare_cache_for_generation
def patched_f(self, generation_config, model_kwargs, assistant_model, batch_size, max_cache_length, device):
    generation_config.cache_implementation = 'dynamic'
    return original_f(self, generation_config, model_kwargs, assistant_model, batch_size, max_cache_length, device)
GenerationMixin._prepare_cache_for_generation = patched_f

# -----------------------------
# Load model + tokenizer
# -----------------------------
if "magistral" in args.model.lower():
    # Magistral-specific workaround
    model, _ = FastModel.from_pretrained(
        model_name=args.model,
        max_seq_length=10048,
        load_in_4bit=(args.load_in_4bit.lower() == "yes"),
        load_in_8bit=False,
        full_finetuning=False,
    )
    # Force a text-only tokenizer to avoid image prompt issues
    tokenizer = AutoTokenizer.from_pretrained(args.model, use_fast=True)
    #tokenizer = get_chat_template(tokenizer, chat_template="mistral")
else:
    # Default behavior for other models
    model, tokenizer = FastModel.from_pretrained(
        model_name=args.model,
        max_seq_length=10000,
        load_in_4bit=(args.load_in_4bit.lower() == "yes"),
        load_in_8bit=False,
        full_finetuning=False,
    )
print("loaded model")

# -----------------------------
# Load predefined eval dataset
# -----------------------------
dataset = load_from_disk(args.dataset)
eval_dataset = dataset["validation"]

# Apply chat template + standardization
MODEL_TEMPLATES = {
    "llama-3.2": "llama-3.2",   # e.g. "Llama-3.2-3B-Instruct"
    "phi-4": "phi-4",           # Phi-4 reasoning/instruct
    "qwen3": "qwen3",           # Qwen3 uses ChatML-style ("qwen2" in Unsloth)
    "gemma-3": "gemma-3",
    "llama-instruct-3.1":"llama-3.1",
    "mistral":"mistral",
    "gpt-oss": "gptoss"
}

def pick_template(model_name: str) -> str:
    lname = model_name.lower()
    if "llama-3.2" in lname:
        return MODEL_TEMPLATES["llama-3.2"]
    elif "phi-4" in lname:
        return MODEL_TEMPLATES["phi-4"]
    elif "qwen3" in lname:
        return MODEL_TEMPLATES["qwen3"]
    elif "gemma-3" in lname:
        return MODEL_TEMPLATES["gemma-3"]
    elif "llama-instruct-3.1" in lname:
        return MODEL_TEMPLATES["llama-instruct-3.1"]
    elif "mistral" in lname:
        return MODEL_TEMPLATES["mistral"]
    elif "magistral" in lname:
        return MODEL_TEMPLATES["mistral"]
    elif "gpt-oss" in lname:
        return MODEL_TEMPLATES["gpt-oss"]
    else:
        return None  # fallback: let Unsloth guess

# Check if the model is Magistral
if not "magistral" in args.model.lower():
    # For other models, pick and apply the appropriate template
    template_name = pick_template(args.model)
    tokenizer = get_chat_template(tokenizer, chat_template=template_name)
    
#template_name = pick_template(args.model)
#tokenizer = get_chat_template(tokenizer, chat_template=template_name) 




def clean_metadata_from_messages(example):
    new_messages = []
    for msg in example["messages"]:
        if msg["role"] == "user":
            content = msg["content"]
            if not args.keep_title:
                content = re.sub(
                    r"^#\s*title:.*(?:\n|$)", "", content,
                    flags=re.MULTILINE | re.IGNORECASE
                )
            if not args.keep_summary:
                content = re.sub(
                    r"^#\s*summary:.*(?:\n|$)", "", content,
                    flags=re.MULTILINE | re.IGNORECASE
                )
            msg["content"] = content.strip()
        new_messages.append(msg)
    example["messages"] = new_messages
    return example

eval_dataset = eval_dataset.map(clean_metadata_from_messages)
eval_dataset = standardize_data_formats(eval_dataset)

# Add the Magistral thinking system prompt if using Magistral model
if "magistral" in args.model.lower():
    MAGISTRAL_SYSTEM_PROMPT = """First draft your thinking process (inner monologue) until you arrive at a response. Format your response using Markdown, and use LaTeX for any mathematical equations. Write both your thoughts and the response in the same language as the input.

Your thinking process must follow the template below:
[THINK]
Your thoughts or/and draft, like working through an exercise on scratch paper. Be as casual and as long as you want until you are confident to generate the response. Use the same language as the input.
[/THINK]

Here, provide a self-contained response."""

    def add_thinking_system_prompt(example):
        messages = example["messages"]
        # Check if there's already a system message
        if messages and messages[0]["role"] == "system":
            # Prepend to existing system message
            messages[0]["content"] = MAGISTRAL_SYSTEM_PROMPT + "\n\n" + messages[0]["content"]
        else:
            # Insert new system message at the beginning
            messages.insert(0, {"role": "system", "content": MAGISTRAL_SYSTEM_PROMPT})
        example["messages"] = messages
        return example

    eval_dataset = eval_dataset.map(add_thinking_system_prompt)

def formatting_prompts_func(examples):
    convos = examples["messages"]
    stripped_convos = []
    for convo in convos:
        # remove any assistant messages!
        convo = [msg for msg in convo if msg["role"] != "assistant"]
        stripped_convos.append(convo)
    texts = [
        tokenizer.apply_chat_template(
            convo,
            tokenize=False,
            add_generation_prompt=True,
        )
        for convo in stripped_convos
    ]
    return {"prompt": texts}

eval_dataset = eval_dataset.map(formatting_prompts_func, batched=True)
print(eval_dataset[0]["prompt"])
# -----------------------------
# Generation parameters
# -----------------------------
generation_kwargs = {
    "max_new_tokens": 12000,
    "do_sample": False,
    "temperature": 0,
    "top_p": 0.9,
    "repetition_penalty": 1.1,
}

# -----------------------------
# LLM output parser
# -----------------------------
def parse_llm_output(output_text):
    groups = []
    if "Group 1:" in output_text:
        output_text = "Group 1:" + output_text.split("Group 1:", 1)[1]
    group_blocks = re.split(r"\n*Group \d+:", output_text)
    for block in group_blocks:
        if not block.strip():
            continue
        cell_line = re.search(r"Cell line: (.*)", block)
        pert_type = re.search(r"Perturbation method: (.*)", block)
        gene = re.search(r"Target gene: (.*)", block)
        control = re.search(r"Control: (.*)", block)
        case = re.search(r"Case: (.*)", block)
        if pert_type and gene and control and case:
            groups.append({
                "cell_line": cell_line.group(1).strip() if cell_line else "",
                "pert_type": pert_type.group(1).strip(),
                "perturbed_gene": gene.group(1).strip(),
                "control": [x.strip() for x in control.group(1).split(",")],
                "case": [x.strip() for x in case.group(1).split(",")]
            })
    return groups
# -----------------------------
# Generation function
# -----------------------------
def generate_batch(batch):
    prompts = batch["prompt"]
    inputs = tokenizer(prompts, return_tensors="pt", padding=True, truncation=True)
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    outputs = model.generate(
        **inputs,
        max_new_tokens=generation_kwargs["max_new_tokens"],
        do_sample=generation_kwargs["do_sample"],
        temperature=generation_kwargs["temperature"],
        top_p=generation_kwargs["top_p"],
        repetition_penalty=generation_kwargs["repetition_penalty"],
    )

    # Detect if it's a Magistral model
    is_magistral = "magistral" in args.model.lower()

    texts = []
    for i, output_ids in enumerate(outputs):
        prompt_len = len(inputs["input_ids"][i])
        generated_ids = output_ids[prompt_len:]
        
        # Use skip_special_tokens=False if Magistral, True otherwise
        text = tokenizer.decode(generated_ids, skip_special_tokens=not is_magistral)
        
        # Remove </s> tags if Magistral
        if is_magistral:
            text = text.replace("</s>", "")
        
        texts.append(text)
    return {"raw_output": texts}

# -----------------------------
# Run inference
# -----------------------------
eval_dataset = eval_dataset.map(generate_batch, batched=True, batch_size=args.batch_size)

# -----------------------------
# Save outputs
# -----------------------------
result_dir = args.output_dir
os.makedirs(result_dir, exist_ok=True)

# sanitize model name for filenames
safe_model_name = args.model.strip("./").replace("/", "_")

# Add flags for title/summary retention to output filenames
keep_flags = []
if args.keep_title:
    keep_flags.append("keeptitle")
if args.keep_summary:
    keep_flags.append("keepsummary")

flag_suffix = ""
if keep_flags:
    flag_suffix = "_" + "_".join(keep_flags)    
    

for i, record in enumerate(eval_dataset):
    output_text = record["raw_output"]
    if isinstance(output_text, list):
        output_text = output_text[0]

    # Save raw (unmodified) LLM output before stripping <think> blocks
    accession = record.get("metadata", {}).get("accession", f"sample{i}")
    
    # Include flag suffix in filenames
    outpath = os.path.join(result_dir, f"{accession}_{safe_model_name}{flag_suffix}.tsv")
    raw_outpath = os.path.join(result_dir, f"{accession}_{safe_model_name}{flag_suffix}_raw.txt")
    with open(raw_outpath, "w", encoding="utf-8") as f_raw:
        f_raw.write(output_text.strip())
    print(f"Saved raw LLM output to {raw_outpath}")

    # Clean the output for parsing
    cleaned_output = re.sub(r"<think>.*?</think>|\[THINK\].*?\[/THINK\]", "", output_text, flags=re.DOTALL).strip()

    pred_groups = parse_llm_output(cleaned_output)

    # Save parsed TSV output
    with open(outpath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, delimiter="\t")
        writer.writerow(["cell_line", "pert_type", "perturbed_gene", "control", "case"])
        for group in pred_groups:
            writer.writerow([
                group["cell_line"],
                group["pert_type"],
                group["perturbed_gene"],
                ",".join(group["control"]),
                ",".join(group["case"])
            ])
    print(f"Saved {len(pred_groups)} parsed groups to {outpath}")


