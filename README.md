# SampleSheet Generators

A collection of command-line tools for generating Illumina SampleSheets from simplified user-provided configuration files.

The repository currently contains:

* NovaSeq X Series SampleSheet Generator
* MiSeq i100 Series SampleSheet Generator

These tools are intended for routine laboratory use and are designed to reduce manual editing of Illumina SampleSheet files while providing extensive validation and user feedback.

---

# Repository Structure

```text
├── README
├── README.md
├── auto_samplesheet.ipynb
├── autosamplesheetv1.py
├── autosamplesheetv2.py
├── examples
├── miseqi100_autosamplesheet.py
├── novaseq_autosamplesheet.py
├── set_A-D_index_adapters.csv
└── set_NexteraXT_index_adapters.csv
```

---

# Requirements

## Software

* Python ≥ 3.8

## Python Packages

Install required packages:

```bash
pip install pandas
```

---

# Available Tools

## 1. NovaSeq X Series SampleSheet Generator

### Purpose

Creates NovaSeq X SampleSheets from a simplified sample configuration file.

### Features

* Automatic index assignment
* Manual index assignment
* Hybrid index assignment
* Optional lane assignment
* Duplicate index detection within lanes
* Sample name validation
* Automatic lane assignment
* Index wrap-around support
* Interactive overwrite protection
* Log file generation

### Input

* NovaSeq UDP index file
* User sample configuration file

### Output

* NovaSeq-compatible SampleSheet.csv
* Log file

### Documentation

See:

```text
README/Novaseq_README.txt
```

---

## 2. MiSeq i100 Series SampleSheet Generator

### Purpose

Creates MiSeq i100 SampleSheets using separate i7 and i5 index definitions.

### Features

* i7/i5 index lookup
* Automatic conversion of index names to sequences
* Input validation
* Sample name validation
* Log file generation
* MiSeq i100 compatible output

### Input

* Index lookup table
* Sample configuration file

### Output

* MiSeq i100 SampleSheet.csv
* Log file

### Documentation

See:

```text
README/Miseqi100_README.txt
```

---

# Choosing the Correct Tool

| Sequencer  | Tool                       |
| ---------- | -------------------------- |
| NovaSeq X  | novaseq_autosamplesheet.py |
| MiSeq i100 | miseq_i100_samplesheet.py  |

---

# Example Workflows

## NovaSeq X

Sample configuration:

```text
sample_name,index_name,lane
WWKK2426-110,UDP0008,1
WWKK2426-111,UDP0009,2
WWKK2426-130,UDP0010,3
```

Generate SampleSheet:

```bash
python3 novaseq_autosamplesheet.py \
    -i set_A-D_index_adapters.csv \
    -c samples.csv \
    -r XRes52
```

Output:

```text
SampleSheet.csv
SampleSheet.log
```

---

## MiSeq i100

Sample configuration:

```text
sample_name,i7_index,i5_index
WWDI2568,N701,S501
WWKL2567,N702,S502
WWKL2568,N703,S503
```

Generate SampleSheet:

```bash
python3 miseq_i100_samplesheet.py \
    -i set_NexteraXT_index_adapters.csv \
    -c samples.csv \
    -r MiSeq_Run_001
```

Output:

```text
SampleSheet.csv
SampleSheet.log
```

---

# Validation Performed

Both tools perform extensive validation including:

* Required columns present
* Missing values
* Sample name validation
* Invalid index names
* Duplicate sample detection
* File existence checks
* Output overwrite confirmation

---

# Log Files

Both generators create log files containing:

* warnings
* errors
* informational messages
* automatic index assignments
* duplicate sample reports
* validation summaries

These logs should be archived together with the generated SampleSheet whenever possible.

---

# General Recommendations

* Always review generated SampleSheets before upload.
* Keep index definition files unchanged.
* Store generated log files together with sequencing documentation.
* Use descriptive run names.
* Verify automatically assigned indices before sequencing.
* Perform a small test run after updating any index set.

---

# Support

For questions regarding index sets, workflow changes, or repository maintenance, contact the repository maintainer.
