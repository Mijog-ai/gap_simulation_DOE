# DOE Batch Simulation Setup Script

## Overview
This Python script automates the initial setup for Design of Experiments (DOE) batch simulations for MZ hydraulic pump simulations. It verifies folder structure, copies required files, and extracts geometry parameters.

## Features

### ✓ Step 0: File Copy Operation
- Copies `piston_pr.inp` from `INP` folder to `Zscalar` folder
- One-time operation with overwrite protection

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

### Interactive Mode (Recommended)
```bash
python3 doe_batch_setup.py
```

This will:
1. Prompt you for the base folder path
2. Verify the folder structure
3. Ask for confirmation before proceeding
4. Execute Step 0 and Step 1
5. Display a summary of results

### Programmatic Usage

```python
from doe_batch_setup import DOEBatchSetup

# Initialize
setup = DOEBatchSetup('/path/to/base_folder')

# Verify folder structure
status = setup.verify_folder_structure()

# Execute Step 0
success = setup.step0_copy_piston_pr()

# Execute Step 1
geometry_values = setup.step1_extract_geometry_values()

# Access extracted values
print(f"lK = {geometry_values['lK']} mm")
print(f"lZ0 = {geometry_values['lZ0']} mm")
print(f"lKG = {geometry_values['lKG']} mm")
print(f"lSK = {geometry_values['lSK']} mm")
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

## Next Steps

After completing Step 0 and Step 1, you can:

1. **Extend the script** to include additional steps for your DOE workflow
2. **Batch process** multiple simulation folders
3. **Modify parameters** based on extracted geometry values
4. **Generate input files** for simulation runs

## Requirements

- Python 3.6 or higher
- Standard library only (no external dependencies)

## Error Handling

The script includes comprehensive error handling:
- ✓ Missing file/folder detection
- ✓ Overwrite protection
- ✓ Parameter extraction validation
- ✓ Clear error messages with guidance

## Notes

- The script uses regex pattern matching to extract parameters from geometry.txt
- All extracted values are returned as floats
- The copy operation includes a confirmation prompt if the destination file already exists
- All paths are handled using `pathlib.Path` for cross-platform compatibility

## Author
Created for MZ hydraulic pump simulation batch processing

## Version
1.0.0 - Initial release with Step 0 and Step 1 implementation