#!/usr/bin/env python3
"""
Option 2: Speedup Ratio Plot
Shows how many times faster optimized is compared to vanilla
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

def create_speedup_ratio_plot(vanilla_df, optimized_df, output_path):
    """Create speedup ratio plot showing performance improvements"""
    
    # Calculate throughput
    vanilla_df = calculate_throughput(vanilla_df)
    optimized_df = calculate_throughput(optimized_df)
    
    # Calculate mean throughput for each configuration
    vanilla_means = vanilla_df.groupby(['storage_type', 'cache_type', 'thread_count'])['throughput'].mean().reset_index()
    optimized_means = optimized_df.groupby(['storage_type', 'cache_type', 'thread_count'])['throughput'].mean().reset_index()
    
    # Merge to calculate speedup ratios
    merged = pd.merge(vanilla_means, optimized_means, 
                     on=['storage_type', 'cache_type', 'thread_count'],
                     suffixes=('_vanilla', '_optimized'))
    
    # Calculate speedup ratio
    merged['speedup_ratio'] = merged['throughput_optimized'] / merged['throughput_vanilla']
    
    # Create configuration labels
    merged['config_label'] = (merged['storage_type'] + '_' + 
                             merged['cache_type'] + '_' + 
                             merged['thread_count'].astype(str) + 'T')
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 12))
    fig.suptitle('Performance Speedup: Optimized vs Vanilla\n(Higher values = better optimization)', 
                 fontsize=16, fontweight='bold')
    
    # Color mapping
    storage_colors = {'VolatileStorage': '#FF6B6B', 'PMemStorage': '#4ECDC4', 'FileStorage': '#45B7D1'}
    thread_colors = {1: 0.7, 4: 1.0}  # Alpha values for thread counts
    
    # Plot 1: All configurations
    x_pos = np.arange(len(merged))
    colors = [storage_colors[storage] for storage in merged['storage_type']]
    alphas = [thread_colors[thread] for thread in merged['thread_count']]
    
    bars = ax1.bar(x_pos, merged['speedup_ratio'], 
                   color=colors, alpha=0.8)
    
    # Color bars by alpha based on thread count
    for bar, alpha in zip(bars, alphas):
        bar.set_alpha(alpha)
    
    # Add horizontal line at y=1 (no improvement)
    ax1.axhline(y=1, color='red', linestyle='--', alpha=0.7, linewidth=2, label='No improvement')
    
    # Add value labels on bars
    for i, (bar, ratio) in enumerate(zip(bars, merged['speedup_ratio'])):
        height = bar.get_height()
        color = 'darkgreen' if ratio >= 2 else 'darkorange' if ratio >= 1.5 else 'darkred'
        ax1.annotate(f'{ratio:.1f}x',
                    xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3),
                    textcoords='offset points',
                    ha='center', va='bottom',
                    fontsize=9, fontweight='bold',
                    color=color)
    
    ax1.set_xlabel('Configuration (Storage_Cache_Threads)', fontsize=12)
    ax1.set_ylabel('Speedup Ratio (Optimized/Vanilla)', fontsize=12)
    ax1.set_title('Speedup Across All Configurations', fontsize=14)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(merged['config_label'], rotation=45, ha='right')
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.legend()
    
    # Plot 2: Grouped by storage type
    storage_types = sorted(merged['storage_type'].unique())
    cache_types = sorted(merged['cache_type'].unique())
    thread_counts = sorted(merged['thread_count'].unique())
    
    x_positions = []
    speedup_values = []
    bar_colors = []
    bar_labels = []
    tick_positions = []
    tick_labels = []
    
    current_x = 0
    for storage_type in storage_types:
        storage_data = merged[merged['storage_type'] == storage_type]
        
        # Add storage type label position
        storage_start = current_x
        
        for cache_type in cache_types:
            cache_data = storage_data[storage_data['cache_type'] == cache_type]
            
            for thread_count in thread_counts:
                thread_data = cache_data[cache_data['thread_count'] == thread_count]
                if len(thread_data) > 0:
                    x_positions.append(current_x)
                    speedup_values.append(thread_data['speedup_ratio'].iloc[0])
                    bar_colors.append(storage_colors[storage_type])
                    bar_labels.append(f'{cache_type}_{thread_count}T')
                    current_x += 1
            
            # Add small gap between cache types
            current_x += 0.3
        
        # Add storage type tick
        storage_end = current_x - 0.3
        tick_positions.append((storage_start + storage_end) / 2)
        tick_labels.append(storage_type)
        
        # Add larger gap between storage types
        current_x += 0.7
    
    # Create grouped bar plot
    bars2 = ax2.bar(x_positions, speedup_values, color=bar_colors, alpha=0.8)
    
    # Add horizontal line at y=1
    ax2.axhline(y=1, color='red', linestyle='--', alpha=0.7, linewidth=2, label='No improvement')
    
    # Add value labels
    for bar, ratio in zip(bars2, speedup_values):
        height = bar.get_height()
        color = 'darkgreen' if ratio >= 2 else 'darkorange' if ratio >= 1.5 else 'darkred'
        ax2.annotate(f'{ratio:.1f}x',
                    xy=(bar.get_x() + bar.get_width()/2, height),
                    xytext=(0, 3),
                    textcoords='offset points',
                    ha='center', va='bottom',
                    fontsize=9, fontweight='bold',
                    color=color)
    
    ax2.set_xlabel('Storage Type', fontsize=12)
    ax2.set_ylabel('Speedup Ratio (Optimized/Vanilla)', fontsize=12)
    ax2.set_title('Speedup Grouped by Storage Type', fontsize=14)
    ax2.set_xticks(tick_positions)
    ax2.set_xticklabels(tick_labels)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.legend()
    
    # Add minor ticks for individual bars
    ax2.set_xticks(x_positions, minor=True)
    ax2.set_xticklabels(bar_labels, minor=True, rotation=45, ha='right', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Option 2 plot saved to: {output_path}")
    
    # Print summary statistics
    print("\nSpeedup Summary:")
    print(f"Average speedup: {merged['speedup_ratio'].mean():.2f}x")
    print(f"Median speedup: {merged['speedup_ratio'].median():.2f}x")
    print(f"Min speedup: {merged['speedup_ratio'].min():.2f}x")
    print(f"Max speedup: {merged['speedup_ratio'].max():.2f}x")
    
    # Identify problematic configurations
    low_speedup = merged[merged['speedup_ratio'] < 1.5]
    if len(low_speedup) > 0:
        print(f"\nConfigurations with low speedup (<1.5x):")
        for _, row in low_speedup.iterrows():
            print(f"  {row['config_label']}: {row['speedup_ratio']:.2f}x")
    
    return fig

def main():
    parser = argparse.ArgumentParser(description='Generate Option 2: Speedup ratio plot')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output', default='option2_speedup_ratio.pdf', help='Output file path')
    
    args = parser.parse_args()
    
    try:
        # Load data
        vanilla_df = load_vanilla_data(args.vanilla_csv)
        optimized_df = load_optimized_data(args.optimized_csv)
        
        # Create plot
        fig = create_speedup_ratio_plot(vanilla_df, optimized_df, args.output)
        
        print("Option 2 plot generation completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()