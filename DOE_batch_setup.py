#!/usr/bin/env python3
"""
DOE Batch Simulation Setup Script
This script prepares the environment for batch runs of MZ simulation
"""

import os
import shutil
import re
from pathlib import Path


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
                response = input("Do you want to overwrite it? (y/n): ").lower()
                if response != 'y':
                    print("Skipping copy operation.")
                    return True
            
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
            
            with open(self.geometry_file, 'r') as f:
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


def main():
    """
    Main function to run the DOE batch setup
    """
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "DOE BATCH SIMULATION SETUP" + " " * 27 + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")
    
    # Get base folder path from user or use current directory
    base_folder = "H:/Base_folder"
    if not base_folder:
        base_folder = os.getcwd()
    
    # Initialize the setup
    setup = DOEBatchSetup(base_folder)
    
    # Verify folder structure
    status = setup.verify_folder_structure()
    
    # Check if we can proceed
    if not all([status.get('base_folder'), status.get('INP'), 
                status.get('Zscalar'), status.get('geometry_txt')]):
        print("❌ Cannot proceed due to missing critical files/folders.")
        print("Please ensure the folder structure is correct and try again.")
        return
    
    # Ask user if they want to proceed
    response = input("\nDo you want to proceed with Step 0 and Step 1? (y/n): ").lower()
    if response != 'y':
        print("Operation cancelled by user.")
        return
    
    # Execute Step 0
    step0_success = setup.step0_copy_piston_pr()
    
    # Execute Step 1
    geometry_values = setup.step1_extract_geometry_values()
    
    # Summary
    print("=" * 70)
    print("SETUP SUMMARY")
    print("=" * 70)
    print(f"Step 0 (Copy piston_pr.inp): {'✓ SUCCESS' if step0_success else '✗ FAILED'}")
    print(f"Step 1 (Extract geometry):   {'✓ SUCCESS' if geometry_values else '✗ FAILED'}")
    print("=" * 70)
    
    if geometry_values:
        print("\n✓ Setup complete! You can now proceed with the next steps.")
        print(f"\nExtracted values are stored in the geometry_values dictionary:")
        print(f"  {geometry_values}")
    else:
        print("\n⚠ Setup completed with warnings. Please check the errors above.")
    
    print("\n")


if __name__ == "__main__":
    main()
