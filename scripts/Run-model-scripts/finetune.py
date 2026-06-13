# -*- coding: utf-8 -*-
import os
import csv
import pickle
import torch
import argparse
import shutil
import re
from datasets import Dataset
from datasets import load_from_disk
from unsloth import FastModel
from unsloth.chat_templates import get_chat_template, standardize_data_formats, train_on_responses_only
from trl import SFTTrainer, SFTConfig
from transformers import TrainerCallback

# ========================
# Command line arguments
# ========================
parser = argparse.ArgumentParser(description="Train a Qwen model with QLoRA.")
parser.add_argument("--model_name", type=str, required=True)
parser.add_argument("--load_in_4bit", action="store_true")
parser.add_argument("--lora_rank", type=int, default=32)
parser.add_argument("--lora_alpha", type=int, default=32)
parser.add_argument("--learning_rate", type=float, default=2e-4)
parser.add_argument("--seed", type=int, default=3407)
parser.add_argument("--num_epochs", type=int, default=3)
parser.add_argument("--max_seq_length", type=int, default=10048)
parser.add_argument("--output_dir", type=str, default="finetuned_models")
parser.add_argument("--per_device_batch_size", type=int, default=4,
                    help="Batch size per device (default: 4)")
parser.add_argument("--gradient_accumulation_steps", type=int, default=4,
                    help="Number of gradient accumulation steps (default: 4)")
args = parser.parse_args()




# ========================
# Load model
# ========================
model, tokenizer = FastModel.from_pretrained(
    model_name=args.model_name,
    max_seq_length=args.max_seq_length,
    load_in_4bit=args.load_in_4bit,
    load_in_8bit=False,
    full_finetuning=False,
)

model = FastModel.get_peft_model(
    model,
    r=args.lora_rank,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ],
    lora_alpha=args.lora_alpha,
    lora_dropout=0,
    bias="none",
    use_gradient_checkpointing="unsloth",
    random_state=args.seed,
    use_rslora=False,
    loftq_config=None
)

# ========================
# Load dataset
# ========================
dataset = load_from_disk("gene_perturbation_training")


def clean_metadata_from_messages(example):
    new_messages = []
    for msg in example["messages"]:
        if msg["role"] == "user":
            content = msg["content"]
            content = re.sub(
                r"^#\s*summary:.*(?:\n|$)", "", content,
                flags=re.MULTILINE | re.IGNORECASE
            )
            msg["content"] = content.strip()
        new_messages.append(msg)
    example["messages"] = new_messages
    return example

# Remove the summary from the metadata, keep the title
dataset = dataset.map(clean_metadata_from_messages)

# Access predefined splits directly
train_dataset = dataset["train"]
eval_dataset = dataset["validation"]

# Apply chat template + standardization
tokenizer = get_chat_template(tokenizer, chat_template="qwen3-instruct")
train_dataset = standardize_data_formats(train_dataset)
eval_dataset = standardize_data_formats(eval_dataset)

def formatting_prompts_func(examples):
    convos = examples["messages"]
    texts = [
        tokenizer.apply_chat_template(convo, tokenize=False, add_generation_prompt=False)
        for convo in convos
    ]
    return {"text": texts}

train_dataset = train_dataset.map(formatting_prompts_func, batched=True)
eval_dataset = eval_dataset.map(formatting_prompts_func, batched=True)

print(f"Train size: {len(train_dataset)}, Validation size: {len(eval_dataset)}")


# ========================
# Calculate dynamic warmup steps
# ========================
num_train_examples = len(train_dataset)
per_device_batch_size = args.per_device_batch_size
gradient_accumulation_steps = args.gradient_accumulation_steps
num_epochs = args.num_epochs
num_gpus = torch.cuda.device_count() if torch.cuda.is_available() else 1

steps_per_epoch = num_train_examples // (per_device_batch_size * num_gpus * gradient_accumulation_steps)
total_steps = steps_per_epoch * num_epochs

warmup_ratio = 0.05  # 5% of total training steps
warmup_steps = int(total_steps * warmup_ratio)

print(f"Total steps: {total_steps}, Warmup steps (auto): {warmup_steps}")

# ========================
# Trainer setup
# ========================
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=train_dataset,
    eval_dataset=eval_dataset,
    args=SFTConfig(
        dataset_text_field="text",
        per_device_train_batch_size=args.per_device_batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        warmup_steps=warmup_steps,
        num_train_epochs=args.num_epochs,
        learning_rate=args.learning_rate,
        eval_strategy="steps",
        eval_steps=20,
        save_strategy="no",
        max_length=args.max_seq_length,
        logging_steps=1,
        optim="adamw_8bit",
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=args.seed,
        report_to="none",
    ),
)

trainer = train_on_responses_only(
    trainer,
    instruction_part="<|im_start|>user\n",
    response_part="<|im_start|>assistant\n",
)

# ========================
# Callback for saving
# ========================
class SaveAndLogCallback(TrainerCallback):
    def __init__(self, model, tokenizer, args):
        self.model = model
        self.tokenizer = tokenizer
        self.args = args
        self.output_dir = args.output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Master log file for all steps across epochs
        self.master_log_file = os.path.join(self.output_dir, "step_metrics.csv")
        if not os.path.exists(self.master_log_file):
            with open(self.master_log_file, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["step", "epoch", "train_loss", "eval_loss"])

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is None:
            return
        with open(self.master_log_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([state.global_step, state.epoch, logs.get("loss"), logs.get("eval_loss")])

    def on_epoch_end(self, args, state, control, **kwargs):
        epoch = int(state.epoch)
        print(f"Epoch {epoch} finished — saving models and metrics...")

        # Base name includes all hyperparameters
        base_name = (
            f"{self.args.model_name.replace('/', '_')}"
            f"_r{self.args.lora_rank}"
            f"_alpha{self.args.lora_alpha}"
            f"_lr{self.args.learning_rate}"
            f"_seed{self.args.seed}"
            f"_epoch{epoch}"
        )

        # LoRA checkpoint
        lora_dir = os.path.join(self.output_dir, f"{base_name}_lora")
        self.model.save_pretrained(lora_dir)
        self.tokenizer.save_pretrained(lora_dir)

        # Merged checkpoint
        merged_dir = os.path.join(self.output_dir, f"{base_name}_merged")
        self.model.save_pretrained_merged(
            merged_dir,
            self.tokenizer,
            save_method="merged_16bit"
        )

        # Save epoch-specific metrics copy
        epoch_metrics_file = os.path.join(self.output_dir, f"{base_name}_metrics.csv")
        # Copy master log so far
        shutil.copy(self.master_log_file, epoch_metrics_file)

        print(f"Saved LoRA, merged model, and metrics for epoch {epoch}")

# Add callback with access to argparse arguments
trainer.add_callback(SaveAndLogCallback(model, tokenizer, args=args))
trainer_stats = trainer.train()

# ========================
# Memory stats
# ========================
used_memory = round(torch.cuda.max_memory_reserved() / 1024 / 1024 / 1024, 3)
gpu_stats = torch.cuda.get_device_properties(0)
max_memory = round(gpu_stats.total_memory / 1024 / 1024 / 1024, 3)
used_percentage = round(used_memory / max_memory * 100, 3)
print(f"Peak reserved memory = {used_memory} GB ({used_percentage} % of max memory)")


