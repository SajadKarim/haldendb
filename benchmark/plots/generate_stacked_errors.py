#!/usr/bin/env python3
"""
Generate Option 1 Overlay with Stacked Error Bars using discovered CSV paths
"""

import subprocess
import sys
import os

def main():
    # Use the same CSV paths as used in thread comparison
    vanilla_csv = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250924_171318/combined_benchmark_results_with_perf_20250924_220907.csv"
    optimized_csv = "/home/skarim/Code/haldendb_ex/haldendb_pvt/benchmark/build/cache_profiling_results_20250925_004057_default_configs_only/combined_benchmark_results_with_perf_20250925_151521.csv"
    
    output_path = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/plots/option1_overlay_stacked_errors.pdf"
    
    # Check if CSV files exist
    if not os.path.exists(vanilla_csv):
        print(f"❌ Vanilla CSV not found: {vanilla_csv}")
        return 1
    
    if not os.path.exists(optimized_csv):
        print(f"❌ Optimized CSV not found: {optimized_csv}")
        return 1
    
    print("🚀 Generating Option 1 Overlay with Stacked Error Bars...")
    print(f"📊 Vanilla data: {vanilla_csv}")
    print(f"📊 Optimized data: {optimized_csv}")
    print(f"💾 Output: {output_path}")
    
    # Run the plot generation
    cmd = [
        sys.executable,
        "/home/skarim/Code/haldendb_ex/haldendb/benchmark/plots/option1_overlay_stacked_errors.py",
        "--vanilla-csv", vanilla_csv,
        "--optimized-csv", optimized_csv,
        "--output", output_path
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Plot generated successfully!")
        print(result.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating plot: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())