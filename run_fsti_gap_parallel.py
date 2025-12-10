#!/usr/bin/env python3
"""
Simple command-line runner for fsti_gap.exe parallel execution
"""
import sys
from pathlib import Path
from DOE_batch_setup import GapExeRunner

def main():
    # Get base folder (default to current directory if not provided)
    if len(sys.argv) > 1:
        base_folder = sys.argv[1]
    else:
        base_folder = str(Path.cwd())

    # Get max workers (optional)
    max_workers = None
    if len(sys.argv) > 2:
        try:
            max_workers = int(sys.argv[2])
        except ValueError:
            print(f"Warning: Invalid max_workers value '{sys.argv[2]}', using default")

    print(f"Base folder: {base_folder}")
    print(f"Max workers: {max_workers if max_workers else 'auto (CPU count)'}")
    print()

    # Create runner and execute
    runner = GapExeRunner(base_folder)

    # Run parallel execution
    results = runner.run_gap_exe_parallel(max_workers=max_workers, show_console=True)

    # Exit with appropriate code
    if results:
        success_count = sum(1 for v in results.values() if v['success'])
        if success_count == len(results):
            print("\n✓ All executions completed successfully!")
            sys.exit(0)
        else:
            print(f"\n⚠ {len(results) - success_count} executions failed")
            sys.exit(1)
    else:
        print("\n✗ No T folders found to process")
        sys.exit(1)

if __name__ == "__main__":
    main()
