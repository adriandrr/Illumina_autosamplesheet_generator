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

#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
import pandas as pd
import csv


class SampleSheetError(Exception):
    pass


# -----------------------------
# Load index file
# -----------------------------
def detect_delimiter(file_path: str) -> str:
    with open(file_path, "r", newline="") as f:
        sample = f.read(2048)
        try:
            return csv.Sniffer().sniff(sample, delimiters=",\t; ").delimiter
        except Exception:
            return None

def load_index_file(index_file, index_set):
    path = Path(index_file)
    if not path.exists():
        raise SampleSheetError(f"Index file not found: {index_file}")


    if index_set == "NT":
        df = pd.read_csv(path)
        required = {"i7_Index_Name","i7_Bases_for_MiSeq","i5_Index_Name","i5_Bases_for_MiSeq",}

        missing = required - set(df.columns)
        if missing:
            raise SampleSheetError(f"Missing columns in index file: {missing}")

        # Build lookup dictionaries
        i7_lookup = dict(zip(df["i7_Index_Name"], df["i7_Bases_for_MiSeq"]))
        i5_lookup = dict(zip(df["i5_Index_Name"], df["i5_Bases_for_MiSeq"]))
    
    elif index_set == "UD":
        df = pd.read_csv(path,index_col=False)
        required = {
            "Index_Name",
            "i7_Bases_for_Sample_Sheet",
            "i5_Bases_for_Sample_Sheet_in_Forward_Orientation"
            }

        missing = required - set(df.columns)
        if missing:
            raise SampleSheetError(f"Missing columns in index file: {missing}")
        # Build lookup dictionaries
        i7_lookup = dict(zip(df["Index_Name"], df["i7_Bases_for_Sample_Sheet"]))
        i5_lookup = dict(zip(df["Index_Name"], df["i5_Bases_for_Sample_Sheet_in_Forward_Orientation"]))
    else:
        raise SampleSheetError(f"Index set must be NT (NexteraXT) or UD (UDP Indexes): {index_set}")

    return i7_lookup, i5_lookup


# -----------------------------
# Load sample file
# -----------------------------
def load_sample_file(sample_file, index_set):
    path = Path(sample_file)
    if not path.exists():
        raise SampleSheetError(f"Sample file not found: {sample_file}")

    df = pd.read_csv(sample_file,sep=detect_delimiter(sample_file),engine="python")

    if index_set == "NT":
        required = {"sample_name", "i7_index", "i5_index"}
    elif index_set == "UD":
        required = {"sample_name", "UD_index"}
    else:
        raise SampleSheetError(f"Index set must be NT (NexteraXT) or UD (UDP Indexes): {index_set}")
    
    missing = required - set(df.columns)

    if missing:
        raise SampleSheetError(f"Missing columns in sample file: {missing}")

    # Clean empty strings
    df = df.replace("", pd.NA)

    # Validate no missing values
    if df.isnull().any().any():
        raise SampleSheetError("Sample file contains empty values.")

    # Validate unique samples
    if df["sample_name"].duplicated().any():
        raise SampleSheetError("Duplicate sample names detected.")

    return df


# -----------------------------
# Build SampleSheet
# -----------------------------
def build_samplesheet(df, index_set, i7_lookup, i5_lookup):
    rows = []
    
    if index_set == "NT":
        for _, row in df.iterrows():
            sample = row["sample_name"]
            i7_name = row["i7_index"]
            i5_name = row["i5_index"]

            if i7_name not in i7_lookup:
                raise SampleSheetError(f"Invalid i7 index '{i7_name}' for sample '{sample}'")

            if i5_name not in i5_lookup:
                raise SampleSheetError(f"Invalid i5 index '{i5_name}' for sample '{sample}'")

            rows.append({
                "Sample_ID": sample,
                "Index": i7_lookup[i7_name],
                "Index2": i5_lookup[i5_name],
            })
    elif index_set == "UD":
        for _, row in df.iterrows():
            sample = row["sample_name"]
            UD_name = row["UD_index"]

            if UD_name not in i7_lookup:
                raise SampleSheetError(f"Invalid i7 index '{UD_name}' for sample '{sample}'")

            if UD_name not in i5_lookup:
                raise SampleSheetError(f"Invalid i5 index '{UD_name}' for sample '{sample}'")

            rows.append({
                "Sample_ID": sample,
                "Index": i7_lookup[UD_name],
                "Index2": i5_lookup[UD_name],
            })
    else:
        raise SampleSheetError(f"Index set must be NT (NexteraXT) or UD (UDP Indexes): {index_set}")
        

    return pd.DataFrame(rows)


