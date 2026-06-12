#!/usr/bin/env python3
"""
NovaSeq X SampleSheet generator.

Features:
- Accepts sample names from a 1-column text/CSV/TSV file + starting index.
- Accepts manual sample/index assignments from a 2-column text/CSV/TSV file.
- Assigns indices consecutively based on index CSV order.
- Wraps around to the first index after the last one.
- Cycles lane numbers from 1 to 8.
- Validates inputs with user-friendly error messages.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
import pandas as pd


REQUIRED_INDEX_COLUMNS = {
    "Index_Name",
    "i7_Bases_for_Sample_Sheet",
    "i5_Bases_for_Sample_Sheet_in_Forward_Orientation",
}


class SampleSheetError(Exception):
    """Custom exception for user-friendly errors."""


def load_index_table(index_file: str) -> pd.DataFrame:
    path = Path(index_file)
    if not path.exists():
        raise SampleSheetError(f"Index file not found: {index_file}")

    try:
        df = pd.read_csv(path,index_col=False)
    except Exception as e:
        raise SampleSheetError(f"Could not read index file: {e}")

    missing = REQUIRED_INDEX_COLUMNS - set(df.columns)
    if missing:
        raise SampleSheetError(
            "Index file is missing required columns: " + ", ".join(sorted(missing))
        )

    if df["Index_Name"].duplicated().any():
        duplicates = df.loc[df["Index_Name"].duplicated(), "Index_Name"].tolist()
        raise SampleSheetError(
            f"Duplicate Index_Name entries found: {', '.join(duplicates)}"
        )

    return df


def detect_delimiter(file_path: str) -> str:
    with open(file_path, "r", newline="") as f:
        sample = f.read(2048)
        try:
            return csv.Sniffer().sniff(sample, delimiters=",\t; ").delimiter
        except Exception:
            return None


def load_input_file(input_file: str) -> list[list[str]]:
    path = Path(input_file)
    if not path.exists():
        raise SampleSheetError(f"Input file not found: {input_file}")

    delimiter = detect_delimiter(input_file)

    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            if delimiter:
                parts = [p.strip() for p in line.split(delimiter) if p.strip()]
            else:
                parts = line.split()

            if not parts:
                continue

            rows.append(parts)

    if not rows:
        raise SampleSheetError("Input file is empty.")

    return rows


def get_wrapped_indices(index_names: list[str], start_index: str, n: int) -> list[str]:
    if start_index not in index_names:
        raise SampleSheetError(
            f"Start index '{start_index}' was not found in the index set."
        )

    start_pos = index_names.index(start_index)
    result = []

    for i in range(n):
        pos = (start_pos + i) % len(index_names)
        result.append(index_names[pos])

    return result


def parse_sample_assignments(rows: list[list[str]], index_names: list[str], start_index=None):
    assigned = {}

    col_counts = {len(row) for row in rows}
    if len(col_counts) > 1:
        raise SampleSheetError(
            "Input file contains inconsistent column counts. Use either one or two columns throughout."
        )

    n_cols = col_counts.pop()

    if n_cols == 1:
        if not start_index:
            raise SampleSheetError(
                "A start index must be provided when using a one-column sample file."
            )

        sample_ids = [row[0] for row in rows]

        duplicates = {s for s in sample_ids if sample_ids.count(s) > 1}
        if duplicates:
            raise SampleSheetError(
                "Duplicate sample IDs found: " + ", ".join(sorted(duplicates))
            )

        indices = get_wrapped_indices(index_names, start_index, len(sample_ids))
        assigned = dict(zip(sample_ids, indices))

    elif n_cols == 2:
        for row in rows:
            sample, index_name = row

            if sample in assigned:
                raise SampleSheetError(f"Duplicate sample ID in input: {sample}")

            if index_name not in index_names:
                raise SampleSheetError(
                    f"Index '{index_name}' for sample '{sample}' not found in index set."
                )

            assigned[sample] = index_name

    else:
        raise SampleSheetError(
            "Input file must contain either one column (sample IDs) or two columns (sample + index)."
        )

    return assigned


def write_samplesheet(
    output_file: str,
    run_name: str,
    assigned_indices: dict[str, str],
    index_lookup: dict,
    read1_cycles: int = 151,
    read2_cycles: int = 151,
    index1_cycles: int = 10,
    index2_cycles: int = 10,
):
    try:
        with open(output_file, "w", newline="") as f:
            f.write("[Header],\n")
            f.write("FileFormatVersion,2\n")
            f.write(f"RunName,{run_name}\n")
            f.write("InstrumentPlatform,NovaSeqXSeries\n")
            f.write("IndexOrientation,Forward\n\n")

            f.write("[Reads]\n")
            f.write(f"Read1Cycles,{read1_cycles}\n")
            f.write(f"Read2Cycles,{read2_cycles}\n")
            f.write(f"Index1Cycles,{index1_cycles}\n")
            f.write(f"Index2Cycles,{index2_cycles}\n\n")

            f.write("[Sequencing_Settings]\n")
            f.write("LibraryPrepKits,IlluminaDNAPrep\n\n")

            f.write("[BCLConvert_Settings]\n")
            f.write("SoftwareVersion,4.3.16\n")
            f.write("AdapterRead1,CTGTCTCTTATACACATCT\n")
            f.write("AdapterRead2,CTGTCTCTTATACACATCT\n")
            f.write(
                f"OverrideCycles,Y{read1_cycles};I{index1_cycles};I{index2_cycles};Y{read2_cycles}\n"
            )
            f.write("FastqCompressionFormat,gzip\n")
            f.write("GenerateFastqcMetrics,true\n\n")

            f.write("[BCLConvert_Data]\n")
            f.write("Lane,Sample_ID,Index,Index2\n")

            for i, (sample, index_name) in enumerate(assigned_indices.items()):
                lane = (i % 8) + 1
                row = index_lookup[index_name]
                f.write(
                    f"{lane},{sample},{row['i7_Bases_for_Sample_Sheet']},{row['i5_Bases_for_Sample_Sheet_in_Forward_Orientation']}\n"
                )
    except Exception as e:
        raise SampleSheetError(f"Could not write SampleSheet: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate an Illumina NovaSeq X SampleSheet.csv"
    )

    parser.add_argument("--index-file","-i", required=True, help="Illumina index set CSV")
    parser.add_argument("--sample-file","-s", required=True, help="Sample input file")
    parser.add_argument("--run-name","-r", default="XResXX", help="Run name")
    parser.add_argument(
        "--start-index",
        help="Start index for automatic assignment (required for one-column input)",
    )
    parser.add_argument(
        "--output","-o",
        default="SampleSheet.csv",
        help="Output SampleSheet file (default: SampleSheet.csv)",
    )
    if args.run_name is None:
        print("Warning: No Runname given, used default XResXX, please change manually")

    args = parser.parse_args()

    if Path(args.output).exists():
        print(f"Warning: output file '{args.output}' already exists and will be overwritten.")

    index_df = load_index_table(args.index_file)
    index_names = index_df["Index_Name"].tolist()
    index_lookup = index_df.set_index("Index_Name").to_dict(orient="index")

    rows = load_input_file(args.sample_file)
    assignments = parse_sample_assignments(rows, index_names, args.start_index)

    write_samplesheet(
        output_file=args.output,
        run_name=args.run_name,
        assigned_indices=assignments,
        index_lookup=index_lookup,
    )

    print(f"SampleSheet successfully written to: {args.output}")
    print(f"Total samples: {len(assignments)}")


if __name__ == "__main__":
    try:
        main()
    except SampleSheetError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nCancelled by user.", file=sys.stderr)
        sys.exit(130)
