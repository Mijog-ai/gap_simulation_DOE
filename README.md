# DOE Batch Simulation Setup Script

## Overview
This Python script provides a GUI-based tool to automate the initial setup for Design of Experiments (DOE) batch simulations for MZ hydraulic pump simulations. It verifies folder structure, copies required files, extracts geometry parameters, and reads lK_scale_value parameters from a CSV file.

## Features

### ✓ GUI Interface
- User-friendly graphical interface using PyQt5
- Browse buttons for folder and file selection
- Real-time output log display
- Automatic execution without user prompts

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

### GUI Mode (Recommended)
```bash
python3 DOE_batch_setup.py
```

This will launch a graphical interface where you can:
1. Select the base folder path using the Browse button
2. Select the CSV file containing lK_scale_value parameters
3. Click "Run Batch Setup" to execute all steps automatically
4. View real-time progress in the output log
5. Get a success/error popup when complete

The GUI automatically:
- Verifies the folder structure
- Copies piston_pr.inp (overwrites if exists)
- Extracts geometry parameters from geometry.txt
- Reads all lK_scale_values from the CSV file
- No user prompts during execution

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

Each row after the header represents a scale value to be used in batch processing.

### Programmatic Usage

```python
from DOE_batch_setup import DOEBatchSetup

# Initialize
setup = DOEBatchSetup('/path/to/base_folder')

# Verify folder structure
status = setup.verify_folder_structure()

# Execute Step 0
success = setup.step0_copy_piston_pr()

# Execute Step 1
geometry_values = setup.step1_extract_geometry_values()

# Read CSV values
lk_values = setup.read_lk_scale_values('/path/to/csv_file.csv')

# Access extracted values
print(f"lK = {geometry_values['lK']} mm")
print(f"lZ0 = {geometry_values['lZ0']} mm")
print(f"lKG = {geometry_values['lKG']} mm")
print(f"lSK = {geometry_values['lSK']} mm")
print(f"lK_scale_values = {lk_values}")
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
   ```

4. **Summary Report**
   - Success/failure status of each step
   - Dictionary of extracted values for further processing

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

### Usage

```bash
# Run both copy and scaling operations
python3 run_piston_scaling.py /path/to/base_folder

# Only copy piston_pr.inp files (no scaling)
python3 run_piston_scaling.py /path/to/base_folder --copy-only

# Only run Z_MeshScaler.py (no copying)
python3 run_piston_scaling.py /path/to/base_folder --scale-only
```

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

## Next Steps

After completing all steps, you can:

1. **Verify scaled meshes** in each IM_piston folder
2. **Run simulations** for each scaled configuration
3. **Analyze results** across different scale values
4. **Post-process** simulation outputs

## Requirements

- Python 3.6 or higher
- PyQt5 (install with: `pip install PyQt5`)
- Standard library modules (os, shutil, re, csv, pathlib, threading, sys)

## Error Handling

The script includes comprehensive error handling:
- ✓ Missing file/folder detection
- ✓ CSV file validation and parsing
- ✓ Parameter extraction validation
- ✓ Clear error messages with GUI popups
- ✓ Real-time progress logging

## Notes

- The script uses regex pattern matching to extract parameters from geometry.txt
- All extracted values are returned as floats
- The copy operation automatically overwrites existing files (no prompts)
- All paths are handled using `pathlib.Path` for cross-platform compatibility
- The GUI runs in a separate thread to remain responsive during execution
- Print statements are redirected to the GUI output log for real-time feedback

## Author
### Mit Gandhi

