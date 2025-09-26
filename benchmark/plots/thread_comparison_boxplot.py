#!/usr/bin/env python3
"""
Generate box plots comparing cache policies for different thread counts
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import argparse

def load_data(csv_path):
    """Load the benchmark data"""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} records from CSV")
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
    
    print(f"Optimized data thread count distribution:")
    print(df['thread_count'].value_counts().sort_index())
    print(f"Optimized data cache type distribution:")
    print(df['cache_type'].value_counts())
    
    return df

def calculate_throughput(df):
    """Calculate throughput from record_count and time_ns"""
    # Throughput = record_count / (time_ns / 1e9) = record_count * 1e9 / time_ns
    df['calculated_throughput'] = df['record_count'] * 1e9 / df['time_ns']
    return df

def create_thread_comparison_boxplot(vanilla_csv_path, optimized_csv_path):
    """Create box plots comparing cache policies for different storage types"""
    
    # Load and prepare vanilla data
    df_vanilla = load_data(vanilla_csv_path)
    df_vanilla = calculate_throughput(df_vanilla)
    
    # Load and prepare optimized data
    df_optimized = load_optimized_data(optimized_csv_path)
    df_optimized = calculate_throughput(df_optimized)
    
    # Filter for thread counts 1 and 4 for both datasets
    df_vanilla_filtered = df_vanilla[df_vanilla['thread_count'].isin([1, 4])].copy()
    df_optimized_filtered = df_optimized[df_optimized['thread_count'].isin([1, 4])].copy()
    
    # Replace SSARC with A2Q in vanilla data (do this early)
    df_vanilla_filtered['cache_type'] = df_vanilla_filtered['cache_type'].replace('SSARC', 'A2Q')
    
    print(f"Vanilla data after filtering for thread counts 1 and 4: {len(df_vanilla_filtered)} records")
    print(f"Optimized data after filtering for thread counts 1 and 4: {len(df_optimized_filtered)} records")
    
    print(f"Vanilla thread count distribution:")
    print(df_vanilla_filtered['thread_count'].value_counts().sort_index())
    print(f"Vanilla cache type distribution:")
    print(df_vanilla_filtered['cache_type'].value_counts())
    print(f"Vanilla storage type distribution:")
    print(df_vanilla_filtered['storage_type'].value_counts())
    
    print(f"Optimized storage type distribution:")
    print(df_optimized_filtered['storage_type'].value_counts())
    
    # Get unique cache types and storage types
    cache_types = sorted(df_vanilla_filtered['cache_type'].unique())
    storage_types = ['VolatileStorage', 'PMemStorage', 'FileStorage']  # Order them logically
    
    print(f"Cache types: {cache_types}")
    print(f"Storage types: {storage_types}")
    
    # Create figure with 6 subplots (2 rows, 3 columns)
    fig, axes = plt.subplots(2, 3, figsize=(24, 12))
    
    # Calculate y-axis limits to use same scale across all subplots
    all_vanilla_throughput = df_vanilla_filtered['calculated_throughput'].values
    all_optimized_throughput = df_optimized_filtered['calculated_throughput'].values
    all_throughput = np.concatenate([all_vanilla_throughput, all_optimized_throughput])
    y_min = 0
    y_max = np.max(all_throughput) * 1.1
    
    print(f"Y-axis range: {y_min:.0f} to {y_max:.0f} ops/sec")
    
    # Colors for each cache type
    colors = {'CLOCK': '#2E86AB', 'LRU': '#A23B72', 'A2Q': '#F18F01'}
    
    def plot_storage_data(ax, data, storage_type, title, is_vanilla=True):
        """Plot data for a specific storage type showing thread count comparison"""
        
        # Filter data for this storage type
        storage_data = data[data['storage_type'] == storage_type]
        
        if len(storage_data) == 0:
            ax.text(0.5, 0.5, f'No data for {storage_type}', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title(title, fontsize=14, fontweight='bold')
            return
        
        # Separate by thread count
        thread_1_data = storage_data[storage_data['thread_count'] == 1]
        thread_4_data = storage_data[storage_data['thread_count'] == 4]
        
        # Prepare data for box plots
        plot_data = []
        plot_labels = []
        plot_colors = []
        positions = []
        pos_counter = 1
        
        for cache_type in cache_types:
            # Thread 1 data
            cache_thread_1 = thread_1_data[thread_1_data['cache_type'] == cache_type]['calculated_throughput']
            if len(cache_thread_1) > 0:
                plot_data.append(cache_thread_1.values)
                plot_labels.append(f"{cache_type}\n(1 thread)")
                plot_colors.append(colors.get(cache_type, '#666666'))
                positions.append(pos_counter)
                pos_counter += 1
            
            # Thread 4 data
            cache_thread_4 = thread_4_data[thread_4_data['cache_type'] == cache_type]['calculated_throughput']
            if len(cache_thread_4) > 0:
                plot_data.append(cache_thread_4.values)
                plot_labels.append(f"{cache_type}\n(4 threads)")
                plot_colors.append(colors.get(cache_type, '#666666'))
                positions.append(pos_counter)
                pos_counter += 1
            
            # Add spacing between cache types
            pos_counter += 0.5
        
        if plot_data:
            bp = ax.boxplot(plot_data, positions=positions, patch_artist=True, 
                           showmeans=True, meanline=True, widths=0.6)
            
            # Color the boxes
            for patch, color in zip(bp['boxes'], plot_colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.7)
            
            # Style the plot
            for element in ['whiskers', 'fliers', 'medians', 'caps']:
                plt.setp(bp[element], color='black')
            plt.setp(bp['means'], color='red', linewidth=2)
            
            # Set custom x-tick labels
            ax.set_xticks(positions)
            ax.set_xticklabels(plot_labels, rotation=45, ha='right', fontsize=9)
            
            # Add dividing lines between cache types
            for i in range(len(cache_types) - 1):
                divider_x = positions[i*2 + 1] + 0.75
                ax.axvline(x=divider_x, color='gray', linestyle=':', alpha=0.5, linewidth=1)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_ylabel('Throughput (ops/sec)', fontsize=12)
        ax.set_ylim(y_min, y_max)
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='y', labelsize=10)
    
    # Plot vanilla data (first row)
    for col, storage_type in enumerate(storage_types):
        title = f"Vanilla - {storage_type}"
        plot_storage_data(axes[0, col], df_vanilla_filtered, storage_type, title, is_vanilla=True)
    
    # Plot optimized data (second row)
    for col, storage_type in enumerate(storage_types):
        title = f"Optimized - {storage_type}"
        plot_storage_data(axes[1, col], df_optimized_filtered, storage_type, title, is_vanilla=False)
    
    # Add legend to the top right subplot
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=colors[cache], alpha=0.7, label=cache) 
                      for cache in cache_types if cache in colors]
    axes[0, 2].legend(handles=legend_elements, loc='upper right', fontsize=11)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot as PDF
    output_path = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/plots/thread_comparison_boxplot.pdf"
    plt.savefig(output_path, bbox_inches='tight', facecolor='white')
    print(f"Plot saved to: {output_path}")
    
    # Print summary statistics organized by storage type
    print("\n=== SUMMARY STATISTICS BY STORAGE TYPE ===")
    
    for storage_type in storage_types:
        print(f"\n{'='*60}")
        print(f"STORAGE TYPE: {storage_type}")
        print(f"{'='*60}")
        
        for thread_count in [1, 4]:
            print(f"\n  Thread Count = {thread_count}:")
            
            # Vanilla data statistics
            vanilla_storage_thread_data = df_vanilla_filtered[
                (df_vanilla_filtered['storage_type'] == storage_type) & 
                (df_vanilla_filtered['thread_count'] == thread_count)
            ]
            print(f"    VANILLA:")
            for cache_type in cache_types:
                cache_data = vanilla_storage_thread_data[vanilla_storage_thread_data['cache_type'] == cache_type]['calculated_throughput']
                if len(cache_data) > 0:
                    print(f"      {cache_type}:")
                    print(f"        Count: {len(cache_data)}")
                    print(f"        Mean:  {cache_data.mean():.0f} ops/sec")
                    print(f"        Median: {cache_data.median():.0f} ops/sec")
                    print(f"        Std:   {cache_data.std():.0f} ops/sec")
                    print(f"        Min:   {cache_data.min():.0f} ops/sec")
                    print(f"        Max:   {cache_data.max():.0f} ops/sec")
            
            # Optimized data statistics
            optimized_storage_thread_data = df_optimized_filtered[
                (df_optimized_filtered['storage_type'] == storage_type) & 
                (df_optimized_filtered['thread_count'] == thread_count)
            ]
            print(f"    OPTIMIZED:")
            for cache_type in cache_types:
                cache_data = optimized_storage_thread_data[optimized_storage_thread_data['cache_type'] == cache_type]['calculated_throughput']
                if len(cache_data) > 0:
                    print(f"      {cache_type}:")
                    print(f"        Count: {len(cache_data)}")
                    print(f"        Mean:  {cache_data.mean():.0f} ops/sec")
                    print(f"        Median: {cache_data.median():.0f} ops/sec")
                    print(f"        Std:   {cache_data.std():.0f} ops/sec")
                    print(f"        Min:   {cache_data.min():.0f} ops/sec")
                    print(f"        Max:   {cache_data.max():.0f} ops/sec")
    
    plt.close()

def main():
    """Main function to parse arguments and generate the plot"""
    parser = argparse.ArgumentParser(description='Generate box plots comparing vanilla and optimized cache policies for different thread counts')
    parser.add_argument('--vanilla-csv', 
                       help='Path to the vanilla CSV file containing benchmark results',
                       default='/home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250924_171318/combined_benchmark_results_with_perf_20250924_220907.csv')
    parser.add_argument('--optimized-csv',
                       help='Path to the optimized CSV file containing benchmark results',
                       default='/home/skarim/Code/haldendb_ex/haldendb_pvt/benchmark/build/cache_profiling_results_20250925_004057_default_configs_only/combined_benchmark_results_with_perf_20250925_151521.csv')
    
    args = parser.parse_args()
    
    try:
        create_thread_comparison_boxplot(args.vanilla_csv, args.optimized_csv)
        print("Thread comparison box plot with vanilla and optimized data generated successfully!")
    except Exception as e:
        print(f"Error generating plot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()