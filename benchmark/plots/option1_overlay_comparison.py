#!/usr/bin/env python3
"""
Option 1: Performance Improvement Focus with Overlay Design
Shows vanilla vs optimized with grouped bars and speedup annotations
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

def create_overlay_comparison_plot(vanilla_df, optimized_df, output_path):
    """Create overlay comparison plot with grouped bars"""
    
    # Calculate throughput
    vanilla_df = calculate_throughput(vanilla_df)
    optimized_df = calculate_throughput(optimized_df)
    
    # Add variant labels
    vanilla_df['variant'] = 'Version 1'
    optimized_df['variant'] = 'Version 2'
    
    # Combine data
    combined_df = pd.concat([vanilla_df, optimized_df], ignore_index=True)
    
    # Get unique storage types and rename them
    storage_type_mapping = {
        'FileStorage': 'SSD NVMe',
        'PMemStorage': 'NVM',
        'VolatileStorage': 'NVDIMM'
    }
    combined_df['storage_type'] = combined_df['storage_type'].map(storage_type_mapping)
    
    # Define custom order: NVDIMM, NVM, SSD NVMe
    storage_types = ['NVDIMM', 'NVM', 'SSD NVMe']
    cache_types = sorted(combined_df['cache_type'].unique())
    thread_counts = sorted(combined_df['thread_count'].unique())
    
    # Create figure with subplots for each storage type
    fig, axes = plt.subplots(1, 3, figsize=(20, 8))
    
    # Patterns for variants and threads (using black color only)
    patterns = {
        ('Version 1', 1): '///',        # Diagonal lines
        ('Version 1', 4): '\\\\\\',     # Reverse diagonal lines
        ('Version 2', 1): '...',      # Dots
        ('Version 2', 4): 'xxx'       # Crosses
    }
    
    for i, storage_type in enumerate(storage_types):
        ax = axes[i]
        storage_data = combined_df[combined_df['storage_type'] == storage_type]
        
        # Calculate mean throughput and min/max for each combination
        summary_stats = storage_data.groupby(['cache_type', 'thread_count', 'variant'])['throughput'].agg(['mean', 'min', 'max']).reset_index()
        
        # Set up bar positions
        x_pos = np.arange(len(cache_types))
        bar_width = 0.2
        
        # Plot bars for each combination
        for j, thread_count in enumerate(thread_counts):
            for k, variant in enumerate(['Version 1', 'Version 2']):
                data_subset = summary_stats[
                    (summary_stats['thread_count'] == thread_count) & 
                    (summary_stats['variant'] == variant)
                ]
                
                if len(data_subset) == 0:
                    continue
                
                # Calculate bar positions
                offset = (j * 2 + k - 1.5) * bar_width
                positions = x_pos + offset
                
                means = []
                error_lower = []
                error_upper = []
                for cache_type in cache_types:
                    cache_data = data_subset[data_subset['cache_type'] == cache_type]
                    if len(cache_data) > 0:
                        mean_val = cache_data['mean'].iloc[0]
                        min_val = cache_data['min'].iloc[0]
                        max_val = cache_data['max'].iloc[0]
                        means.append(mean_val)
                        # Error bars: distance from mean to min/max
                        error_lower.append(mean_val - min_val)
                        error_upper.append(max_val - mean_val)
                    else:
                        means.append(0)
                        error_lower.append(0)
                        error_upper.append(0)
                
                # Plot bars without error bars using patterns
                bars = ax.bar(positions, means, bar_width, 
                             color='white',
                             edgecolor='black',
                             hatch=patterns[(variant, thread_count)],
                             alpha=1.0,
                             label=f'{variant} ({thread_count} thread{"s" if thread_count > 1 else ""})')
                
                # Add speedup annotations for optimized bars
                if variant == 'Version 2':
                    for idx, (pos, mean_opt) in enumerate(zip(positions, means)):
                        if mean_opt > 0:
                            # Find corresponding vanilla value
                            vanilla_data = summary_stats[
                                (summary_stats['thread_count'] == thread_count) & 
                                (summary_stats['variant'] == 'Version 1') &
                                (summary_stats['cache_type'] == cache_types[idx])
                            ]
                            if len(vanilla_data) > 0:
                                mean_vanilla = vanilla_data['mean'].iloc[0]
                                if mean_vanilla > 0:
                                    speedup = mean_opt / mean_vanilla
                                    ax.annotate(f'{speedup:.1f}x', 
                                              xy=(pos, mean_opt), 
                                              xytext=(0, 2), 
                                              textcoords='offset points',
                                              ha='center', va='bottom',
                                              fontsize=18, fontweight='bold',
                                              color='darkred' if speedup < 2 else 'darkgreen')
        
        # Customize subplot
        ax.set_title(f'{storage_type}', fontsize=28, fontweight='bold')
        if i == 0:
            ax.set_ylabel('Throughput', fontsize=24)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(cache_types, fontsize=20)
        ax.grid(True, alpha=0.3, axis='y')
                
        # Format y-axis to show values in millions
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
        ax.tick_params(axis='y', labelsize=18)
    
    # Set consistent y-axis limits across all subplots (0 to 4M)
    for ax in axes:
        ax.set_ylim(0, 5e6)
        
    # Add legend at the bottom of the entire figure (single row)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='lower center', bbox_to_anchor=(0.5, -0.05), 
               ncol=4, fontsize=20, frameon=False)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Option 1 plot saved to: {output_path}")
    
    return fig

def main():
    parser = argparse.ArgumentParser(description='Generate Option 1: Overlay comparison plot')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output', default='option1_overlay_comparison.pdf', help='Output file path')
    
    args = parser.parse_args()
    
    try:
        # Load data
        vanilla_df = load_vanilla_data(args.vanilla_csv)
        optimized_df = load_optimized_data(args.optimized_csv)
        
        # Create plot
        fig = create_overlay_comparison_plot(vanilla_df, optimized_df, args.output)
        
        print("Option 1 plot generation completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()