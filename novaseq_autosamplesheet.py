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
import collections
from datetime import datetime
import re

REQUIRED_INDEX_COLUMNS = {
    "Index_Name",
    "i7_Bases_for_Sample_Sheet",
    "i5_Bases_for_Sample_Sheet_in_Forward_Orientation",
}

REQUIRED_INPUT_HEADER = ["sample_name", "index_name", "lane"]


class SampleSheetError(Exception):
    pass

LOG_MESSAGES = []

def log(message):
    print(message)
    LOG_MESSAGES.append(message)

def write_log_file(log_file):
    with open(log_file, "w") as f:
        f.write(
            f"NovaSeq SampleSheet Generator Log\n"
            f"Generated: {datetime.now()}\n\n"
        )

        for message in LOG_MESSAGES:
            f.write(message + "\n")

def load_index_table(index_file: str) -> pd.DataFrame:
    df = pd.read_csv(index_file,index_col=False)

    missing = REQUIRED_INDEX_COLUMNS - set(df.columns)
    if missing:
        raise SampleSheetError(f"Missing index columns: {missing}")

    return df

def detect_delimiter(file_path: str) -> str:
    with open(file_path, "r", newline="") as f:
        sample = f.read(2048)
        try:
            return csv.Sniffer().sniff(sample, delimiters=",\t; ").delimiter
        except Exception:
            return None

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
    indexlist = [index_names[(start_pos + i) % len(index_names)] for i in range(n)]
    log(f"INFO: Automatic index assignment from {indexlist[0]} - {indexlist[-1]}")
    return indexlist

def validate_sample_names(df):

    reserved_words = {
        "all",
        "default",
        "none",
        "unknown",
        "undetermined",
        "stats",
        "reports"
    }

    warnings_found = False

    # Anything except letters, numbers, hyphen and underscore
    allowed_pattern = re.compile(r"^[A-Za-z0-9_-]+$")

    for sample in df["sample_name"]:

        issues = []

        sample_str = str(sample)

        # Reserved words
        if sample_str.lower() in reserved_words:
            issues.append("reserved word")

        # Length
        if len(sample_str) > 40:
            issues.append(
                f"length {len(sample_str)} exceeds recommended maximum of 40"
            )

        # Start/end characters
        if sample_str.startswith("-"):
            issues.append("starts with '-'")

        if sample_str.endswith("-"):
            issues.append("ends with '-'")

        if sample_str.startswith("_"):
            issues.append("starts with '_'")

        if sample_str.endswith("_"):
            issues.append("ends with '_'")

        # Allowed characters
        if not allowed_pattern.match(sample_str):

            invalid_chars = sorted(
                set(
                    ch for ch in sample_str
                    if not re.match(r"[A-Za-z0-9_-]", ch)
                )
            )

            issues.append(
                "contains invalid character(s): "
                + ", ".join(repr(x) for x in invalid_chars)
            )

        if issues:

            if not warnings_found:
                log("")
                log("WARNING: Sample name validation issues detected:")
                log("")
                warnings_found = True

            for issue in issues:
                log(f"  {sample_str} - {issue}")

    if warnings_found:
        log("")
        log(
            "WARNING: Illumina may reject Sample_ID values "
            "containing invalid characters or reserved names."
        )

def validate_duplicate_indices_per_lane(df):

    duplicate_found = False

    grouped = (
        df.groupby(["lane", "index_name"])
          .size()
          .reset_index(name="count")
    )

    duplicates = grouped[grouped["count"] > 1]

    if duplicates.empty:
        return

    duplicate_found = True

    log("")
    log("ERROR: Duplicate index assignments detected within lanes:")
    log("")

    for _, row in duplicates.iterrows():

        lane = row["lane"]
        index_name = row["index_name"]
        count = row["count"]

        affected = df[
            (df["lane"] == lane)
            & (df["index_name"] == index_name)
        ]["sample_name"].tolist()

        log(
            f"Lane {lane}: {index_name} "
            f"used {count} times"
        )

        for sample in affected:
            log(f"  - {sample}")

    if duplicate_found:
        raise SampleSheetError(
            "Duplicate index assignments found within the same lane."
        )

