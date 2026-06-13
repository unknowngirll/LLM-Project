import pandas as pd
from pathlib import Path
from datasets import Dataset, DatasetDict
import argparse

def build_dataset(metadata_dir, output_name, training, ground_truth_file, system_prompt_file, user_prompt_file):
    # ----------------------------
    # Load ground truth
    # ----------------------------
    rnaseq_df = pd.read_csv(ground_truth_file, sep="\t")

    # Map GSE to assistant answer
    gse_to_answer = {}
    for gse_id, group_df in rnaseq_df.groupby("accession"):
        lines = []
        for idx, row in enumerate(group_df.itertuples(), start=1):
            lines.append(f"Group {idx}:")
            lines.append(f"  Cell line: {row.cell_line}")
            lines.append(f"  Perturbation method: {row.pert_type}")
            lines.append(f"  Target gene: {row.pert_symbol}")
            lines.append(f"  Control: {row.controlSamples}")
            lines.append(f"  Case: {row.caseSamples}")
        gse_to_answer[gse_id] = "\n".join(lines)

    # ----------------------------
    # Load prompt templates
    # ----------------------------
    system_prompt = Path(system_prompt_file).read_text().strip()
    user_prompt_template = Path(user_prompt_file).read_text().strip()

    # ----------------------------
    # Build records
    # ----------------------------
    records = []
    metadata_path = Path(metadata_dir)

    for tsv_file in metadata_path.glob("*_metadata.tsv"):
        gse_id = tsv_file.stem.split("_")[0]
        table_str = tsv_file.read_text().strip()

        user_prompt = user_prompt_template.format(table=table_str)
        assistant_answer = gse_to_answer.get(gse_id, "No valid groups found")

        records.append({
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
                {"role": "assistant", "content": assistant_answer}
            ],
            "metadata": {"accession": gse_id}
        })

    # ----------------------------
    # Create Hugging Face dataset
    # ----------------------------
    dataset = Dataset.from_list(records)

    if training:
        print("Preparing training/validation split...")
        dataset = dataset.shuffle(seed=42)
        split = dataset.train_test_split(test_size=0.2, seed=42)
        dataset_dict = DatasetDict({
            "train": split["train"],
            "validation": split["test"]
        })
    else:
        print("Preparing validation-only dataset...")
        dataset_dict = DatasetDict({
            "validation": dataset
        })

    # ----------------------------
    # Save to disk
    # ----------------------------
    output_path = Path(output_name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset_dict.save_to_disk(output_path)
    print(f"Dataset saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Build a Hugging Face dataset from GEO metadata TSV files."
    )
    parser.add_argument("--metadata_dir", required=True,
                        help="Directory containing *_metadata.tsv files.")
    parser.add_argument("--output_name", required=True,
                        help="Output directory name for the Hugging Face dataset.")
    parser.add_argument("--ground_truth_file", required=True,
                        help="Path to ground truth TSV file (must have an 'accession' column).")
    parser.add_argument("--system_prompt_file", required=True,
                        help="Path to text file containing the system prompt.")
    parser.add_argument("--user_prompt_file", required=True,
                        help="Path to text file containing the user prompt template (use {table} placeholder).")
    parser.add_argument("--training", action="store_true",
                        help="If set, create a shuffled train/validation split. Otherwise, only create a validation set.")

    args = parser.parse_args()

    build_dataset(
        metadata_dir=args.metadata_dir,
        output_name=args.output_name,
        training=args.training,
        ground_truth_file=args.ground_truth_file,
        system_prompt_file=args.system_prompt_file,
        user_prompt_file=args.user_prompt_file,
    )


if __name__ == "__main__":
    main()
