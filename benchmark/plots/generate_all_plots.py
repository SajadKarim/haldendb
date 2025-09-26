#!/usr/bin/env python3
"""
Generate all performance visualization plots
Runs both the throughput comparison and detailed metrics analysis
"""

import subprocess
import sys
import argparse
import os

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Generating {description}...")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Warnings:", result.stderr)
        print(f"✓ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error generating {description}:")
        print(f"Exit code: {e.returncode}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return False

def main():
    parser = argparse.ArgumentParser(description='Generate all performance visualization plots')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output-dir', default='.', help='Output directory for plots')
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    success_count = 0
    total_plots = 0
    
    # 1. Generate throughput comparison (Option 1)
    total_plots += 1
    cmd1 = [
        'python', os.path.join(script_dir, 'option1_overlay_comparison.py'),
        '--vanilla-csv', args.vanilla_csv,
        '--optimized-csv', args.optimized_csv,
        '--output', os.path.join(args.output_dir, 'option1_throughput_comparison.pdf')
    ]
    if run_command(cmd1, "Throughput Comparison Plot (Option 1)"):
        success_count += 1
    
    # 2. Generate detailed metrics analysis (Option 2)
    total_plots += 1
    cmd2 = [
        'python', os.path.join(script_dir, 'option2_detailed_metrics.py'),
        '--vanilla-csv', args.vanilla_csv,
        '--optimized-csv', args.optimized_csv,
        '--output', os.path.join(args.output_dir, 'option2_detailed_metrics.pdf')
    ]
    if run_command(cmd2, "Detailed Metrics Analysis (Option 2)"):
        success_count += 1
    
    # 3. Generate comprehensive dashboard
    total_plots += 1
    cmd3 = [
        'python', os.path.join(script_dir, 'cache_and_performance_metrics.py'),
        '--vanilla-csv', args.vanilla_csv,
        '--optimized-csv', args.optimized_csv,
        '--plot-type', 'dashboard',
        '--output-dir', args.output_dir
    ]
    if run_command(cmd3, "Comprehensive Metrics Dashboard"):
        success_count += 1
    
    # 4. Generate separate cache metrics plot
    total_plots += 1
    cmd4 = [
        'python', os.path.join(script_dir, 'cache_and_performance_metrics.py'),
        '--vanilla-csv', args.vanilla_csv,
        '--optimized-csv', args.optimized_csv,
        '--plot-type', 'cache',
        '--output-dir', args.output_dir
    ]
    if run_command(cmd4, "Cache Metrics Comparison"):
        success_count += 1
    
    # 5. Generate separate performance metrics plot
    total_plots += 1
    cmd5 = [
        'python', os.path.join(script_dir, 'cache_and_performance_metrics.py'),
        '--vanilla-csv', args.vanilla_csv,
        '--optimized-csv', args.optimized_csv,
        '--plot-type', 'performance',
        '--output-dir', args.output_dir
    ]
    if run_command(cmd5, "Performance Metrics Comparison"):
        success_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Successfully generated: {success_count}/{total_plots} plots")
    
    if success_count == total_plots:
        print("🎉 All plots generated successfully!")
        print(f"\nGenerated files in {args.output_dir}:")
        for filename in [
            'option1_throughput_comparison.pdf',
            'option2_detailed_metrics.pdf', 
            'metrics_dashboard.pdf',
            'cache_metrics_comparison.pdf',
            'performance_metrics_comparison.pdf'
        ]:
            filepath = os.path.join(args.output_dir, filename)
            if os.path.exists(filepath):
                print(f"  ✓ {filename}")
            else:
                print(f"  ✗ {filename} (missing)")
    else:
        print(f"⚠️  {total_plots - success_count} plots failed to generate")
        sys.exit(1)

if __name__ == "__main__":
    main()