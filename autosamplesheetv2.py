#!/usr/bin/env python3
"""
NovaSeq X SampleSheet generator.

UPDATED FEATURES:
- Input file MUST contain a header.
- Supports 1, 2, or 3 columns:
    sample_name,index_name,lane
- Lane column is optional but header is required.
- If lane is provided → overrides automatic lane cycling.
- Lane must be integer 1–8.
- Wrap-around index assignment.
- Extensive validation for non-technical users.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
import pandas as pd


REQUIRED_INDEX_COLUMNS = {
    "Index_Name",
    "i7_Bases_for_Sample_Sheet",
    "i5_Bases_for_Sample_Sheet_in_Forward_Orientation",
}

REQUIRED_INPUT_HEADER = ["sample_name", "index_name", "lane"]


class SampleSheetError(Exception):
    pass


def load_index_table(index_file: str) -> pd.DataFrame:
    df = pd.read_csv(index_file)

    missing = REQUIRED_INDEX_COLUMNS - set(df.columns)
    if missing:
        raise SampleSheetError(f"Missing index columns: {missing}")

    return df


def validate_lane(value, sample):
    if pd.isna(value):
        return None

    if not str(value).isdigit():
        raise SampleSheetError(f"Lane for sample '{sample}' must be a number (1–8).")

    lane = int(value)
    if not 1 <= lane <= 8:
        raise SampleSheetError(f"Lane for sample '{sample}' must be between 1 and 8.")

    return lane


def get_wrapped_indices(index_names, start_index, n):
    if start_index not in index_names:
        raise SampleSheetError(f"Start index '{start_index}' not found.")

    start_pos = index_names.index(start_index)
    return [index_names[(start_pos + i) % len(index_names)] for i in range(n)]


def parse_input_file(file_path, index_names, start_index=None):
    df = pd.read_csv(file_path)

    # Validate header
    header = list(df.columns)

    if "sample_name" not in header:
        raise SampleSheetError("Input file must contain column: sample_name")

    # Normalize missing columns
    if "index_name" not in header:
        df["index_name"] = None
    if "lane" not in header:
        df["lane"] = None

    samples = df["sample_name"].tolist()

    if len(set(samples)) != len(samples):
        raise SampleSheetError("Duplicate sample names detected.")

    # Case 1: automatic index assignment
    if df["index_name"].isnull().all():
        if not start_index:
            raise SampleSheetError("Start index required when index_name column is empty.")

        indices = get_wrapped_indices(index_names, start_index, len(samples))
        df["index_name"] = indices

    # Validate index names
    for s, idx in zip(df["sample_name"], df["index_name"]):
        if idx not in index_names:
            raise SampleSheetError(f"Invalid index '{idx}' for sample '{s}'.")

    # Validate lanes
    df["lane"] = [validate_lane(v, s) for v, s in zip(df["lane"], df["sample_name"])]

    return df


def write_samplesheet(output, run_name, df, index_lookup):
    with open(output, "w") as f:
        f.write("[Header],\n")
        f.write("FileFormatVersion,2\n")
        f.write(f"RunName,{run_name}\n")
        f.write("InstrumentPlatform,NovaSeqXSeries\n")
        f.write("IndexOrientation,Forward\n\n")

        f.write("[Reads]\n151\n151\n10\n10\n\n")

        f.write("[Sequencing_Settings]\nLibraryPrepKits,IlluminaDNAPrep\n\n")

        f.write("[BCLConvert_Settings]\n")
        f.write("SoftwareVersion,4.3.16\n")
        f.write("AdapterRead1,CTGTCTCTTATACACATCT\n")
        f.write("AdapterRead2,CTGTCTCTTATACACATCT\n")
        f.write("OverrideCycles,Y151;I10;I10;Y151\n")
        f.write("FastqCompressionFormat,gzip\n")
        f.write("GenerateFastqcMetrics,true\n\n")

        f.write("[BCLConvert_Data]\n")
        f.write("Lane,Sample_ID,Index,Index2\n")

        for i, row in df.iterrows():
            lane = row["lane"] if row["lane"] else (i % 8) + 1
            idx = index_lookup[row["index_name"]]

            f.write(
                f"{lane},{row['sample_name']},{idx['i7_Bases_for_Sample_Sheet']},{idx['i5_Bases_for_Sample_Sheet_in_Forward_Orientation']}\n"
            )


# ---------------- CLI ----------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--index-file","-i", required=True, help="Illumina index set CSV")
    parser.add_argument("--sample-config","-s", required=True, help="Sample input file")
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

    args = parser.parse_args()
    
    if args.run_name is None:
        print("Warning: No Runname given, used default XResXX, please change manually")    

    index_df = load_index_table(args.index_file)
    index_names = index_df["Index_Name"].tolist()
    index_lookup = index_df.set_index("Index_Name").to_dict(orient="index")

    print(index_lookup)

    df = parse_input_file(args.sample_config, index_names, args.start_index)

    write_samplesheet(args.output, args.run_name, df, index_lookup)

    print("SampleSheet created successfully.")


if __name__ == "__main__":
    try:
        main()
    except SampleSheetError as e:
        print(f"ERROR: {e}")
        sys.exit(1)


"""
======================== README ========================

NovaSeq SampleSheet Generator

This tool creates a valid Illumina NovaSeq SampleSheet.csv file.

----------------------------------------
1. REQUIREMENTS
----------------------------------------
- Python 3.8 or higher
- pandas

Install pandas if needed:
    pip install pandas

----------------------------------------
2. INPUT FILES
----------------------------------------

A) Index file (provided by Illumina)
   Example: set_A-D_index_adapters.csv

B) Sample file (YOU create this)

This file MUST contain a header.

Valid formats:

1. Automatic index assignment:

sample_name
SampleA
SampleB
SampleC

→ Requires --start-index

2. Manual index assignment:

sample_name,index_name
SampleA,UDP0001
SampleB,UDP0002

3. Optional lane assignment:

sample_name,index_name,lane
SampleA,UDP0001,1
SampleB,UDP0002,2
SampleC,UDP0003,8

Rules:
- lane must be 1–8
- leave lane empty to auto-assign

----------------------------------------
3. RUNNING THE SCRIPT
----------------------------------------

Basic usage:

python script.py \
  --index-file set_A_index_adapters.csv \
  --input-file samples.csv \
  --run-name MyRun \
  --start-index UDP0005

----------------------------------------
4. OUTPUT
----------------------------------------

Creates:
    SampleSheet.csv

Ready for direct upload to Illumina system.

----------------------------------------
5. COMMON ERRORS
----------------------------------------

ERROR: Missing index columns
→ Wrong index file

ERROR: Start index not found
→ Typo in index name

ERROR: Duplicate sample names
→ Each sample must be unique

ERROR: Lane must be between 1 and 8
→ Fix lane column

----------------------------------------
6. TIPS
----------------------------------------

- Use Excel to prepare sample sheet, then export as CSV
- Double-check index names carefully
- Keep original index file unchanged

========================================================
"""