def parse_input_file(file_path, index_names, start_index=None):
    df = pd.read_csv(file_path,sep=detect_delimiter(file_path),engine="python")

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
    sample_counts = collections.Counter(samples)

    duplicates = {
        sample: count
        for sample, count in sample_counts.items()
        if count > 1
    }

    if duplicates:
        log("WARNING: Duplicate sample names detected:")
        for sample, count in sorted(duplicates.items()):
            log(f"  {sample}: {count} occurrences")

    # Normalize empty strings
    df["index_name"] = df["index_name"].replace("", pd.NA)

    all_missing = df["index_name"].isnull().all()
    some_missing = df["index_name"].isnull().any()

    # -------------------------------------------------
    # CASE 1: fully automatic assignment
    # -------------------------------------------------
    if all_missing:

        if not start_index:
            raise SampleSheetError(
                "No index_name values provided. "
                "Please specify --start-index."
            )

        indices = get_wrapped_indices(
            index_names,
            start_index,
            len(df)
        )

        df["index_name"] = indices

        log(
            f"INFO: Automatically assigned indices "
            f"INFO: starting from {start_index}"
        )

    # -------------------------------------------------
    # CASE 2: hybrid assignment
    # -------------------------------------------------
    elif some_missing:

        if not start_index:
            raise SampleSheetError(
                "ERROR: Some samples contain index_name values while others are empty.\n"
                "ERROR: Please either:\n"
                "ERROR:   - provide all index_name values manually\n"
                "ERROR:   - OR use --start-index for automatic completion"
            )

        log(
            "\nWARNING: Hybrid index assignment detected.\n"
            "WARNING: Some samples already contain configured index names,\n"
            "WARNING: while others are missing.\n"
            "WARNING: Missing index names will now be automatically assigned\n"
            f"WARNING: starting from: {start_index}\n"
        )

        # Get required number of indices
        missing_count = df["index_name"].isnull().sum()

        auto_indices = get_wrapped_indices(
            index_names,
            start_index,
            missing_count
        )

        auto_iter = iter(auto_indices)

        assigned_samples = []

        for idx, row in df.iterrows():

            if pd.isna(row["index_name"]):

                new_index = next(auto_iter)

                df.at[idx, "index_name"] = new_index

                assigned_samples.append(
                    f"{row['sample_name']} -> {new_index}"
                )

        log("INFO: Automatically assigned indices:")
        for x in assigned_samples:
            log(f"INFO: - {x}")

    # -------------------------------------------------
    # CASE 3: fully manual assignment
    # -------------------------------------------------
    else:

        log("INFO: Using fully manual index assignment.")

    # Validate index names
    for s, idx in zip(df["sample_name"], df["index_name"]):
        if idx not in index_names:
            raise SampleSheetError(f"Invalid index '{idx}' for sample '{s}'.")

    # Validate lanes
    df["lane"] = [validate_lane(v, s) for v, s in zip(df["lane"], df["sample_name"])]

    return df


def write_samplesheet(output, run_name, df, index_lookup, read_cycles, index_cycles, software_version):
    with open(output, "w") as f:
        f.write("[Header],\n")
        f.write("FileFormatVersion,2\n")
        f.write(f"RunName,{run_name}\n")
        f.write("InstrumentPlatform,NovaSeqXSeries\n")
        f.write("IndexOrientation,Forward\n\n")

        f.write("[Reads]\n")
        f.write(f"Read1Cycles,{read_cycles}\n")
        f.write(f"Read2Cycles,{read_cycles}\n")
        f.write(f"Index1Cycles,{index_cycles}\n")
        f.write(f"Index2Cycles,{index_cycles}\n\n")

        f.write("[BCLConvert_Settings]\n")
        f.write(f"SoftwareVersion,{software_version}\n")
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
    parser.add_argument("--index-file","-i", required=True, help="Illumina index set CSV (default: set_A-D_index_adapters.csv)")
    parser.add_argument("--sample-config","-c", required=True, help="Sample input file (see: README)")
    parser.add_argument("--run-name","-r", default="XResXX", help="Run name (default: XResXX)")
    parser.add_argument("--start-index","-s",
                        help="Start index for automatic assignment (required for one-column input) example: UDP0001",
    )
    parser.add_argument("--read-cycles","-rc", default="151", help="Readcycles (default: 301)")
    parser.add_argument("--software-version","-v", default="4.4.12", help="SoftwareVersion (default: 4.4.12)")
    parser.add_argument("--index-cycles","-ic", default="10", help="Indexcycles (default: 8)")
    parser.add_argument("--output","-o", default="SampleSheet.csv",
        help="Output SampleSheet file (default: SampleSheet.csv)")

    args = parser.parse_args()

    log_file = Path(args.output).with_suffix(".log")

    if Path(args.output).exists():
        log(
            f"\nWARNING:\n"
            f"Output file already exists:\n"
            f"  {args.output}\n"
        )

        while True:

            answer = input(
                "Overwrite existing file? [y/n]: "
            ).strip().lower()

            if answer in {"y", "yes"}:
                log("Overwriting existing file.\n")
                break

            elif answer in {"n", "no"}:
                log("Operation cancelled.")
                sys.exit(0)

            else:
                log(
                    "Please answer with:\n"
                    "  y / yes\n"
                    "  n / no"
                )

    log("\n####################")
    log("Errors/Warnings/Info")
    log("####################\n")

    index_df = load_index_table(args.index_file)
    index_names = index_df["Index_Name"].tolist()
    index_lookup = index_df.set_index("Index_Name").to_dict(orient="index")

    df = parse_input_file(args.sample_config, index_names, args.start_index)

    # Validations
    validate_sample_names(df)
    validate_duplicate_indices_per_lane(df)

    write_samplesheet(args.output, args.run_name, df, index_lookup, args.read_cycles, args.index_cycles, args.software_version)
    
    unique_samples = df["sample_name"].nunique()
    
    log(f"INFO: Runname set to {args.run_name}")
    log(f"INFO: Read cycles set to {args.read_cycles}")
    log(f"INFO: Index cycles set to {args.index_cycles}")
    log(f"INFO: SoftwareVersion set to {args.software_version}")
    log(f"INFO: Total sample-lane combinations: {len(df)}")
    log(f"INFO: Unique samples: {unique_samples}")
    log("INFO: SampleSheet created successfully.")

    write_log_file(log_file)
    log(f"INFO: Log written to {log_file}")


if __name__ == "__main__":
    try:
        main()
    except SampleSheetError as e:
        log(f"ERROR: {e}")
        sys.exit(1)