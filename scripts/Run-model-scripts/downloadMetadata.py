import GEOparse
import pandas as pd
import time
import humanize
import os
import glob
import argparse

# -----------------------------
# Fetch GSE metadata
# -----------------------------
def fetch_gse_metadata(gse_id):
    print(f"Fetching metadata for {gse_id}...")
    start_time = time.time()

    gse = GEOparse.get_GEO(geo=gse_id, destdir="./", silent=True)

    duration = time.time() - start_time
    print(f"Metadata fetched in {humanize.precisedelta(duration)}")

    # Get experiment-level metadata
    gse_title = gse.metadata.get("title", [""])[0]
    gse_summary = gse.metadata.get("summary", [""])[0]
    overall_design = gse.metadata.get("overall_design", [""])[0]

    # Header lines
    table_lines = [
        f"# title: {gse_title}",
        f"# summary: {gse_summary}",
        f"# design: {overall_design}",
        "GSM\ttitle\tdescription\tsource\tcharacteristics\torganism\tmolecule\tlibrary_strategy\tlibrary_source\tlibrary_selection"
    ]

    # Each sample (GSM)
    for gsm_name, gsm in gse.gsms.items():
        title = gsm.metadata.get("title", [""])[0]
        desc = gsm.metadata.get("description", [""])[0]
        source = gsm.metadata.get("source_name_ch1", [""])[0]
        organism = gsm.metadata.get("organism_ch1", [""])[0]
        characteristics = gsm.metadata.get("characteristics_ch1", [""])
        characteristics_str = "; ".join(characteristics)

        molecule = gsm.metadata.get("molecule_ch1", [""])[0]
        lib_strategy = gsm.metadata.get("library_strategy", [""])[0]
        lib_source = gsm.metadata.get("library_source", [""])[0]
        lib_selection = gsm.metadata.get("library_selection", [""])[0]

        table_lines.append(
            f"{gsm_name}\t{title}\t{desc}\t{source}\t{characteristics_str}\t{organism}\t{molecule}\t{lib_strategy}\t{lib_source}\t{lib_selection}"
        )

    return "\n".join(table_lines)


# -----------------------------
# Main script
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="Fetch GEO metadata for a list of GSE accession numbers.")
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the input text file (must contain a column named 'accession')."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to the output directory where metadata TSV files will be saved."
    )
    args = parser.parse_args()

    input_file = args.input
    output_dir = args.output

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Load accession numbers
    df = pd.read_csv(input_file, sep="\t")
    if "accession" not in df.columns:
        raise ValueError("Input file must contain a column named 'accession'.")

    unique_accessions = df["accession"].drop_duplicates()

    for accession in unique_accessions:
        output_file = os.path.join(output_dir, f"{accession}_metadata.tsv")

        if os.path.exists(output_file):
            print(f"Skipping {accession} (already exists)")
            continue

        try:
            tsv_string = fetch_gse_metadata(accession)
            with open(output_file, "w") as f:
                f.write(tsv_string)
            print(f"Saved: {output_file}")

        except Exception as e:
            print(f"Failed to process {accession}: {e}")

        finally:
            # Clean up temporary .soft files
            for f in glob.glob(f"{accession}*soft*"):
                try:
                    os.remove(f)
                    print(f"Cleaned up {f}")
                except Exception as e:
                    print(f"Warning: could not remove {f}: {e}")


# -----------------------------
# Entry point
# -----------------------------
if __name__ == "__main__":
    main()
