#!/usr/bin/env python3
"""
Master script to generate comprehensive cache performance analysis
Generates multiple types of visualizations comparing vanilla vs optimized variants
"""

import argparse
import subprocess
import sys
import os

def run_script(script_name, vanilla_csv, optimized_csv, output_prefix):
    """Run a plotting script with the given parameters"""
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    output_file = f"{output_prefix}_{script_name.replace('.py', '.pdf')}"
    
    cmd = [
        sys.executable, script_path,
        '--vanilla-csv', vanilla_csv,
        '--optimized-csv', optimized_csv,
        '--output', output_file
    ]
    
    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print(f"Output: {output_file}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✓ Success!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error running {script_name}:")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"✗ Unexpected error running {script_name}: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Generate comprehensive cache performance analysis')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output-prefix', default='cache_analysis', help='Prefix for output files')
    parser.add_argument('--plots', nargs='+', 
                       choices=['dashboard', 'radar', 'differences', 'all'],
                       default=['all'],
                       help='Which plots to generate')
    
    args = parser.parse_args()
    
    # Verify input files exist
    if not os.path.exists(args.vanilla_csv):
        print(f"Error: Vanilla CSV file not found: {args.vanilla_csv}")
        sys.exit(1)
    
    if not os.path.exists(args.optimized_csv):
        print(f"Error: Optimized CSV file not found: {args.optimized_csv}")
        sys.exit(1)
    
    # Define available scripts
    scripts = {
        'dashboard': 'cache_performance_comparison.py',
        'radar': 'cache_performance_radar.py', 
        'differences': 'cache_performance_differences.py'
    }
    
    # Determine which scripts to run
    if 'all' in args.plots:
        scripts_to_run = list(scripts.keys())
    else:
        scripts_to_run = args.plots
    
    print("Cache Performance Analysis Generator")
    print("="*50)
    print(f"Vanilla CSV: {args.vanilla_csv}")
    print(f"Optimized CSV: {args.optimized_csv}")
    print(f"Output prefix: {args.output_prefix}")
    print(f"Plots to generate: {', '.join(scripts_to_run)}")
    
    # Run selected scripts
    results = {}
    for plot_type in scripts_to_run:
        if plot_type in scripts:
            success = run_script(scripts[plot_type], args.vanilla_csv, args.optimized_csv, args.output_prefix)
            results[plot_type] = success
        else:
            print(f"Warning: Unknown plot type '{plot_type}' - skipping")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    successful = sum(results.values())
    total = len(results)
    
    for plot_type, success in results.items():
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{plot_type:15} {status}")
    
    print(f"\nCompleted: {successful}/{total} plots generated successfully")
    
    if successful > 0:
        print(f"\nGenerated files:")
        for plot_type, success in results.items():
            if success:
                output_file = f"{args.output_prefix}_{scripts[plot_type].replace('.py', '.pdf')}"
                print(f"  - {output_file}")
                
                # Also mention additional files that might be generated
                if plot_type == 'dashboard':
                    heatmap_file = output_file.replace('.pdf', '_heatmap.pdf')
                    if os.path.exists(heatmap_file):
                        print(f"  - {heatmap_file}")
                elif plot_type == 'radar':
                    summary_file = output_file.replace('.pdf', '_summary.pdf')
                    if os.path.exists(summary_file):
                        print(f"  - {summary_file}")
                elif plot_type == 'differences':
                    summary_file = output_file.replace('.pdf', '_summary.pdf')
                    csv_file = output_file.replace('.pdf', '_summary.csv')
                    if os.path.exists(summary_file):
                        print(f"  - {summary_file}")
                    if os.path.exists(csv_file):
                        print(f"  - {csv_file}")
    
    if successful < total:
        print(f"\nSome plots failed to generate. Check the error messages above.")
        sys.exit(1)
    else:
        print(f"\nAll plots generated successfully! 🎉")

if __name__ == "__main__":
    main()