# -----------------------------
# Write output
# -----------------------------
def write_samplesheet(df, output_file, run_name, read_cycles, index_cycles):
    with open(output_file, "w") as f:
        f.write("[Header]\n")
        f.write("FileFormatVersion,2\n")
        f.write(f"RunName,{run_name}\n")
        f.write("InstrumentPlatform,MiSeqi100Series\n")
        f.write("IndexOrientation,Forward\n")
        f.write("AnalysisLocation,Local\n\n")
        f.write("[Reads]\n")
        f.write(f"Read1Cycles,{read_cycles}\n")
        f.write(f"Read2Cycles,{read_cycles}\n")
        f.write(f"Index1Cycles,{index_cycles}\n")
        f.write(f"Index2Cycles,{index_cycles}\n\n")
        f.write("[BCLConvert_Settings]\n")
        f.write("SoftwareVersion,4.4.6\n")
        f.write("AdapterRead1,CTGTCTCTTATACACATCT\n")
        f.write("AdapterRead2,CTGTCTCTTATACACATCT\n")
        f.write("OverrideCycles,Y301;I8;I8;Y301\n")
        f.write("FastqCompressionFormat,dragen\n")
        f.write("NoLaneSplitting,TRUE\n")
        f.write("GenerateFastqcMetrics,TRUE\n\n")
        f.write("[BCLConvert_Data]\n")
        f.write("Sample_ID,Index,Index2\n")
        
        for i, row in df.iterrows():
            sample = row["Sample_ID"]
            idx = row["Index"]
            idx2 = row["Index2"]

            f.write(
                f"{sample},{idx},{idx2}\n"
            )


# -----------------------------
# CLI
# -----------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Generate SampleSheet from dual-index input"
    )

    parser.add_argument("--index-file","-i", required=True, help="Illumina index set CSV")
    parser.add_argument("--sample-config","-c", required=True, help="Sample input file (see: README)")
    parser.add_argument("--index-set","-s", default="NT", help="Specification of index set (default: NT; UD possible)")
    parser.add_argument("--run-name","-r", default="Runname123", help="Run name (default: Runname123)")
    parser.add_argument("--read-cycles","-rc", default="301", help="Readcycles (default: 301)")
    parser.add_argument("--index-cycles","-ic", default="8", help="Indexcycles (default: 8)")
    parser.add_argument("--output","-o", default="SampleSheet.csv",help="Output SampleSheet file (default: SampleSheet.csv)")

    args = parser.parse_args()

    if args.run_name == "Runname123":
        print("Warning: No Runname given, used default Runname123, please change manually")

    i7_lookup, i5_lookup = load_index_file(args.index_file, args.index_set)
    sample_df = load_sample_file(args.sample_config, args.index_set)

    result_df = build_samplesheet(sample_df, args.index_set, i7_lookup, i5_lookup)

    write_samplesheet(result_df, args.output, args.run_name, args.read_cycles, args.index_cycles)

    print(f"SampleSheet written to: {args.output}")
    print(f"Total samples: {len(result_df)}")


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
    conda install -c anaconda pandas

----------------------------------------
2. INPUT FILES
----------------------------------------

A) Index file (provided by Illumina, prepared by Adrian)
   Example: set_A-D_index_adapters.csv

B) Sample file (YOU create this)
    
    General format:
    This file MUST contain a header:

    sample_name,index_name,lane
    (comma as separator)

    or

    sample_name index_name  lane
    (tab as separator → f.e. when you copy from tables)

    DONT mix up separators like this:
    
    sample_name	index_name	lane
    WWKK2426-110,UDP0008,1
    WWKK2426-111,UDP0009,2
    WWKK2426-130,UDP0010,3

    Keep it consistent:
    
    sample_name,index_name,lane
    WWKK2426-110,UDP0008,1
    WWKK2426-111,UDP0009,2
    WWKK2426-130,UDP0010,3

    or

    sample_name index_name   lane
    WWKK2426-110    UDP0008 1
    WWKK2426-111    UDP0009 2
    WWKK2426-130    UDP0010 3

    Valid formats:

    1. Automatic index assignment:

    sample_name,index_name,lane
    SampleA
    SampleB
    SampleC

    → Requires --start-index or -s
    → in this case, the index names will be assigned sequentially
    → f.e. when executed with -s UDP0008, the first sample will be assigned to UDP0008,
    the next sample will be UDP0009 and so on up until the last (V3 Indexes are considered)
    → manual check is recommended
    → Lanes will be assigned automatically from 1-8

    2. Manual index assignment:

    sample_name,index_name,lane
    SampleA,UDP0001
    SampleB,UDP0002
    SampleC,UDP0006

    → Lanes will be assigned automatically from 1-8

    3. Optional lane assignment:

    sample_name,index_name,lane
    SampleA,UDP0001,1
    SampleB,UDP0002,2
    SampleC,UDP0003,6

    Rules:
    - lane must be 1–8
    - leave lane empty to auto-assign

----------------------------------------
3. RUNNING THE SCRIPT
----------------------------------------

Basic usage:

python3 autosamplesheetv3.py \
  --index-file set_A-D_index_adapters.csv \
  --sample-config samples.csv \
  --run-name MyRun \
  --start-index UDP0005 \
  --output Samplesheet1.csv

----------------------------------------
4. OUTPUT
----------------------------------------

Creates:
    Samplesheet1.csv

(Hopefully) Ready for direct upload to Illumina system.

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

- Use Notion/Excel to prepare sample sheet, then export as CSV
- Double-check index names carefully
- Keep original index file unchanged

========================================================
"""
