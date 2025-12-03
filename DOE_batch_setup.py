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
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QTextEdit, QFileDialog, QMessageBox, QFrame)
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
                original_print(*args, file=output, **kwargs)
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
                self.finished_signal.emit(True, f"Batch setup completed successfully!\n{len(lk_values)} lK_scale_values loaded.")
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
