#!/usr/bin/env python3
"""
Option 1 Extended: Performance Comparison by Operation Type
Shows vanilla vs optimized with separate subplots for each operation across storage types
Layout: 4 rows (operations) × 3 columns (storage types) = 12 subplots
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import argparse

def load_vanilla_data(csv_path):
    """Load the vanilla benchmark data"""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} records from vanilla CSV")
    
    # Replace SSARC with A2Q in vanilla data for consistency
    df['cache_type'] = df['cache_type'].replace('SSARC', 'A2Q')
    
    return df

def load_optimized_data(csv_path):
    """Load the optimized benchmark data and normalize column names"""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} records from optimized CSV")
    
    # Normalize column names to match vanilla format
    df = df.rename(columns={
        'policy_name': 'cache_type',
        'time_us': 'time_ns'  # Will convert units later
    })
    
    # Convert time from microseconds to nanoseconds
    df['time_ns'] = df['time_ns'] * 1000
    
    # Map config_name to thread_count
    df['thread_count'] = df['config_name'].map({
        'non_concurrent_default': 1,
        'concurrent_default': 4
    })
    
    # Filter out any unmapped configs
    df = df.dropna(subset=['thread_count'])
    df['thread_count'] = df['thread_count'].astype(int)
    
    return df

def calculate_throughput(df):
    """Calculate throughput in operations per second"""
    df = df.copy()
    # Throughput = record_count / (time_ns / 1e9) = record_count * 1e9 / time_ns
    df['throughput'] = df['record_count'] * 1e9 / df['time_ns']
    return df

def create_extended_operation_plot(vanilla_df, optimized_df, output_path):
    """Create extended plot with separate subplots for each operation type"""
    
    # Calculate throughput
    vanilla_df = calculate_throughput(vanilla_df)
    optimized_df = calculate_throughput(optimized_df)
    
    # Add variant labels
    vanilla_df['variant'] = 'Vanilla'
    optimized_df['variant'] = 'Optimized'
    
    # Combine data
    combined_df = pd.concat([vanilla_df, optimized_df], ignore_index=True)
    
    # Get unique values
    storage_types = sorted(combined_df['storage_type'].unique())
    cache_types = sorted(combined_df['cache_type'].unique())
    thread_counts = sorted(combined_df['thread_count'].unique())
    operation_types = sorted(combined_df['operation'].unique())
    
    print(f"Storage types: {storage_types}")
    print(f"Cache types: {cache_types}")
    print(f"Thread counts: {thread_counts}")
    print(f"Operation types: {operation_types}")
    
    # Create figure with 6 rows (operations) × 3 columns (storage types)
    fig, axes = plt.subplots(6, 3, figsize=(24, 30))
    fig.suptitle('Performance Comparison by Operation Type: Vanilla vs Optimized\n(Higher bars = better performance)', 
                 fontsize=18, fontweight='bold', y=0.98)
    
    # Colors for variants and threads
    colors = {
        ('Vanilla', 1): '#87CEEB',    # Light blue
        ('Vanilla', 4): '#4682B4',    # Steel blue
        ('Optimized', 1): '#FFB347',  # Light orange
        ('Optimized', 4): '#FF6347'   # Tomato red
    }
    
    # Create plots for each operation type (rows) and storage type (columns)
    for op_idx, operation_type in enumerate(operation_types):
        for storage_idx, storage_type in enumerate(storage_types):
            ax = axes[op_idx, storage_idx]
            
            # Filter data for this operation and storage type
            op_storage_data = combined_df[
                (combined_df['operation'] == operation_type) & 
                (combined_df['storage_type'] == storage_type)
            ]
            
            if len(op_storage_data) == 0:
                ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes, fontsize=12)
                ax.set_title(f'{operation_type} - {storage_type}', fontsize=12, fontweight='bold')
                continue
            
            # Prepare data for plotting
            x_pos = np.arange(len(cache_types))
            bar_width = 0.2
            
            # Plot bars for each variant and thread count combination
            for i, (variant, thread_count) in enumerate([('Vanilla', 1), ('Vanilla', 4), ('Optimized', 1), ('Optimized', 4)]):
                variant_data = op_storage_data[
                    (op_storage_data['variant'] == variant) & 
                    (op_storage_data['thread_count'] == thread_count)
                ]
                
                means = []
                stds = []
                
                for cache_type in cache_types:
                    cache_data = variant_data[variant_data['cache_type'] == cache_type]['throughput']
                    if len(cache_data) > 0:
                        means.append(cache_data.mean())
                        stds.append(cache_data.std() if len(cache_data) > 1 else 0)
                    else:
                        means.append(0)
                        stds.append(0)
                
                # Plot bars
                positions = x_pos + (i - 1.5) * bar_width
                bars = ax.bar(positions, means, bar_width, 
                             color=colors[(variant, thread_count)], 
                             alpha=0.8, 
                             yerr=stds, 
                             capsize=3,
                             label=f'{variant} ({thread_count}T)')
                
                # Add value labels on bars (only for non-zero values)
                for j, (pos, mean, std) in enumerate(zip(positions, means, stds)):
                    if mean > 0:
                        label_y = mean + std + ax.get_ylim()[1] * 0.01
                        ax.text(pos, label_y, f'{mean/1e6:.1f}M', 
                               ha='center', va='bottom', fontsize=8, rotation=0)
            
            # Calculate and display speedup annotations
            for j, cache_type in enumerate(cache_types):
                # Get vanilla and optimized data for this cache type
                vanilla_1t = op_storage_data[
                    (op_storage_data['variant'] == 'Vanilla') & 
                    (op_storage_data['thread_count'] == 1) & 
                    (op_storage_data['cache_type'] == cache_type)
                ]['throughput']
                
                vanilla_4t = op_storage_data[
                    (op_storage_data['variant'] == 'Vanilla') & 
                    (op_storage_data['thread_count'] == 4) & 
                    (op_storage_data['cache_type'] == cache_type)
                ]['throughput']
                
                optimized_1t = op_storage_data[
                    (op_storage_data['variant'] == 'Optimized') & 
                    (op_storage_data['thread_count'] == 1) & 
                    (op_storage_data['cache_type'] == cache_type)
                ]['throughput']
                
                optimized_4t = op_storage_data[
                    (op_storage_data['variant'] == 'Optimized') & 
                    (op_storage_data['thread_count'] == 4) & 
                    (op_storage_data['cache_type'] == cache_type)
                ]['throughput']
                
                # Calculate speedups if data exists
                speedups = []
                if len(vanilla_1t) > 0 and len(optimized_1t) > 0 and vanilla_1t.mean() > 0:
                    speedup_1t = optimized_1t.mean() / vanilla_1t.mean()
                    speedups.append(f"1T: {speedup_1t:.1f}x")
                
                if len(vanilla_4t) > 0 and len(optimized_4t) > 0 and vanilla_4t.mean() > 0:
                    speedup_4t = optimized_4t.mean() / vanilla_4t.mean()
                    speedups.append(f"4T: {speedup_4t:.1f}x")
                
                # Display speedup annotation
                if speedups:
                    speedup_text = "\n".join(speedups)
                    ax.text(j, ax.get_ylim()[1] * 0.85, speedup_text, 
                           ha='center', va='top', fontsize=8, 
                           bbox=dict(boxstyle="round,pad=0.3", facecolor='yellow', alpha=0.7))
            
            # Customize subplot
            title = f'{operation_type} - {storage_type}'
            ax.set_title(title, fontsize=12, fontweight='bold')
            ax.set_xlabel('Cache Policy', fontsize=10)
            
            # Only add y-label to leftmost subplots
            if storage_idx == 0:
                ax.set_ylabel('Throughput (ops/sec)', fontsize=10)
            
            ax.set_xticks(x_pos)
            ax.set_xticklabels(cache_types, fontsize=9)
            ax.grid(True, alpha=0.3, axis='y')
            
            # Format y-axis to show values in millions
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
            
            # Add legend only to the top-right subplot
            if op_idx == 0 and storage_idx == 2:
                ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    
    # Adjust layout to prevent overlap
    plt.tight_layout()
    plt.subplots_adjust(top=0.94, right=0.95)
    
    # Save plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Extended operation plot saved to: {output_path}")
    
    return fig

def main():
    parser = argparse.ArgumentParser(description='Generate Option 1 Extended: Performance comparison by operation type')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output', default='option1_extended_by_operation.pdf', help='Output file path')
    
    args = parser.parse_args()
    
    try:
        # Load data
        vanilla_df = load_vanilla_data(args.vanilla_csv)
        optimized_df = load_optimized_data(args.optimized_csv)
        
        # Create plot
        fig = create_extended_operation_plot(vanilla_df, optimized_df, args.output)
        
        print("Extended operation plot generation completed successfully!")
        
        # Print summary statistics
        print("\n" + "="*60)
        print("SUMMARY STATISTICS BY OPERATION TYPE")
        print("="*60)
        
        # Calculate throughput for summary
        vanilla_df = calculate_throughput(vanilla_df)
        optimized_df = calculate_throughput(optimized_df)
        
        operation_types = sorted(vanilla_df['operation'].unique())
        
        for operation_type in operation_types:
            print(f"\n{operation_type.upper()} OPERATION:")
            print("-" * 40)
            
            vanilla_op = vanilla_df[vanilla_df['operation'] == operation_type]
            optimized_op = optimized_df[optimized_df['operation'] == operation_type]
            
            if len(vanilla_op) > 0 and len(optimized_op) > 0:
                vanilla_mean = vanilla_op['throughput'].mean()
                optimized_mean = optimized_op['throughput'].mean()
                speedup = optimized_mean / vanilla_mean if vanilla_mean > 0 else 0
                
                print(f"  Vanilla avg:   {vanilla_mean/1e6:.2f}M ops/sec")
                print(f"  Optimized avg: {optimized_mean/1e6:.2f}M ops/sec")
                print(f"  Speedup:       {speedup:.2f}x")
            else:
                print("  Insufficient data for comparison")
        
    except Exception as e:
        print(f"Error generating plot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()