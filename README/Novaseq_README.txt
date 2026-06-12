======================== README ========================

python script: novaseq_autosamplesheetv3
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

    4. Hybrid index assignment (NEW):

    sample_name,index_name,lane
    WWKK2426-170,,8
    WWKK2426-171,UDP0009,1
    WWKK2428-110,UDP0010,2
    WWKK2428-111,UDP0011,3
    WWKK2428-130,,4
    WWKK2428-131,,5

    → Requires --start-index or -s
    → Already configured index names will NOT be changed
    → Missing index names will automatically be assigned sequentially
    starting from the provided --start-index
    → Automatic assignment follows the row order in the file
    → V3 indexes are considered automatically
    → Duplicate Indexes (manually and automatically given) will cause an ERROR
    → Manual verification is recommended

    Example:

    python3 novaseq_autosamplesheet.py \
      -i set_A-D_index_adapters.csv \
      -c samples.csv \
      -s UDP0025

    Results in:

    WWKK2426-170 → UDP0025
    WWKK2428-130 → UDP0026
    WWKK2428-131 → UDP0027

    Rules:
    - lane must be 1–8
    - leave lane empty to auto-assign

----------------------------------------
3. RUNNING THE SCRIPT
----------------------------------------

Basic usage:

python3 novaseq_autosamplesheet.py --index-file set_A-D_index_adapters.csv --sample-config samples.csv

or with short flags: 

python3 novaseq_autosamplesheet.py -i set_A-D_index_adapters.csv -c samples.csv

----------------------------------------
4. OPTIONAL FLAGS
----------------------------------------

order free to choose

  --start-index/-s UDP0005
  --run-name/-r MyRun
  --read-cycl/-rc 151
  --index-cycle/-ic 10
  --output/-o Samplesheet1.csv

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
5. OUTPUT
----------------------------------------

Creates:
    Samplesheet1.csv

(Hopefully) Ready for direct upload to Illumina system.

----------------------------------------
6. COMMON ERRORS
----------------------------------------

ERROR: Missing index columns
→ Wrong index file

ERROR: Start index not found
→ Typo in index name

ERROR: Duplicate sample names
→ Each sample must be unique

ERROR: Lane must be between 1 and 8
→ Fix lane column

ERROR: Some samples contain index names while others are empty
→ Either:
    - provide ALL index names manually
    - OR use --start-index for automatic completion

ERROR: Duplicate index assignments detected
→ The same index was assigned multiple times
→ Check hybrid assignment carefully

ERROR: Output file already exists
→ Confirm overwrite with:
    y / yes
→ Or choose a different output filename using:
    --output / -o

----------------------------------------
7. TIPS
----------------------------------------

- Use Notion/Excel to prepare sample sheet, then export as CSV
- Double-check index names carefully
- Keep original index file unchanged
- Hybrid index assignment is useful for partially prepared runs
- Always manually inspect automatically assigned indices
- Avoid duplicate index combinations whenever possible
- Use different output names for test runs

========================================================
