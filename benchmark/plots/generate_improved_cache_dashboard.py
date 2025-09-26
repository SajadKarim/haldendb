#!/usr/bin/env python3
"""
Quick script to generate the improved 3x5 cache performance dashboard
with legend in top left of first subplot
"""

import subprocess
import sys
import os

def main():
    # Your exact file paths
    vanilla_csv = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250924_171318/combined_benchmark_results_with_perf_20250924_220907.csv"
    optimized_csv = "/home/skarim/Code/haldendb_ex/haldendb_pvt/benchmark/build/cache_profiling_results_20250925_004057_default_configs_only/combined_benchmark_results_with_perf_20250925_151521.csv"
    
    # Output file with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"cache_performance_dashboard_{timestamp}.pdf"
    
    # Script path
    script_path = os.path.join(os.path.dirname(__file__), "cache_performance_comparison.py")
    
    # Command to run
    cmd = [
        sys.executable, script_path,
        '--vanilla-csv', vanilla_csv,
        '--optimized-csv', optimized_csv,
        '--output', output_file,
        '--plot-type', 'dashboard'
    ]
    
    print("Generating improved cache performance dashboard (5x3 layout)...")
    print("Layout: 5 metrics (rows) x 3 storage types (columns)")
    print(f"Output: {output_file}")
    print("="*60)
    
    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✓ Success! Dashboard saved to: {output_file}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error: {e}")
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)