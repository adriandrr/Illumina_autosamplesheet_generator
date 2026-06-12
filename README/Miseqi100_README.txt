README — MiSeq SampleSheet Generator (Dual Index)
Overview

This script generates a valid Illumina MiSeq SampleSheet from:

an Illumina index reference file
a user-provided sample configuration file

It automatically converts index names (e.g. N701, S501) into the correct DNA sequences required by the sequencer.

----------------------------------------
1. REQUIREMENTS
----------------------------------------

Software
Python ≥ 3.8
Python package:
pandas
Installation

Open a terminal and run:

pip install pandas

----------------------------------------
2. INPUT FILES
----------------------------------------

2.1 Index File (provided by Illumina, prepared by Adrian)

This file contains the mapping between index names and sequences.

Required format:
i7_Index_Name,i7_Bases_for_MiSeq,i5_Index_Name,i5_Bases_for_MiSeq
N701,TAAGGCGA,S501,TAGATCGC
N702,CGTACTAG,S502,CTCTCTAT
...

2.2 Sample Configuration File (you create this)

This file defines which sample gets which indices.

Required format:
sample_name,i7_index,i5_index
Sample1,N701,S501
Sample2,N702,S502
Sample3,N703,S503

Important rules:
Header must be present
Column names must match exactly:
sample_name
i7_index
i5_index
No empty cells allowed
Sample names must be unique
Index names must exist in the index file
Supported delimiters

The script automatically detects:

comma ,
tab \t
semicolon ;
space

So these are all valid:

sample_name,i7_index,i5_index
sample_name    i7_index    i5_index
(just keep consistent)

----------------------------------------
3. RUNNING THE SCRIPT
----------------------------------------

flag order free to choose

Basic usage
python3 miseqi100_autosamplesheet.py \
  --index-file index.csv \
  --sample-config samples.csv \
  --run-name MyRun

Full command with all options
python3 miseqi100_autosamplesheet.py \
  -i index.csv \
  -c samples.csv \
  -r MyRun \
  -rc 301 \
  -ic 8 \
  -o SampleSheet.csv

Parameters explained
Parameter	Description
-i / --index-file	Index reference file
-c / --sample-config	Sample configuration file
-r / --run-name	Name of sequencing run
-rc / --read-cycles	Read length (default: 301)
-ic / --index-cycles	Index length (default: 8)
-o / --output	Output file name

----------------------------------------
4. OUTPUT
----------------------------------------

The script generates:

SampleSheet.csv

This file is (hopefully) ready to be used on the Illumina instrument.

----------------------------------------
4.1 INTERACTIVE OVERWRITE CONFIRMATION
----------------------------------------

If the selected output file already exists:

    Samplesheet1.csv

the script will stop and ask for confirmation before overwriting:

    WARNING:
    Output file already exists:
      Samplesheet1.csv

    Overwrite existing file? [y/n]:

Valid responses:

    y
    yes
    n
    no

Behavior:

    y / yes
    → overwrite existing file

    n / no
    → cancel execution safely

This is intended to prevent accidental overwriting
of already validated SampleSheets.

----------------------------------------
5. What the Script Does (Simple Explanation)
----------------------------------------

For each sample:

Reads the index names (e.g. N701, S501)
Looks up the corresponding DNA sequences
Writes them into the SampleSheet, adds header

Example:

Input:

Sample1,N701,S501

Output:

Sample_ID,Index,Index2
Sample1,TAAGGCGA,TAGATCGC

----------------------------------------
6. COMMON ERRORS AND FIXES
----------------------------------------

❌ "Index file not found"
Check file path
Ensure file exists

❌ "Missing columns in index file"
Index file format is wrong
Check header spelling

❌ "Missing columns in sample file"
Header missing or incorrect

Must be:

sample_name,i7_index,i5_index

❌ "Sample file contains empty values"
Remove empty cells
Ensure all samples have indices

❌ "Duplicate sample names detected"
Each sample must appear only once

❌ "Invalid i7/i5 index"
Index name does not exist in index file
Check spelling carefully

----------------------------------------
7. RECOMMENDED WORKFLOW
----------------------------------------

Copy an existing sample file template
Fill in sample names and indices in Excel
Export as CSV
Run script
Upload SampleSheet to sequencer

----------------------------------------
8. TIPS FOR RELIABLE USE
----------------------------------------

Always double-check index names
Never edit the index reference file manually
Keep filenames simple (no spaces)
Use consistent formatting (CSV recommended)
Validate small test runs before large batches

----------------------------------------
9. EXAMPLE FILES
----------------------------------------

Sample file:
sample_name,i7_index,i5_index
WWDI2568,N701,S501
WWKL2567,N702,S502
WWKL2568,N703,S503
Output:
Sample_ID,Index,Index2
WWDI2568,TAAGGCGA,TAGATCGC
WWKL2567,CGTACTAG,CTCTCTAT
WWKL2568,AGGCAGAA,TATCCTCT

----------------------------------------
SUMMARY
----------------------------------------

This script ensures:

correct index sequence assignment
validated input
reproducible SampleSheet generation

It is designed for safe use in routine sequencing workflows.