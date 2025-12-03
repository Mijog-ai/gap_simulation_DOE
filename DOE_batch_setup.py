#!/usr/bin/env python3
"""
DOE Batch Simulation Setup Script
This script prepares the environment for batch runs of MZ simulation
"""

import os
import shutil
import re
import csv
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path
import threading


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
            with open(csv_path, 'r') as f:
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


class DOEBatchGUI:
    """
    GUI for DOE Batch Setup
    """
    def __init__(self, root):
        self.root = root
        self.root.title("DOE Batch Simulation Setup")
        self.root.geometry("800x600")

        # Variables
        self.base_folder_var = tk.StringVar()
        self.csv_file_var = tk.StringVar()

        # Create GUI elements
        self.create_widgets()

    def create_widgets(self):
        """Create all GUI widgets"""
        # Title
        title_frame = tk.Frame(self.root, bg="#2c3e50", pady=10)
        title_frame.pack(fill=tk.X)

        title_label = tk.Label(
            title_frame,
            text="DOE BATCH SIMULATION SETUP",
            font=("Arial", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack()

        # Input Frame
        input_frame = tk.Frame(self.root, padx=20, pady=20)
        input_frame.pack(fill=tk.X)

        # Base Folder Selection
        tk.Label(
            input_frame,
            text="Base Folder Path:",
            font=("Arial", 10, "bold")
        ).grid(row=0, column=0, sticky="w", pady=5)

        tk.Entry(
            input_frame,
            textvariable=self.base_folder_var,
            width=60
        ).grid(row=0, column=1, padx=5, pady=5)

        tk.Button(
            input_frame,
            text="Browse",
            command=self.browse_base_folder,
            width=10
        ).grid(row=0, column=2, padx=5, pady=5)

        # CSV File Selection
        tk.Label(
            input_frame,
            text="CSV File (lK_scale_value):",
            font=("Arial", 10, "bold")
        ).grid(row=1, column=0, sticky="w", pady=5)

        tk.Entry(
            input_frame,
            textvariable=self.csv_file_var,
            width=60
        ).grid(row=1, column=1, padx=5, pady=5)

        tk.Button(
            input_frame,
            text="Browse",
            command=self.browse_csv_file,
            width=10
        ).grid(row=1, column=2, padx=5, pady=5)

        # Run Button
        button_frame = tk.Frame(self.root, pady=10)
        button_frame.pack()

        self.run_button = tk.Button(
            button_frame,
            text="Run Batch Setup",
            command=self.run_setup,
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            width=20,
            height=2
        )
        self.run_button.pack()

        # Output Text Area
        output_frame = tk.Frame(self.root, padx=20, pady=10)
        output_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            output_frame,
            text="Output Log:",
            font=("Arial", 10, "bold")
        ).pack(anchor="w")

        self.output_text = scrolledtext.ScrolledText(
            output_frame,
            wrap=tk.WORD,
            font=("Courier", 9),
            bg="#f8f9fa"
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

    def browse_base_folder(self):
        """Browse for base folder"""
        folder_path = filedialog.askdirectory(title="Select Base Folder")
        if folder_path:
            self.base_folder_var.set(folder_path)
            self.log_output(f"Base folder selected: {folder_path}\n")

    def browse_csv_file(self):
        """Browse for CSV file"""
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if file_path:
            self.csv_file_var.set(file_path)
            self.log_output(f"CSV file selected: {file_path}\n")

    def log_output(self, message):
        """Log message to output text area"""
        self.output_text.insert(tk.END, message)
        self.output_text.see(tk.END)
        self.root.update_idletasks()

    def run_setup(self):
        """Run the batch setup process"""
        base_folder = self.base_folder_var.get()
        csv_file = self.csv_file_var.get()

        # Validate inputs
        if not base_folder:
            messagebox.showerror("Error", "Please select a base folder!")
            return

        if not csv_file:
            messagebox.showerror("Error", "Please select a CSV file!")
            return

        # Disable run button
        self.run_button.config(state=tk.DISABLED, text="Running...")
        self.output_text.delete(1.0, tk.END)

        # Run in a separate thread to keep GUI responsive
        thread = threading.Thread(target=self.execute_setup, args=(base_folder, csv_file))
        thread.daemon = True
        thread.start()

    def execute_setup(self, base_folder, csv_file):
        """Execute the actual setup process"""
        try:
            # Redirect print statements to GUI
            import sys
            from io import StringIO

            # Custom print function that also outputs to GUI
            original_print = print
            def gui_print(*args, **kwargs):
                output = StringIO()
                original_print(*args, file=output, **kwargs)
                message = output.getvalue()
                self.log_output(message)
                original_print(*args, **kwargs)

            # Replace built-in print
            import builtins
            builtins.print = gui_print

            # Initialize the setup
            setup = DOEBatchSetup(base_folder)

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
                messagebox.showerror("Error", "Missing critical files/folders. Check the output log.")
                return

            # Read lK_scale_values from CSV
            lk_values = setup.read_lk_scale_values(csv_file)

            if not lk_values:
                print("❌ Could not read lK_scale_values from CSV file.")
                messagebox.showerror("Error", "Failed to read CSV file. Check the output log.")
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
            print(f"CSV lK_scale_values read:    ✓ SUCCESS ({len(lk_values)} values)")
            print("=" * 70)

            if geometry_values and lk_values:
                print("\n✓ Setup complete! You can now proceed with the next steps.")
                print(f"\nExtracted geometry values:")
                for key, val in geometry_values.items():
                    print(f"  {key}: {val}")
                print(f"\nlK_scale_values from CSV: {lk_values}")
                messagebox.showinfo("Success", f"Batch setup completed successfully!\n{len(lk_values)} lK_scale_values loaded.")
            else:
                print("\n⚠ Setup completed with warnings. Please check the errors above.")
                messagebox.showwarning("Warning", "Setup completed with warnings. Check the output log.")

            print("\n")

            # Restore original print
            builtins.print = original_print

        except Exception as e:
            self.log_output(f"\n✗ Error during setup: {e}\n")
            messagebox.showerror("Error", f"An error occurred: {e}")
            import builtins
            builtins.print = original_print

        finally:
            # Re-enable run button
            self.run_button.config(state=tk.NORMAL, text="Run Batch Setup")


def main():
    """
    Main function to run the DOE batch setup with GUI
    """
    root = tk.Tk()
    app = DOEBatchGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
