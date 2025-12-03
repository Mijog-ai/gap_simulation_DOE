#!/usr/bin/env python3
"""
DOE Batch Simulation Setup Script
This script prepares the environment for batch runs of MZ simulation
"""

import os
import shutil
import re
import csv
from pathlib import Path
import threading
import sys
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QFileDialog, QMessageBox, QFrame, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor


class DOEBatchSetup:
    def __init__(self, base_folder):
        """
        Initialize the DOE Batch Setup
        
        Args:
            base_folder: Path to the base folder containing all simulation files
        """
        self.base_folder = Path(base_folder)
        self.required_folders = {
            'INP': self.base_folder / 'INP',
            'simulation': self.base_folder / 'simulation',
            'influgen': self.base_folder / 'influgen',
            'Zscalar': self.base_folder / 'Zscalar'
        }
        self.geometry_file = self.base_folder / 'geometry.txt'
        
    def verify_folder_structure(self):
        """
        Verify that all required folders and files exist
        
        Returns:
            dict: Status of each required item
        """
        print("=" * 70)
        print("VERIFYING FOLDER STRUCTURE")
        print("=" * 70)
        
        status = {}
        
        # Check base folder
        print(f"\n📁 Base folder: {self.base_folder}")
        if self.base_folder.exists():
            print("   ✓ Base folder exists")
            status['base_folder'] = True
        else:
            print("   ✗ Base folder NOT found!")
            status['base_folder'] = False
            return status
        
        # Check required folders
        print("\n📂 Checking required folders:")
        for folder_name, folder_path in self.required_folders.items():
            if folder_path.exists() and folder_path.is_dir():
                print(f"   ✓ {folder_name} folder exists: {folder_path}")
                status[folder_name] = True
            else:
                print(f"   ✗ {folder_name} folder NOT found: {folder_path}")
                status[folder_name] = False
        
        # Check geometry.txt
        print("\n📄 Checking geometry file:")
        if self.geometry_file.exists():
            print(f"   ✓ geometry.txt exists: {self.geometry_file}")
            status['geometry_txt'] = True
        else:
            print(f"   ✗ geometry.txt NOT found: {self.geometry_file}")
            status['geometry_txt'] = False
        
        # Check piston_pr.inp in INP folder
        piston_pr_path = self.required_folders['INP'] / 'piston_pr.inp'
        print("\n📄 Checking INP files:")
        if piston_pr_path.exists():
            print(f"   ✓ piston_pr.inp exists: {piston_pr_path}")
            status['piston_pr_inp'] = True
        else:
            print(f"   ✗ piston_pr.inp NOT found: {piston_pr_path}")
            status['piston_pr_inp'] = False
        
        # Check scalar.txt in Zscalar folder
        scalar_path = self.required_folders['Zscalar'] / 'scalar.txt'
        if scalar_path.exists():
            print(f"   ✓ scalar.txt exists: {scalar_path}")
            status['scalar_txt'] = True
        else:
            print(f"   ⚠ scalar.txt NOT found: {scalar_path} (may be created later)")
            status['scalar_txt'] = False
        
        # Check simulation subfolders
        print("\n📂 Checking simulation subfolders:")
        if status.get('simulation', False):
            sim_folders = [f for f in self.required_folders['simulation'].iterdir() if f.is_dir()]
            if sim_folders:
                print(f"   ✓ Found {len(sim_folders)} simulation folders:")
                for sim_folder in sim_folders:
                    print(f"      - {sim_folder.name}")
                status['simulation_subfolders'] = True
            else:
                print("   ⚠ No simulation subfolders found")
                status['simulation_subfolders'] = False
        
        print("\n" + "=" * 70)
        all_critical = all([
            status.get('base_folder', False),
            status.get('INP', False),
            status.get('Zscalar', False),
            status.get('geometry_txt', False),
            status.get('piston_pr_inp', False)
        ])
        
        if all_critical:
            print("✓ All critical files and folders are present!")
        else:
            print("✗ Some critical files or folders are missing!")
        print("=" * 70 + "\n")
        
        return status
    
    def step0_copy_piston_pr(self):
        """
        Step 0: Copy piston_pr.inp from INP folder to Zscalar folder
        This step is executed only once
        
        Returns:
            bool: True if successful, False otherwise
        """
        print("=" * 70)
        print("STEP 0: COPYING piston_pr.inp TO Zscalar FOLDER")
        print("=" * 70)
        
        source_file = self.required_folders['INP'] / 'piston_pr.inp'
        dest_file = self.required_folders['Zscalar'] / 'piston_pr.inp'
        
        try:
            if not source_file.exists():
                print(f"✗ Source file not found: {source_file}")
                return False
            
            if dest_file.exists():
                print(f"⚠ Destination file already exists: {dest_file}")
                print("  Overwriting...")

            # Perform the copy
            shutil.copy2(source_file, dest_file)
            print(f"✓ Successfully copied piston_pr.inp")
            print(f"  From: {source_file}")
            print(f"  To:   {dest_file}")
            return True
            
        except Exception as e:
            print(f"✗ Error during copy operation: {e}")
            return False
        finally:
            print("=" * 70 + "\n")
    
    def step1_extract_geometry_values(self):
        """
        Step 1: Extract required values from geometry.txt
        
        Returns:
            dict: Dictionary containing the extracted values
        """
        print("=" * 70)
        print("STEP 1: EXTRACTING VALUES FROM geometry.txt")
        print("=" * 70)
        
        required_params = ['lK', 'lZ0', 'lKG', 'lSK']
        extracted_values = {}
        
        try:
            if not self.geometry_file.exists():
                print(f"✗ geometry.txt not found: {self.geometry_file}")
                return None
            
            print(f"\n📖 Reading file: {self.geometry_file}")
            
            with open(self.geometry_file, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            # Extract values using regex
            for param in required_params:
                # Pattern: parameter name followed by whitespace and a number
                pattern = rf'^\s*{param}\s+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)'
                match = re.search(pattern, content, re.MULTILINE)
                
                if match:
                    value = float(match.group(1))
                    extracted_values[param] = value
                else:
                    print(f"⚠ Warning: Could not find parameter '{param}' in geometry.txt")
                    extracted_values[param] = None
            
            # Display extracted values
            print("\n" + "=" * 70)
            print("EXTRACTED GEOMETRY VALUES")
            print("=" * 70)
            
            for param in required_params:
                value = extracted_values.get(param)
                if value is not None:
                    print(f"  {param:10s} = {value:12.6f} mm")
                else:
                    print(f"  {param:10s} = NOT FOUND")
            
            print("=" * 70)
            
            # Verify all values were found
            all_found = all(v is not None for v in extracted_values.values())
            if all_found:
                print("✓ All required values successfully extracted!")
            else:
                print("✗ Some values could not be extracted!")
            
            print("=" * 70 + "\n")
            
            return extracted_values
            
        except Exception as e:
            print(f"✗ Error reading geometry.txt: {e}")
            return None

    def read_lk_scale_values(self, csv_file_path):
        """
        Read lK_scale_value from CSV file

        Args:
            csv_file_path: Path to the CSV file containing lK_scale_value

        Returns:
            list: List of lK_scale_value values
        """
        print("=" * 70)
        print("READING lK_scale_value FROM CSV FILE")
        print("=" * 70)

        try:
            csv_path = Path(csv_file_path)
            if not csv_path.exists():
                print(f"✗ CSV file not found: {csv_path}")
                return None

            print(f"\n📖 Reading file: {csv_path}")

            lk_values = []
            with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.reader(f)
                header = next(reader, None)  # Skip header

                for row in reader:
                    if row and row[0].strip():  # Check if row is not empty
                        try:
                            value = float(row[0].strip())
                            lk_values.append(value)
                        except ValueError:
                            print(f"⚠ Warning: Could not convert '{row[0]}' to number, skipping...")

            print(f"\n✓ Successfully read {len(lk_values)} lK_scale_value entries:")
            for i, val in enumerate(lk_values, 1):
                print(f"   {i}. {val}")

            print("=" * 70 + "\n")

            return lk_values

        except Exception as e:
            print(f"✗ Error reading CSV file: {e}")
            return None

    def step2_create_scaled_piston_folders(self, lk_scale_values, geometry_values):
        """
        Step 2: Create IM_Scaled_piston folders, copy T* folders, and create modified geometry.txt files

        Args:
            lk_scale_values: List of LK scale values from CSV
            geometry_values: Dictionary containing all geometry values including lK, lZ0, lKG, lSK

        Returns:
            bool: True if successful, False otherwise
        """
        print("=" * 70)
        print("STEP 2: CREATING IM_Scaled_piston FOLDERS")
        print("=" * 70)

        try:
            simulation_folder = self.required_folders['simulation']
            zscalar_folder = self.required_folders['Zscalar']
            scalar_template_path = zscalar_folder / 'scalar.txt'

            # Extract base values from geometry
            base_lk = geometry_values.get('lK')
            base_lZ0 = geometry_values.get('lZ0')
            base_lKG = geometry_values.get('lKG')
            base_lSK = geometry_values.get('lSK')

            if None in [base_lk, base_lZ0, base_lKG, base_lSK]:
                print(f"✗ Missing required geometry values (lK, lZ0, lKG, lSK)")
                return False

            # Check if scalar.txt exists in Zscalar folder
            if not scalar_template_path.exists():
                print(f"✗ scalar.txt not found in Zscalar folder: {scalar_template_path}")
                return False

            print(f"\n📖 Reading scalar template from: {scalar_template_path}")

            # Read the scalar.txt template
            with open(scalar_template_path, 'r', encoding='utf-8', errors='replace') as f:
                scalar_lines = f.readlines()

            if len(scalar_lines) < 4:
                print(f"✗ scalar.txt does not have expected format (needs at least 4 lines)")
                return False

            # Find all T* simulation folders in the base simulation directory
            print(f"\n📂 Looking for T* simulation folders in: {simulation_folder}")
            t_folders = [f for f in simulation_folder.iterdir() if f.is_dir() and f.name.startswith('T')]

            if not t_folders:
                print(f"✗ No T* simulation folders found in {simulation_folder}")
                return False

            print(f"✓ Found {len(t_folders)} T* simulation folders:")
            for tf in t_folders:
                print(f"   - {tf.name}")

            print(f"\n✓ Base geometry values:")
            print(f"   lK  = {base_lk}")
            print(f"   lZ0 = {base_lZ0}")
            print(f"   lKG = {base_lKG}")
            print(f"   lSK = {base_lSK}")
            print(f"\n✓ Creating folders for {len(lk_scale_values)} scale values\n")

            created_folders = []

            # Create folders for each LK scale value
            for scale_value in lk_scale_values:
                # Create folder name
                folder_name = f"IM_Scaled_piston_{int(scale_value)}"
                folder_path = simulation_folder / folder_name

                # Create folder
                folder_path.mkdir(parents=True, exist_ok=True)
                print(f"   📁 Created folder: {folder_name}")

                # Create IM_piston folder inside the scaled folder
                im_piston_folder = folder_path / 'IM_piston'
                im_piston_folder.mkdir(parents=True, exist_ok=True)
                im_piston_path = str(im_piston_folder.resolve())
                print(f"      📁 Created IM_piston folder: {im_piston_path}")

                # Calculate scaled values
                scaled_lk = base_lk + scale_value
                scaled_lZ0 = base_lZ0 - scale_value
                scaled_lKG = base_lKG + (0.86 * scale_value)
                scaled_lSK = base_lSK + (0.45 * scale_value)

                # Create modified scalar.txt content
                modified_scalar = scalar_lines.copy()
                modified_scalar[3] = f"{base_lk} {scaled_lk}\n"

                # Write scalar.txt to the folder
                scalar_output_path = folder_path / 'scalar.txt'
                with open(scalar_output_path, 'w', encoding='utf-8') as f:
                    f.writelines(modified_scalar)

                print(f"      ✓ Created scalar.txt with values: {base_lk} {scaled_lk}")

                # Copy each T* folder into the IM_Scaled_piston folder
                for t_folder in t_folders:
                    dest_t_folder = folder_path / t_folder.name

                    # Copy the entire T* folder
                    if dest_t_folder.exists():
                        shutil.rmtree(dest_t_folder)
                    shutil.copytree(t_folder, dest_t_folder)

                    print(f"      📂 Copied {t_folder.name} folder")

                    # Copy and modify geometry.txt into the T*/input folder
                    input_folder = dest_t_folder / 'input'

                    # Ensure input folder exists
                    if not input_folder.exists():
                        input_folder.mkdir(parents=True, exist_ok=True)
                        print(f"         📁 Created input folder in {t_folder.name}")

                    geometry_dest = input_folder / 'geometry.txt'

                    # Read the base geometry.txt
                    with open(self.geometry_file, 'r', encoding='utf-8', errors='replace') as f:
                        geometry_content = f.read()

                    # Update the geometry values using regex
                    geometry_content = re.sub(
                        r'(^\s*lK\s+)[-+]?\d*\.?\d+',
                        lambda m: f'{m.group(1)}{scaled_lk}',
                        geometry_content,
                        flags=re.MULTILINE
                    )
                    geometry_content = re.sub(
                        r'(^\s*lZ0\s+)[-+]?\d*\.?\d+',
                        lambda m: f'{m.group(1)}{scaled_lZ0}',
                        geometry_content,
                        flags=re.MULTILINE
                    )
                    geometry_content = re.sub(
                        r'(^\s*lKG\s+)[-+]?\d*\.?\d+',
                        lambda m: f'{m.group(1)}{scaled_lKG}',
                        geometry_content,
                        flags=re.MULTILINE
                    )
                    geometry_content = re.sub(
                        r'(^\s*lSK\s+)[-+]?\d*\.?\d+',
                        lambda m: f'{m.group(1)}{scaled_lSK}',
                        geometry_content,
                        flags=re.MULTILINE
                    )

                    # Write modified geometry.txt
                    with open(geometry_dest, 'w', encoding='utf-8') as f:
                        f.write(geometry_content)

                    print(f"         ✓ Created geometry.txt in input folder with scaled values:")
                    print(f"            lK  = {scaled_lk:.6f}")
                    print(f"            lZ0 = {scaled_lZ0:.6f}")
                    print(f"            lKG = {scaled_lKG:.6f}")
                    print(f"            lSK = {scaled_lSK:.6f}")

                    # Update options_piston.txt with the correct IM_piston_path
                    options_piston_file = dest_t_folder / 'input' / 'options_piston.txt'

                    if options_piston_file.exists():
                        # Read the options_piston.txt file
                        # Use latin-1 encoding to preserve all bytes without decoding errors
                        with open(options_piston_file, 'r', encoding='latin-1') as f:
                            options_content = f.read()

                        # Replace the IM_piston_path line with the actual path
                        # Pattern matches: IM_piston_path followed by any path
                        options_content = re.sub(
                            r'(^\s*IM_piston_path\s+).*$',
                            lambda m: f'{m.group(1)}{im_piston_path}',
                            options_content,
                            flags=re.MULTILINE
                        )

                        # Write the updated content back
                        with open(options_piston_file, 'w', encoding='latin-1') as f:
                            f.write(options_content)

                        print(f"         ✓ Updated options_piston.txt with IM_piston_path:")
                        print(f"            {im_piston_path}")
                    else:
                        print(f"         ⚠ options_piston.txt not found in {t_folder.name}")

                created_folders.append(folder_name)

            print("\n" + "=" * 70)
            print(f"✓ Successfully created {len(created_folders)} folders:")
            for folder in created_folders:
                print(f"   - {folder}")
            print("=" * 70 + "\n")

            return True

        except Exception as e:
            print(f"✗ Error creating folders: {e}")
            import traceback
            traceback.print_exc()
            return False


class PistonScalingRunner:
    """Runner for piston scaling operations"""
    def __init__(self, base_folder):
        """
        Initialize the Piston Scaling Runner

        Args:
            base_folder: Path to the base folder containing all simulation files
        """
        self.base_folder = Path(base_folder)
        self.inp_folder = self.base_folder / 'INP'
        self.simulation_folder = self.base_folder / 'simulation'
        self.piston_pr_source = self.inp_folder / 'piston_pr.inp'

    def verify_files(self):
        """
        Verify that required files and folders exist

        Returns:
            bool: True if all required files exist, False otherwise
        """
        print("=" * 70)
        print("VERIFYING FILES AND FOLDERS")
        print("=" * 70)

        # Check base folder
        if not self.base_folder.exists():
            print(f"✗ Base folder NOT found: {self.base_folder}")
            return False
        print(f"✓ Base folder exists: {self.base_folder}")

        # Check INP folder
        if not self.inp_folder.exists():
            print(f"✗ INP folder NOT found: {self.inp_folder}")
            return False
        print(f"✓ INP folder exists: {self.inp_folder}")

        # Check piston_pr.inp
        if not self.piston_pr_source.exists():
            print(f"✗ piston_pr.inp NOT found: {self.piston_pr_source}")
            return False
        print(f"✓ piston_pr.inp exists: {self.piston_pr_source}")

        # Check simulation folder
        if not self.simulation_folder.exists():
            print(f"✗ simulation folder NOT found: {self.simulation_folder}")
            return False
        print(f"✓ simulation folder exists: {self.simulation_folder}")

        # Find IM_scaled_piston folders
        scaled_folders = list(self.simulation_folder.glob('IM_scaled_piston_*'))
        if not scaled_folders:
            print(f"✗ No IM_scaled_piston_* folders found in: {self.simulation_folder}")
            return False
        print(f"✓ Found {len(scaled_folders)} IM_scaled_piston_* folders")

        print("=" * 70 + "\n")
        return True

    def copy_piston_pr_files(self):
        """
        Copy piston_pr.inp from INP folder to each IM_piston folder

        Returns:
            list: List of IM_piston folders where files were copied
        """
        print("=" * 70)
        print("STEP 1: COPYING piston_pr.inp TO IM_piston FOLDERS")
        print("=" * 70)

        # Find all IM_scaled_piston folders
        scaled_folders = sorted(self.simulation_folder.glob('IM_scaled_piston_*'))

        if not scaled_folders:
            print("✗ No IM_scaled_piston_* folders found!")
            return []

        print(f"\nFound {len(scaled_folders)} IM_scaled_piston folders\n")

        copied_folders = []

        for scaled_folder in scaled_folders:
            # Find IM_piston folder inside
            im_piston_folder = scaled_folder / 'IM_piston'

            if not im_piston_folder.exists():
                print(f"⚠ IM_piston folder NOT found in: {scaled_folder.name}")
                print(f"  Creating IM_piston folder...")
                im_piston_folder.mkdir(parents=True, exist_ok=True)

            # Copy piston_pr.inp to IM_piston folder
            dest_file = im_piston_folder / 'piston_pr.inp'

            try:
                shutil.copy2(self.piston_pr_source, dest_file)
                print(f"✓ Copied to: {scaled_folder.name}/IM_piston/")
                copied_folders.append(im_piston_folder)
            except Exception as e:
                print(f"✗ Error copying to {scaled_folder.name}/IM_piston/: {e}")

        print(f"\n✓ Successfully copied piston_pr.inp to {len(copied_folders)} folders")
        print("=" * 70 + "\n")

        return copied_folders

    def scale_z_mesh(self, scalar_config_file):
        """
        Scale Z-coordinates in mesh based on configuration file
        This is the integrated Z_MeshScaler functionality

        Args:
            scalar_config_file: Path to the scalar.txt configuration file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Read the configuration file
            with open(scalar_config_file, 'r') as f:
                lines = f.readlines()

            if len(lines) < 4:
                print(f"   ✗ Error: scalar.txt must have at least 4 lines")
                return False

            original_inp = lines[0].strip()
            new_inp = lines[1].strip()
            z1, z1new = map(float, lines[2].strip().split())
            z2, z2new = map(float, lines[3].strip().split())

            # If paths are relative, resolve them relative to the scalar config file directory
            config_dir = Path(scalar_config_file).parent
            original_inp_path = config_dir / original_inp if not Path(original_inp).is_absolute() else Path(original_inp)
            new_inp_path = config_dir / new_inp if not Path(new_inp).is_absolute() else Path(new_inp)

            # Check if original input file exists
            if not original_inp_path.exists():
                print(f"   ✗ Error: Original .inp file not found: {original_inp_path}")
                return False

            # Read the original Abaqus input file
            with open(original_inp_path, 'r') as f:
                original_lines = f.readlines()

            # Write to the new scaled Abaqus input file
            with open(new_inp_path, 'w') as f:
                in_node_section = False
                for line in original_lines:
                    stripped_line = line.strip()
                    if stripped_line.startswith('*NODE'):
                        f.write(line)
                        in_node_section = True
                        continue
                    if in_node_section and stripped_line.startswith('*'):
                        in_node_section = False
                    if in_node_section and stripped_line:
                        # Parse node line: assuming format "node_id, x, y, z"
                        parts = [p.strip() for p in stripped_line.split(',')]
                        if len(parts) != 4:
                            # If not a valid node line, write it unchanged
                            f.write(line)
                            continue
                        node_id = parts[0]
                        try:
                            x = float(parts[1])
                            y = float(parts[2])
                            z = float(parts[3])
                        except ValueError:
                            # If parsing fails, write original line
                            f.write(line)
                            continue

                        # Scale Z-coordinate
                        if z <= z1:
                            new_z = z  # No change for Z <= Z1
                        elif z <= z2:
                            if z2 - z1 == 0:
                                new_z = z1new  # Avoid division by zero
                            else:
                                # Linear interpolation: new_z = z1new + (z - z1) * (z2new - z1new) / (z2 - z1)
                                new_z = z1new + (z - z1) * (z2new - z1new) / (z2 - z1)
                        else:
                            # Apply offset for Z > Z2
                            new_z = z + (z2new - z2)

                        # Write the scaled node with formatting similar to Abaqus style
                        f.write(f"{node_id:10}, {x:20.13E}, {y:20.13E}, {new_z:20.13E}\n")
                        continue
                    f.write(line)

            return True

        except Exception as e:
            print(f"   ✗ Error during Z-scaling: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_z_scaler(self):
        """
        Run Z mesh scaling for each IM_scaled_piston folder

        Returns:
            dict: Dictionary with folder names and their execution status
        """
        print("=" * 70)
        print("STEP 2: RUNNING Z MESH SCALING FOR EACH FOLDER")
        print("=" * 70)

        # Find all IM_scaled_piston folders
        scaled_folders = sorted(self.simulation_folder.glob('IM_scaled_piston_*'))

        if not scaled_folders:
            print("✗ No IM_scaled_piston_* folders found!")
            return {}

        print(f"\nProcessing {len(scaled_folders)} folders\n")

        results = {}

        for scaled_folder in scaled_folders:
            folder_name = scaled_folder.name
            scalar_file = scaled_folder / 'scalar.txt'

            # Check if scalar.txt exists
            if not scalar_file.exists():
                print(f"⚠ {folder_name}: scalar.txt NOT found, skipping...")
                results[folder_name] = 'skipped - no scalar.txt'
                continue

            print(f"📂 Processing: {folder_name}")
            print(f"   Scalar file: {scalar_file}")

            try:
                # Run integrated Z mesh scaler
                success = self.scale_z_mesh(str(scalar_file))

                if success:
                    print(f"   ✓ Successfully processed and scaled mesh")
                    results[folder_name] = 'success'
                else:
                    print(f"   ✗ Failed to scale mesh")
                    results[folder_name] = 'failed'

            except Exception as e:
                print(f"   ✗ Exception: {e}")
                results[folder_name] = f'error - {str(e)}'

            print()

        # Summary
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        success_count = sum(1 for v in results.values() if v == 'success')
        print(f"Total folders: {len(results)}")
        print(f"Successful:    {success_count}")
        print(f"Failed:        {len(results) - success_count}")
        print("=" * 70 + "\n")

        return results


class WorkerThread(QThread):
    """Worker thread for running batch setup without blocking GUI"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, base_folder, csv_file):
        super().__init__()
        self.base_folder = base_folder
        self.csv_file = csv_file

    def run(self):
        """Execute the actual setup process"""
        try:
            # Redirect print statements to GUI
            from io import StringIO
            import builtins

            # Custom print function that emits to GUI
            original_print = print
            def gui_print(*args, **kwargs):
                output = StringIO()
                # Remove 'file' from kwargs to avoid duplicate argument error
                kwargs_copy = kwargs.copy()
                kwargs_copy.pop('file', None)
                original_print(*args, file=output, **kwargs_copy)
                message = output.getvalue()
                self.output_signal.emit(message)
                original_print(*args, **kwargs)

            # Replace built-in print
            builtins.print = gui_print

            # Initialize the setup
            setup = DOEBatchSetup(self.base_folder)

            # Verify folder structure
            print("\n")
            print("╔" + "═" * 68 + "╗")
            print("║" + " " * 15 + "DOE BATCH SIMULATION SETUP" + " " * 27 + "║")
            print("╚" + "═" * 68 + "╝")
            print("\n")

            status = setup.verify_folder_structure()

            # Check if we can proceed
            if not all([status.get('base_folder'), status.get('INP'),
                        status.get('Zscalar'), status.get('geometry_txt')]):
                print("❌ Cannot proceed due to missing critical files/folders.")
                print("Please ensure the folder structure is correct and try again.")
                self.finished_signal.emit(False, "Missing critical files/folders. Check the output log.")
                builtins.print = original_print
                return

            # Read lK_scale_values from CSV
            lk_values = setup.read_lk_scale_values(self.csv_file)

            if not lk_values:
                print("❌ Could not read lK_scale_values from CSV file.")
                self.finished_signal.emit(False, "Failed to read CSV file. Check the output log.")
                builtins.print = original_print
                return

            # Execute Step 0
            step0_success = setup.step0_copy_piston_pr()

            # Execute Step 1
            geometry_values = setup.step1_extract_geometry_values()

            # Execute Step 2 - Create IM_Scaled_piston folders
            step2_success = False
            if geometry_values and lk_values:
                step2_success = setup.step2_create_scaled_piston_folders(lk_values, geometry_values)

            # Summary
            print("=" * 70)
            print("SETUP SUMMARY")
            print("=" * 70)
            print(f"Step 0 (Copy piston_pr.inp):       {'✓ SUCCESS' if step0_success else '✗ FAILED'}")
            print(f"Step 1 (Extract geometry):         {'✓ SUCCESS' if geometry_values else '✗ FAILED'}")
            print(f"Step 2 (Create scaled folders):    {'✓ SUCCESS' if step2_success else '✗ FAILED'}")
            print(f"CSV lK_scale_values read:          ✓ SUCCESS ({len(lk_values)} values)")
            print("=" * 70)

            if geometry_values and lk_values and step2_success:
                print("\n✓ Setup complete! You can now proceed with the next steps.")
                print(f"\nExtracted geometry values:")
                for key, val in geometry_values.items():
                    print(f"  {key}: {val}")
                print(f"\nlK_scale_values from CSV: {lk_values}")
                print(f"\n✓ Created {len(lk_values)} IM_Scaled_piston folders in simulation directory")
                self.finished_signal.emit(True, f"Batch setup completed successfully!\n{len(lk_values)} folders created with scalar.txt files.")
            else:
                print("\n⚠ Setup completed with warnings. Please check the errors above.")
                self.finished_signal.emit(False, "Setup completed with warnings. Check the output log.")

            print("\n")

            # Restore original print
            builtins.print = original_print

        except Exception as e:
            self.output_signal.emit(f"\n✗ Error during setup: {e}\n")
            self.finished_signal.emit(False, f"An error occurred: {e}")
            import builtins
            builtins.print = original_print


class PistonScalingWorker(QThread):
    """Worker thread for piston scaling operations"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, base_folder, operation='both'):
        super().__init__()
        self.base_folder = base_folder
        self.operation = operation  # 'copy', 'scale', or 'both'

    def run(self):
        """Execute the piston scaling process"""
        try:
            # Redirect print statements to GUI
            from io import StringIO
            import builtins

            # Custom print function that emits to GUI
            original_print = print
            def gui_print(*args, **kwargs):
                output = StringIO()
                kwargs_copy = kwargs.copy()
                kwargs_copy.pop('file', None)
                original_print(*args, file=output, **kwargs_copy)
                message = output.getvalue()
                self.output_signal.emit(message)
                original_print(*args, **kwargs)

            # Replace built-in print
            builtins.print = gui_print

            # Initialize runner
            print("\n")
            print("╔" + "═" * 68 + "╗")
            print("║" + " " * 18 + "PISTON SCALING RUNNER" + " " * 29 + "║")
            print("╚" + "═" * 68 + "╝")
            print("\n")

            runner = PistonScalingRunner(self.base_folder)

            # Verify files
            if not runner.verify_files():
                print("✗ Verification failed. Please check the errors above.")
                self.finished_signal.emit(False, "Verification failed. Check the output log.")
                builtins.print = original_print
                return

            # Execute operations based on selected mode
            copied_folders = []
            results = {}

            if self.operation in ['copy', 'both']:
                copied_folders = runner.copy_piston_pr_files()
                if not copied_folders and self.operation == 'copy':
                    print("⚠ No files were copied.")
                    self.finished_signal.emit(False, "No files were copied. Check the output log.")
                    builtins.print = original_print
                    return

            if self.operation in ['scale', 'both']:
                results = runner.run_z_scaler()

                if not results:
                    print("⚠ No folders were processed.")
                    self.finished_signal.emit(False, "No folders were processed. Check the output log.")
                    builtins.print = original_print
                    return

                # Check results
                success_count = sum(1 for v in results.values() if v == 'success')
                if all(v == 'success' for v in results.values()):
                    print("✓ All folders processed successfully!")
                    self.finished_signal.emit(True, f"Piston scaling completed successfully!\n{success_count} folders processed.")
                else:
                    print("⚠ Some folders failed to process. Check the summary above.")
                    self.finished_signal.emit(False, f"Some folders failed.\n{success_count}/{len(results)} successful.")
            elif self.operation == 'copy':
                print("✓ Copy operation completed successfully!")
                self.finished_signal.emit(True, f"Copied piston_pr.inp to {len(copied_folders)} folders.")

            # Restore original print
            builtins.print = original_print

        except Exception as e:
            self.output_signal.emit(f"\n✗ Error during piston scaling: {e}\n")
            self.finished_signal.emit(False, f"An error occurred: {e}")
            import builtins
            builtins.print = original_print


class DOEBatchGUI(QMainWindow):
    """
    GUI for DOE Batch Setup using PyQt5
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DOE Batch Simulation Setup")
        self.setGeometry(100, 100, 800, 600)

        # Variables
        self.base_folder_path = ""
        self.csv_file_path = ""
        self.worker_thread = None
        self.piston_scaling_worker = None

        # Create GUI elements
        self.create_widgets()

    def create_widgets(self):
        """Create all GUI widgets"""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Title
        title_frame = QFrame()
        title_frame.setStyleSheet("background-color: #2c3e50; padding: 10px;")
        title_layout = QVBoxLayout()
        title_frame.setLayout(title_layout)

        title_label = QLabel("DOE BATCH SIMULATION SETUP")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setStyleSheet("color: white;")
        title_label.setAlignment(Qt.AlignCenter)
        title_layout.addWidget(title_label)

        main_layout.addWidget(title_frame)

        # Input section
        input_widget = QWidget()
        input_widget.setContentsMargins(20, 20, 20, 20)
        input_layout = QVBoxLayout()
        input_widget.setLayout(input_layout)

        # Base Folder Selection
        base_folder_layout = QHBoxLayout()
        base_folder_label = QLabel("Base Folder Path:")
        base_folder_label.setFont(QFont("Arial", 10, QFont.Bold))
        base_folder_label.setMinimumWidth(180)
        base_folder_layout.addWidget(base_folder_label)

        self.base_folder_entry = QLineEdit()
        self.base_folder_entry.setMinimumWidth(400)
        base_folder_layout.addWidget(self.base_folder_entry)

        base_folder_button = QPushButton("Browse")
        base_folder_button.setMaximumWidth(100)
        base_folder_button.clicked.connect(self.browse_base_folder)
        base_folder_layout.addWidget(base_folder_button)

        input_layout.addLayout(base_folder_layout)

        # CSV File Selection
        csv_file_layout = QHBoxLayout()
        csv_file_label = QLabel("CSV File (lK_scale_value):")
        csv_file_label.setFont(QFont("Arial", 10, QFont.Bold))
        csv_file_label.setMinimumWidth(180)
        csv_file_layout.addWidget(csv_file_label)

        self.csv_file_entry = QLineEdit()
        self.csv_file_entry.setMinimumWidth(400)
        csv_file_layout.addWidget(self.csv_file_entry)

        csv_file_button = QPushButton("Browse")
        csv_file_button.setMaximumWidth(100)
        csv_file_button.clicked.connect(self.browse_csv_file)
        csv_file_layout.addWidget(csv_file_button)

        input_layout.addLayout(csv_file_layout)

        main_layout.addWidget(input_widget)

        # Run Button
        button_widget = QWidget()
        button_layout = QHBoxLayout()
        button_widget.setLayout(button_layout)

        self.run_button = QPushButton("Run Batch Setup")
        self.run_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 15px 30px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.run_button.clicked.connect(self.run_setup)
        button_layout.addStretch()
        button_layout.addWidget(self.run_button)
        button_layout.addStretch()

        main_layout.addWidget(button_widget)

        # Piston Scaling Section
        piston_scaling_group = QGroupBox("Piston Scaling Operations")
        piston_scaling_group.setStyleSheet("QGroupBox { font-weight: bold; margin-top: 10px; }")
        piston_layout = QVBoxLayout()
        piston_scaling_group.setLayout(piston_layout)

        # Info label
        info_label = QLabel("Run piston scaling operations on IM_scaled_piston folders:")
        info_label.setWordWrap(True)
        piston_layout.addWidget(info_label)

        # Button layout
        piston_button_layout = QHBoxLayout()

        # Copy Only button
        self.copy_only_button = QPushButton("Copy piston_pr.inp Files")
        self.copy_only_button.setFont(QFont("Arial", 10))
        self.copy_only_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.copy_only_button.clicked.connect(lambda: self.run_piston_scaling('copy'))
        piston_button_layout.addWidget(self.copy_only_button)

        # Scale Only button
        self.scale_only_button = QPushButton("Run Z Mesh Scaling Only")
        self.scale_only_button.setFont(QFont("Arial", 10))
        self.scale_only_button.setStyleSheet("""
            QPushButton {
                background-color: #e67e22;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #d35400;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.scale_only_button.clicked.connect(lambda: self.run_piston_scaling('scale'))
        piston_button_layout.addWidget(self.scale_only_button)

        # Both operations button
        self.run_both_button = QPushButton("Copy & Scale (Both)")
        self.run_both_button.setFont(QFont("Arial", 10))
        self.run_both_button.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.run_both_button.clicked.connect(lambda: self.run_piston_scaling('both'))
        piston_button_layout.addWidget(self.run_both_button)

        piston_layout.addLayout(piston_button_layout)
        main_layout.addWidget(piston_scaling_group)

        # Output Text Area
        output_widget = QWidget()
        output_widget.setContentsMargins(20, 10, 20, 20)
        output_layout = QVBoxLayout()
        output_widget.setLayout(output_layout)

        output_label = QLabel("Output Log:")
        output_label.setFont(QFont("Arial", 10, QFont.Bold))
        output_layout.addWidget(output_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Courier", 9))
        self.output_text.setStyleSheet("background-color: #f8f9fa;")
        output_layout.addWidget(self.output_text)

        main_layout.addWidget(output_widget)

    def browse_base_folder(self):
        """Browse for base folder"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Select Base Folder",
            "",
            QFileDialog.ShowDirsOnly
        )
        if folder_path:
            self.base_folder_path = folder_path
            self.base_folder_entry.setText(folder_path)
            self.log_output(f"Base folder selected: {folder_path}\n")

    def browse_csv_file(self):
        """Browse for CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV File",
            "",
            "CSV files (*.csv);;All files (*.*)"
        )
        if file_path:
            self.csv_file_path = file_path
            self.csv_file_entry.setText(file_path)
            self.log_output(f"CSV file selected: {file_path}\n")

    def log_output(self, message):
        """Log message to output text area"""
        self.output_text.insertPlainText(message)
        self.output_text.moveCursor(self.output_text.textCursor().End)

    def run_setup(self):
        """Run the batch setup process"""
        base_folder = self.base_folder_entry.text()
        csv_file = self.csv_file_entry.text()

        # Validate inputs
        if not base_folder:
            QMessageBox.critical(self, "Error", "Please select a base folder!")
            return

        if not csv_file:
            QMessageBox.critical(self, "Error", "Please select a CSV file!")
            return

        # Disable run button
        self.run_button.setEnabled(False)
        self.run_button.setText("Running...")
        self.output_text.clear()

        # Create and start worker thread
        self.worker_thread = WorkerThread(base_folder, csv_file)
        self.worker_thread.output_signal.connect(self.log_output)
        self.worker_thread.finished_signal.connect(self.on_setup_finished)
        self.worker_thread.start()

    def on_setup_finished(self, success, message):
        """Handle completion of setup process"""
        # Re-enable run button
        self.run_button.setEnabled(True)
        self.run_button.setText("Run Batch Setup")

        # Show result message
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            if "warning" in message.lower():
                QMessageBox.warning(self, "Warning", message)
            else:
                QMessageBox.critical(self, "Error", message)

    def run_piston_scaling(self, operation):
        """Run piston scaling operations"""
        base_folder = self.base_folder_entry.text()

        # Validate input
        if not base_folder:
            QMessageBox.critical(self, "Error", "Please select a base folder first!")
            return

        # Disable buttons
        self.copy_only_button.setEnabled(False)
        self.scale_only_button.setEnabled(False)
        self.run_both_button.setEnabled(False)

        # Update button text based on operation
        if operation == 'copy':
            self.copy_only_button.setText("Running...")
        elif operation == 'scale':
            self.scale_only_button.setText("Running...")
        else:
            self.run_both_button.setText("Running...")

        self.output_text.clear()

        # Create and start worker thread
        self.piston_scaling_worker = PistonScalingWorker(base_folder, operation)
        self.piston_scaling_worker.output_signal.connect(self.log_output)
        self.piston_scaling_worker.finished_signal.connect(self.on_piston_scaling_finished)
        self.piston_scaling_worker.start()

    def on_piston_scaling_finished(self, success, message):
        """Handle completion of piston scaling process"""
        # Re-enable buttons
        self.copy_only_button.setEnabled(True)
        self.scale_only_button.setEnabled(True)
        self.run_both_button.setEnabled(True)

        # Reset button texts
        self.copy_only_button.setText("Copy piston_pr.inp Files")
        self.scale_only_button.setText("Run Z Mesh Scaling Only")
        self.run_both_button.setText("Copy & Scale (Both)")

        # Show result message
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            if "warning" in message.lower():
                QMessageBox.warning(self, "Warning", message)
            else:
                QMessageBox.critical(self, "Error", message)


def main():
    """
    Main function to run the DOE batch setup with GUI
    """
    app = QApplication(sys.argv)
    window = DOEBatchGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
