#!/usr/bin/env python3
"""
Option 1 Overlay with Stacked Error Bars (Option A)
Shows vanilla vs optimized with separate error bars for each operation type
Layout: 3 rows (storage types) × 1 column with wider bars
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

def create_stacked_error_overlay_plot(vanilla_df, optimized_df, output_path):
    """Create overlay comparison plot with stacked error bars per operation"""
    
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
    
    # Create figure with 3 rows (storage types) × 1 column
    fig, axes = plt.subplots(3, 1, figsize=(16, 18))
    fig.suptitle('Performance Comparison with Per-Operation Error Bars: Vanilla vs Optimized\n(Higher bars = better performance)', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Colors for variants and threads
    colors = {
        ('Vanilla', 1): '#87CEEB',    # Light blue
        ('Vanilla', 4): '#4682B4',    # Steel blue
        ('Optimized', 1): '#FFB347',  # Light orange
        ('Optimized', 4): '#FF6347'   # Tomato red
    }
    
    # Colors for operation error bars (different shades)
    operation_colors = {
        'delete': '#FF4444',
        'insert': '#44FF44', 
        'search_random': '#4444FF',
        'search_sequential': '#FF44FF',
        'search_uniform': '#44FFFF',
        'search_zipfian': '#FFFF44'
    }
    
    for i, storage_type in enumerate(storage_types):
        ax = axes[i]
        storage_data = combined_df[combined_df['storage_type'] == storage_type]
        
        # Set up bar positions with wider spacing
        x_pos = np.arange(len(cache_types))
        bar_width = 0.18  # Slightly wider bars
        
        # Plot bars for each combination
        for j, thread_count in enumerate(thread_counts):
            for k, variant in enumerate(['Vanilla', 'Optimized']):
                # Calculate overall mean for this combination
                variant_thread_data = storage_data[
                    (storage_data['thread_count'] == thread_count) & 
                    (storage_data['variant'] == variant)
                ]
                
                if len(variant_thread_data) == 0:
                    continue
                
                # Calculate bar positions
                offset = (j * 2 + k - 1.5) * bar_width
                positions = x_pos + offset
                
                # Calculate overall means and per-operation stats for each cache type
                overall_means = []
                stacked_errors = []
                
                for cache_type in cache_types:
                    cache_data = variant_thread_data[variant_thread_data['cache_type'] == cache_type]
                    
                    if len(cache_data) == 0:
                        overall_means.append(0)
                        stacked_errors.append([])
                        continue
                    
                    # Overall mean across all operations
                    overall_mean = cache_data['throughput'].mean()
                    overall_means.append(overall_mean)
                    
                    # Per-operation error bars
                    operation_errors = []
                    for operation_type in operation_types:
                        op_data = cache_data[cache_data['operation'] == operation_type]['throughput']
                        if len(op_data) > 0:
                            op_mean = op_data.mean()
                            op_std = op_data.std() if len(op_data) > 1 else 0
                            operation_errors.append({
                                'operation': operation_type,
                                'mean': op_mean,
                                'std': op_std,
                                'color': operation_colors[operation_type]
                            })
                    
                    stacked_errors.append(operation_errors)
                
                # Plot main bars
                bars = ax.bar(positions, overall_means, bar_width,
                             color=colors[(variant, thread_count)],
                             alpha=0.8,
                             label=f'{variant} ({thread_count} thread{"s" if thread_count > 1 else ""})')
                
                # Plot stacked error bars for each operation
                for pos_idx, (pos, mean, op_errors) in enumerate(zip(positions, overall_means, stacked_errors)):
                    if mean > 0 and op_errors:
                        # Calculate error bar positions
                        error_width = bar_width * 0.8  # Slightly narrower than bar
                        num_operations = len(op_errors)
                        error_segment_width = error_width / num_operations
                        
                        for op_idx, op_error in enumerate(op_errors):
                            # Position for this operation's error bar
                            error_pos = pos - error_width/2 + (op_idx + 0.5) * error_segment_width
                            
                            # Draw error bar for this operation
                            op_mean = op_error['mean']
                            op_std = op_error['std']
                            
                            if op_std > 0:
                                # Draw error bar line
                                ax.errorbar(error_pos, op_mean, yerr=op_std,
                                          fmt='none', 
                                          ecolor=op_error['color'],
                                          capsize=2,
                                          capthick=1.5,
                                          elinewidth=2,
                                          alpha=0.8)
                                
                                # Add small marker at operation mean
                                ax.plot(error_pos, op_mean, 'o', 
                                       color=op_error['color'], 
                                       markersize=3, 
                                       alpha=0.9)
                
                # Add speedup annotations for optimized bars
                if variant == 'Optimized':
                    for idx, (pos, mean_opt) in enumerate(zip(positions, overall_means)):
                        if mean_opt > 0:
                            # Find corresponding vanilla value
                            vanilla_data = storage_data[
                                (storage_data['thread_count'] == thread_count) & 
                                (storage_data['variant'] == 'Vanilla') &
                                (storage_data['cache_type'] == cache_types[idx])
                            ]
                            if len(vanilla_data) > 0:
                                mean_vanilla = vanilla_data['throughput'].mean()
                                if mean_vanilla > 0:
                                    speedup = mean_opt / mean_vanilla
                                    ax.annotate(f'{speedup:.1f}x', 
                                              xy=(pos, mean_opt), 
                                              xytext=(0, 10), 
                                              textcoords='offset points',
                                              ha='center', va='bottom',
                                              fontsize=9, fontweight='bold',
                                              color='darkred' if speedup < 2 else 'darkgreen')
        
        # Customize subplot
        ax.set_title(f'{storage_type}', fontsize=14, fontweight='bold')
        ax.set_xlabel('Cache Policy', fontsize=12)
        ax.set_ylabel('Throughput (ops/sec) - Log Scale', fontsize=12)
        ax.set_xticks(x_pos)
        ax.set_xticklabels(cache_types)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Set logarithmic scale for y-axis
        ax.set_yscale('log')
        
        # Format y-axis to show values in millions with log scale
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
        
        # Add legend for variants (only on first subplot)
        if i == 0:
            variant_legend = ax.legend(bbox_to_anchor=(0, 1), loc='upper left', fontsize=10)
            ax.add_artist(variant_legend)  # Keep this legend when adding operation legend
            
            # Add legend for operation error bars
            operation_handles = [plt.Line2D([0], [0], color=color, linewidth=3, alpha=0.8, label=op.replace('_', ' ').title()) 
                               for op, color in operation_colors.items()]
            ax.legend(handles=operation_handles, bbox_to_anchor=(1, 1), loc='upper left', 
                     fontsize=9, title='Operation Error Bars')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.94, right=0.85)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Option 1 Overlay with Stacked Error Bars saved to: {output_path}")
    
    return fig

def main():
    parser = argparse.ArgumentParser(description='Generate Option 1 Overlay with Stacked Error Bars')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output', default='option1_overlay_stacked_errors.pdf', help='Output file path')
    
    args = parser.parse_args()
    
    try:
        # Load data
        vanilla_df = load_vanilla_data(args.vanilla_csv)
        optimized_df = load_optimized_data(args.optimized_csv)
        
        # Create plot
        fig = create_stacked_error_overlay_plot(vanilla_df, optimized_df, args.output)
        
        print("Option 1 Overlay with Stacked Error Bars generation completed successfully!")
        
        # Print summary
        print("\n" + "="*60)
        print("STACKED ERROR BAR EXPLANATION")
        print("="*60)
        print("• Main bars show OVERALL average throughput across all operations")
        print("• Colored error bars show per-operation variance:")
        for op, color in [('delete', '#FF4444'), ('insert', '#44FF44'), ('search_random', '#4444FF'),
                         ('search_sequential', '#FF44FF'), ('search_uniform', '#44FFFF'), ('search_zipfian', '#FFFF44')]:
            print(f"  - {op.replace('_', ' ').title()}: {color}")
        print("• Small dots mark individual operation means")
        print("• Error bars represent standard deviation within each operation")
        print("• This shows both overall performance AND per-operation variability")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()