# DOE Batch Simulation Setup Script

## Overview
This Python script provides a GUI-based tool to automate the initial setup for Design of Experiments (DOE) batch simulations for MZ hydraulic pump simulations. It verifies folder structure, copies required files, extracts geometry parameters, and reads lK_scale_value parameters from a CSV file.

## Features

### ✓ CSV Parameter Import
- Reads `lK_scale_value` parameters from CSV file
- Supports multiple scale values for batch processing
- Automatic validation and error reporting

### ✓ Step 0: File Copy Operation
- Copies `piston_pr.inp` from `INP` folder to `Zscalar` folder
- Automatic overwrite (no prompts)

### ✓ Step 1: Geometry Parameter Extraction
- Extracts the following parameters from `geometry.txt`:
  - `lK` : Piston Length (mm)
  - `lZ0` : Displacement Chamber Length with Piston at ODP (mm)
  - `lKG` : Length of Piston Gap surface (mm)
  - `lSK` : Distance to Center of Mass of Piston/Slipper Assembly (mm)

### ✓ Folder Structure Verification
- Verifies all required folders exist:
  - `INP/` - Contains standard input files
  - `simulation/` - Contains simulation set folders
  - `influgen/` - Contains input files
  - `Zscalar/` - Contains scalar data
- Checks for required files:
  - `geometry.txt` in base folder
  - `piston_pr.inp` in INP folder

## Required Folder Structure

```
base_folder/
├── geometry.txt
├── INP/
│   └── piston_pr.inp
├── simulation/
│   ├── T60_2000rpm_350bar_100d/
│   └── T60_2850rpm_50bar_100d/
├── influgen/
│   └── input/
│       └── input.txt
└── Zscalar/
    └── scalar.txt
```

## Usage

### CSV File Format

The CSV file should contain lK_scale_value entries with a header row:

```csv
lK_scale_value
5
10
15
20
25
30
35
40
```



## Output

The script provides:

1. **Folder Verification Report**
   - Status of each required folder and file
   - Warning/error messages for missing items

2. **Step 0 Result**
   - Confirmation of file copy operation
   - Source and destination paths

3. **Step 1 Result - Extracted Geometry Values**
   ```
   lK         =    95.600000 mm
   lZ0        =    29.038000 mm
   lKG        =    80.753000 mm
   lSK        =    32.595000 mm


## Test Results

Based on your geometry.txt file, the script successfully extracted:

| Parameter | Value (mm) | Description |
|-----------|------------|-------------|
| lK        | 95.600     | Piston Length |
| lZ0       | 29.038     | Displacement Chamber Length |
| lKG       | 80.753     | Length of Piston Gap surface |
| lSK       | 32.595     | Distance to Center of Mass |

## Step 3: Piston Scaling Runner

After creating the IM_scaled_piston folders using the DOE_batch_setup.py script, use the `run_piston_scaling.py` script to:

1. Copy `piston_pr.inp` from `basefolder/INP/` to each `IM_piston` folder
2. Run `Z_MeshScaler.py` for each scaled folder using the `scalar.txt` file



### What it does

1. **Verification**: Checks that all required files and folders exist
2. **Step 1 - Copy Files**: Copies `piston_pr.inp` to each `IM_scaled_piston_*/IM_piston/` folder
3. **Step 2 - Run Scaling**: Executes `Z_MeshScaler.py` with each folder's `scalar.txt` file

### Expected Folder Structure

```
base_folder/
├── INP/
│   └── piston_pr.inp
└── simulation/
    ├── IM_scaled_piston_5/
    │   ├── IM_piston/
    │   │   └── piston_pr.inp (copied here)
    │   ├── scalar.txt
    │   ├── T60_2000rpm_350bar_100d/
    │   └── T60_2850rpm_50bar_100d/
    ├── IM_scaled_piston_10/
    │   ├── IM_piston/
    │   │   └── piston_pr.inp (copied here)
    │   ├── scalar.txt
    │   └── ...
    └── ...
```






## Author
### Mit Gandhi

