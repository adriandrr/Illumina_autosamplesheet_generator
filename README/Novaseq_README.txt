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

    4. Hybrid index assignment

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
    → The script will print a detailed warning showing all automatically
      assigned samples and indices
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

    5. Sample name validation

    Sample names are checked against Illumina naming recommendations.

    Allowed characters:
        A-Z
        a-z
        0-9
        -
        _

    Not allowed:
        spaces
        ? . ( ) [ ] / \ = + < > : ; " ' , * ^ | &

    Additional checks:
        - sample names should not start with '-'
        - sample names should not end with '-'
        - sample names should not start with '_'
        - sample names should not end with '_'
        - sample names should not exceed 40 characters
        - reserved names are discouraged:
            all
            default
            none
            unknown
            undetermined
            stats
            reports

    Violations generate WARNINGS only.
    SampleSheet creation continues.

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
  --software-version/-v 4.4.12
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

    SampleSheet.csv

and additionally:

    SampleSheet.log

The log file contains:

    - warnings
    - errors
    - automatic index assignments
    - duplicate sample reports
    - duplicate index reports
    - validation messages
    - run settings

The generated SampleSheet should be reviewed before upload
to the Illumina system.

----------------------------------------
6. COMMON ERRORS / WARNINGS
----------------------------------------

ERROR: Missing index columns
→ Wrong index file

ERROR: Start index not found
→ Typo in index name

ERROR: Lane must be between 1 and 8
→ Fix lane column

ERROR: Some samples contain index names while others are empty
→ Either:
    - provide ALL index names manually
    - OR use --start-index for automatic completion

ERROR: Invalid index 'UDPxxxx' for sample 'SampleA'
→ Index does not exist in index file

ERROR: Duplicate index assignments found within the same lane
→ The same index is used multiple times in one lane

Example:

    Lane 1: UDP0008 used 2 times
      - SampleA
      - SampleB

Using the same index in different lanes is allowed.

WARNING: Duplicate sample names detected
→ Sample names occur more than once

Example:

    SampleA: 3 occurrences

WARNING: Sample name validation issues detected
→ Sample name may violate Illumina naming recommendations

Example:

    Sample Name - contains invalid character(s): ' '

WARNING: Hybrid index assignment detected
→ Some indices were assigned manually
→ Remaining indices were assigned automatically

WARNING: Output file already exists
→ Confirm overwrite with:
    y / yes

→ Or choose a different output filename using:
    --output / -o

----------------------------------------
7. TIPS
----------------------------------------

- Use Excel, Notion or LibreOffice to prepare sample files
- Export tables as CSV whenever possible
- Double-check index names carefully
- Keep original index files unchanged
- Hybrid index assignment is useful for partially prepared runs
- Always inspect automatically assigned indices
- Review duplicate sample warnings carefully
- Avoid reusing indices within the same lane
- Store SampleSheet.csv and SampleSheet.log together
- Use descriptive run names
- Use different output names for test runs

----------------------------------------
8. LOGGING
----------------------------------------

All warnings, errors and informational messages are written
both to the console and to a log file.

Example:

    SampleSheet.csv
    SampleSheet.log

The log file contains:

    INFO
    WARNING
    ERROR

messages generated during SampleSheet creation.

This file can be archived together with sequencing run
documentation for traceability.