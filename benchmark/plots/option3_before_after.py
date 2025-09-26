#!/usr/bin/env python3
"""
Option 3: Before/After Comparison
Shows vanilla (before) and optimized (after) side by side with connecting arrows
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import argparse
from matplotlib.patches import FancyArrowPatch
from matplotlib.patches import ConnectionPatch

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

def plot_storage_data_before_after(ax_before, ax_after, vanilla_data, optimized_data, storage_type, 
                                  cache_types, thread_counts, max_throughput):
    """Plot data for a specific storage type in before/after format"""
    
    # Filter data for this storage type
    vanilla_storage = vanilla_data[vanilla_data['storage_type'] == storage_type]
    optimized_storage = optimized_data[optimized_data['storage_type'] == storage_type]
    
    # Calculate summary statistics
    vanilla_stats = vanilla_storage.groupby(['cache_type', 'thread_count'])['throughput'].agg(['mean', 'std']).reset_index()
    optimized_stats = optimized_storage.groupby(['cache_type', 'thread_count'])['throughput'].agg(['mean', 'std']).reset_index()
    
    # Colors for thread counts
    thread_colors = {1: '#4CAF50', 4: '#FF9800'}  # Green for 1 thread, Orange for 4 threads
    
    # Set up bar positions
    x_pos = np.arange(len(cache_types))
    bar_width = 0.35
    
    # Store bar positions for arrows
    vanilla_bar_tops = {}
    optimized_bar_tops = {}
    
    # Plot vanilla data (BEFORE)
    for i, thread_count in enumerate(thread_counts):
        thread_data = vanilla_stats[vanilla_stats['thread_count'] == thread_count]
        
        means = []
        stds = []
        positions = []
        
        for j, cache_type in enumerate(cache_types):
            cache_data = thread_data[thread_data['cache_type'] == cache_type]
            if len(cache_data) > 0:
                mean_val = cache_data['mean'].iloc[0]
                std_val = cache_data['std'].iloc[0]
                means.append(mean_val)
                stds.append(std_val)
                
                # Store position for arrows
                pos = x_pos[j] + (i - 0.5) * bar_width
                positions.append(pos)
                vanilla_bar_tops[(cache_type, thread_count)] = (pos, mean_val)
            else:
                means.append(0)
                stds.append(0)
                positions.append(x_pos[j] + (i - 0.5) * bar_width)
        
        bars = ax_before.bar(positions, means, bar_width,
                           yerr=stds, capsize=3,
                           color=thread_colors[thread_count], alpha=0.7,
                           label=f'{thread_count} thread{"s" if thread_count > 1 else ""}')
    
    # Plot optimized data (AFTER)
    for i, thread_count in enumerate(thread_counts):
        thread_data = optimized_stats[optimized_stats['thread_count'] == thread_count]
        
        means = []
        stds = []
        positions = []
        
        for j, cache_type in enumerate(cache_types):
            cache_data = thread_data[thread_data['cache_type'] == cache_type]
            if len(cache_data) > 0:
                mean_val = cache_data['mean'].iloc[0]
                std_val = cache_data['std'].iloc[0]
                means.append(mean_val)
                stds.append(std_val)
                
                # Store position for arrows
                pos = x_pos[j] + (i - 0.5) * bar_width
                positions.append(pos)
                optimized_bar_tops[(cache_type, thread_count)] = (pos, mean_val)
            else:
                means.append(0)
                stds.append(0)
                positions.append(x_pos[j] + (i - 0.5) * bar_width)
        
        bars = ax_after.bar(positions, means, bar_width,
                          yerr=stds, capsize=3,
                          color=thread_colors[thread_count], alpha=0.7,
                          label=f'{thread_count} thread{"s" if thread_count > 1 else ""}')
    
    # Customize axes
    for ax, title_suffix in [(ax_before, 'BEFORE (Vanilla)'), (ax_after, 'AFTER (Optimized)')]:
        ax.set_title(f'{storage_type} - {title_suffix}', fontsize=12, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(cache_types)
        ax.set_ylim(0, max_throughput * 1.1)
        ax.grid(True, alpha=0.3, axis='y')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
    
    ax_before.set_ylabel('Throughput (ops/sec)', fontsize=10)
    ax_before.legend(fontsize=9)
    
    return vanilla_bar_tops, optimized_bar_tops

def create_before_after_plot(vanilla_df, optimized_df, output_path):
    """Create before/after comparison plot"""
    
    # Calculate throughput
    vanilla_df = calculate_throughput(vanilla_df)
    optimized_df = calculate_throughput(optimized_df)
    
    # Get unique values
    storage_types = sorted(vanilla_df['storage_type'].unique())
    cache_types = sorted(vanilla_df['cache_type'].unique())
    thread_counts = sorted(vanilla_df['thread_count'].unique())
    
    # Calculate global max for consistent scaling
    max_vanilla = vanilla_df['throughput'].max()
    max_optimized = optimized_df['throughput'].max()
    max_throughput = max(max_vanilla, max_optimized)
    
    # Create figure with 2 columns (before/after) and 3 rows (storage types)
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    fig.suptitle('Performance Comparison: Before (Vanilla) vs After (Optimized)\n' + 
                 'Arrows show improvement direction', fontsize=16, fontweight='bold')
    
    # Store all bar positions for drawing arrows
    all_vanilla_positions = {}
    all_optimized_positions = {}
    
    for i, storage_type in enumerate(storage_types):
        ax_before = axes[i, 0]
        ax_after = axes[i, 1]
        
        vanilla_positions, optimized_positions = plot_storage_data_before_after(
            ax_before, ax_after, vanilla_df, optimized_df, storage_type,
            cache_types, thread_counts, max_throughput
        )
        
        all_vanilla_positions[storage_type] = vanilla_positions
        all_optimized_positions[storage_type] = optimized_positions
    
    # Add connecting arrows between before and after
    for i, storage_type in enumerate(storage_types):
        ax_before = axes[i, 0]
        ax_after = axes[i, 1]
        
        vanilla_positions = all_vanilla_positions[storage_type]
        optimized_positions = all_optimized_positions[storage_type]
        
        # Draw arrows for each configuration
        for (cache_type, thread_count) in vanilla_positions:
            if (cache_type, thread_count) in optimized_positions:
                # Get positions
                vanilla_pos, vanilla_height = vanilla_positions[(cache_type, thread_count)]
                optimized_pos, optimized_height = optimized_positions[(cache_type, thread_count)]
                
                # Calculate speedup
                speedup = optimized_height / vanilla_height if vanilla_height > 0 else 0
                
                # Choose arrow color based on improvement
                if speedup >= 3:
                    arrow_color = 'darkgreen'
                elif speedup >= 2:
                    arrow_color = 'green'
                elif speedup >= 1.5:
                    arrow_color = 'orange'
                else:
                    arrow_color = 'red'
                
                # Create connection patch (arrow)
                arrow = ConnectionPatch(
                    (vanilla_pos, vanilla_height), (optimized_pos, optimized_height),
                    "data", "data",
                    axesA=ax_before, axesB=ax_after,
                    arrowstyle="->", shrinkB=5, shrinkA=5,
                    mutation_scale=20, fc=arrow_color, ec=arrow_color,
                    alpha=0.6, linewidth=2
                )
                fig.add_artist(arrow)
                
                # Add speedup label on arrow
                mid_x = 0.5  # Middle between the two subplots
                mid_y = (vanilla_height + optimized_height) / 2 / max_throughput
                
                # Convert to figure coordinates
                fig_coords = fig.transFigure.inverted().transform(
                    ax_before.transData.transform((vanilla_pos, vanilla_height))
                )
                
                if speedup > 0:
                    fig.text(0.5, fig_coords[1], f'{speedup:.1f}x',
                           ha='center', va='center',
                           fontsize=8, fontweight='bold',
                           color=arrow_color,
                           bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8))
    
    # Add column labels
    fig.text(0.25, 0.95, 'BEFORE (Vanilla)', ha='center', va='top', 
             fontsize=14, fontweight='bold', color='darkblue')
    fig.text(0.75, 0.95, 'AFTER (Optimized)', ha='center', va='top', 
             fontsize=14, fontweight='bold', color='darkgreen')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Option 3 plot saved to: {output_path}")
    
    # Print improvement summary
    print("\nImprovement Summary:")
    for storage_type in storage_types:
        print(f"\n{storage_type}:")
        vanilla_storage = vanilla_df[vanilla_df['storage_type'] == storage_type]
        optimized_storage = optimized_df[optimized_df['storage_type'] == storage_type]
        
        vanilla_mean = vanilla_storage.groupby(['cache_type', 'thread_count'])['throughput'].mean()
        optimized_mean = optimized_storage.groupby(['cache_type', 'thread_count'])['throughput'].mean()
        
        for (cache_type, thread_count), vanilla_val in vanilla_mean.items():
            if (cache_type, thread_count) in optimized_mean.index:
                optimized_val = optimized_mean[(cache_type, thread_count)]
                speedup = optimized_val / vanilla_val
                print(f"  {cache_type} ({thread_count}T): {vanilla_val/1e6:.1f}M → {optimized_val/1e6:.1f}M ops/sec ({speedup:.1f}x)")
    
    return fig

def main():
    parser = argparse.ArgumentParser(description='Generate Option 3: Before/After comparison plot')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output', default='option3_before_after.pdf', help='Output file path')
    
    args = parser.parse_args()
    
    try:
        # Load data
        vanilla_df = load_vanilla_data(args.vanilla_csv)
        optimized_df = load_optimized_data(args.optimized_csv)
        
        # Create plot
        fig = create_before_after_plot(vanilla_df, optimized_df, args.output)
        
        print("Option 3 plot generation completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()