#!/usr/bin/env python3
"""
Piston Scaling Runner Script
This script copies piston_pr.inp files and runs Z_MeshScaler.py for each scaled folder
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


class PistonScalingRunner:
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

    def run_z_scaler(self):
        """
        Run Z_MeshScaler.py for each IM_scaled_piston folder

        Returns:
            dict: Dictionary with folder names and their execution status
        """
        print("=" * 70)
        print("STEP 2: RUNNING Z_MeshScaler.py FOR EACH FOLDER")
        print("=" * 70)

        # Find all IM_scaled_piston folders
        scaled_folders = sorted(self.simulation_folder.glob('IM_scaled_piston_*'))

        if not scaled_folders:
            print("✗ No IM_scaled_piston_* folders found!")
            return {}

        print(f"\nProcessing {len(scaled_folders)} folders\n")

        results = {}
        script_path = Path(__file__).parent / 'Z_MeshScaler.py'

        if not script_path.exists():
            print(f"✗ Z_MeshScaler.py NOT found at: {script_path}")
            return {}

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
                # Run Z_MeshScaler.py with the scalar.txt file
                result = subprocess.run(
                    [sys.executable, str(script_path), str(scalar_file)],
                    cwd=str(scaled_folder),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )

                if result.returncode == 0:
                    print(f"   ✓ Successfully processed")
                    if result.stdout:
                        print(f"   Output: {result.stdout.strip()}")
                    results[folder_name] = 'success'
                else:
                    print(f"   ✗ Error (return code: {result.returncode})")
                    if result.stderr:
                        print(f"   Error: {result.stderr.strip()}")
                    results[folder_name] = f'failed - {result.returncode}'

            except subprocess.TimeoutExpired:
                print(f"   ✗ Timeout (exceeded 5 minutes)")
                results[folder_name] = 'timeout'
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


def main():
    """
    Main function to run piston scaling
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Copy piston_pr.inp and run Z_MeshScaler.py for scaled folders'
    )
    parser.add_argument(
        'base_folder',
        help='Path to the base folder containing INP and simulation folders'
    )
    parser.add_argument(
        '--copy-only',
        action='store_true',
        help='Only copy piston_pr.inp files, do not run Z_MeshScaler.py'
    )
    parser.add_argument(
        '--scale-only',
        action='store_true',
        help='Only run Z_MeshScaler.py, do not copy files'
    )

    args = parser.parse_args()

    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 18 + "PISTON SCALING RUNNER" + " " * 29 + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")

    # Initialize runner
    runner = PistonScalingRunner(args.base_folder)

    # Verify files
    if not runner.verify_files():
        print("✗ Verification failed. Please check the errors above.")
        sys.exit(1)

    # Execute steps
    if not args.scale_only:
        copied_folders = runner.copy_piston_pr_files()
        if not copied_folders and not args.copy_only:
            print("⚠ No files were copied. Continuing anyway...")

    if not args.copy_only:
        results = runner.run_z_scaler()

        # Check if all succeeded
        if all(v == 'success' for v in results.values()):
            print("✓ All folders processed successfully!")
            sys.exit(0)
        else:
            print("⚠ Some folders failed to process. Check the summary above.")
            sys.exit(1)
    else:
        print("✓ Copy-only mode: Files copied successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
