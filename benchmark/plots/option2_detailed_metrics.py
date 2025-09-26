#!/usr/bin/env python3
"""
Option 2: Detailed Performance Metrics Analysis
Complements the throughput improvement plot with cache and system metrics
Shows cache efficiency, instruction count, and CPU time breakdown
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

def create_detailed_metrics_plot(vanilla_df, optimized_df, output_path):
    """Create detailed metrics plot showing cache efficiency and system metrics"""
    
    # Add variant labels
    vanilla_df['variant'] = 'Version 1'
    optimized_df['variant'] = 'Version 2'
    
    # Combine data
    combined_df = pd.concat([vanilla_df, optimized_df], ignore_index=True)
    
    # Storage type mapping
    storage_type_mapping = {
        'FileStorage': 'SSD NVMe',
        'PMemStorage': 'NVM',
        'VolatileStorage': 'NVDIMM'
    }
    combined_df['storage_type'] = combined_df['storage_type'].map(storage_type_mapping)
    
    # Calculate cache hit ratio if not present
    if 'cache_hit_ratio' not in combined_df.columns:
        combined_df['cache_hit_ratio'] = combined_df['cache_hits'] / (combined_df['cache_hits'] + combined_df['cache_misses'])
    
    # Define order
    storage_types = ['NVDIMM', 'NVM', 'SSD NVMe']
    cache_types = sorted(combined_df['cache_type'].unique())
    
    # Create figure with 4 rows of subplots
    fig, axes = plt.subplots(4, 3, figsize=(20, 16))
    
    # Focus on 4 threads for clarity
    thread_count = 4
    
    # Metrics to plot
    metrics_config = [
        {
            'column': 'cache_hit_ratio',
            'title': 'Cache Hit Ratio',
            'ylabel': 'Hit Ratio',
            'color': '#2E8B57',
            'formatter': lambda x, p: f'{x:.2f}',
            'row': 0
        },
        {
            'column': 'perf_instructions',
            'title': 'Instructions per Operation',
            'ylabel': 'Instructions (Billions)',
            'color': '#4169E1',
            'formatter': lambda x, p: f'{x/1e9:.1f}B',
            'row': 1
        },
        {
            'column': 'perf_user_time',
            'title': 'User CPU Time',
            'ylabel': 'User Time (seconds)',
            'color': '#FF8C00',
            'formatter': lambda x, p: f'{x:.1f}s',
            'row': 2
        },
        {
            'column': 'perf_sys_time',
            'title': 'System CPU Time',
            'ylabel': 'System Time (seconds)',
            'color': '#8B008B',
            'formatter': lambda x, p: f'{x:.1f}s',
            'row': 3
        }
    ]
    
    for i, storage_type in enumerate(storage_types):
        storage_data = combined_df[
            (combined_df['storage_type'] == storage_type) &
            (combined_df['thread_count'] == thread_count)
        ]
        
        if len(storage_data) == 0:
            continue
        
        # Calculate summary statistics
        summary_stats = storage_data.groupby(['cache_type', 'variant']).agg({
            'cache_hit_ratio': 'mean',
            'perf_instructions': 'mean',
            'perf_user_time': 'mean',
            'perf_sys_time': 'mean'
        }).reset_index()
        
        for metric_config in metrics_config:
            row = metric_config['row']
            ax = axes[row, i]
            
            # Set up bar positions
            x_pos = np.arange(len(cache_types))
            bar_width = 0.35
            
            v1_values = []
            v2_values = []
            improvements = []
            
            for cache_type in cache_types:
                v1_data = summary_stats[
                    (summary_stats['cache_type'] == cache_type) & 
                    (summary_stats['variant'] == 'Version 1')
                ]
                v2_data = summary_stats[
                    (summary_stats['cache_type'] == cache_type) & 
                    (summary_stats['variant'] == 'Version 2')
                ]
                
                v1_val = v1_data[metric_config['column']].iloc[0] if len(v1_data) > 0 else 0
                v2_val = v2_data[metric_config['column']].iloc[0] if len(v2_data) > 0 else 0
                
                v1_values.append(v1_val)
                v2_values.append(v2_val)
                
                # Calculate improvement ratio
                if metric_config['column'] == 'cache_hit_ratio':
                    # For hit ratio, show the difference
                    improvement = v2_val - v1_val
                    improvements.append(improvement)
                elif metric_config['column'] == 'perf_instructions':
                    # For instructions, lower is better
                    improvement = (v1_val / v2_val) if v2_val > 0 else 0
                    improvements.append(improvement)
                else:
                    # For CPU times, lower is better
                    improvement = (v1_val / v2_val) if v2_val > 0 else 0
                    improvements.append(improvement)
            
            # Plot bars
            bars1 = ax.bar(x_pos - bar_width/2, v1_values, bar_width, 
                          color=metric_config['color'], alpha=0.6, 
                          label='Version 1' if i == 0 else "")
            bars2 = ax.bar(x_pos + bar_width/2, v2_values, bar_width, 
                          color=metric_config['color'], alpha=1.0,
                          label='Version 2' if i == 0 else "")
            
            # Add improvement annotations
            for j, (pos, improvement) in enumerate(zip(x_pos, improvements)):
                if improvement != 0:
                    y_pos = max(v1_values[j], v2_values[j])
                    
                    if metric_config['column'] == 'cache_hit_ratio':
                        # Show difference for hit ratio
                        text = f'{improvement:+.2f}'
                        color_text = 'darkgreen' if improvement > 0 else 'darkred'
                    else:
                        # Show ratio for other metrics
                        text = f'{improvement:.1f}x'
                        color_text = 'darkgreen' if improvement > 1.1 else 'darkred'
                    
                    ax.annotate(text, 
                              xy=(pos, y_pos), 
                              xytext=(0, 5), 
                              textcoords='offset points',
                              ha='center', va='bottom',
                              fontsize=12, fontweight='bold',
                              color=color_text)
            
            # Customize subplot
            ax.set_title(f'{storage_type} - {metric_config["title"]}', 
                        fontsize=16, fontweight='bold')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(cache_types, fontsize=14)
            ax.grid(True, alpha=0.3, axis='y')
            ax.yaxis.set_major_formatter(plt.FuncFormatter(metric_config['formatter']))
            ax.tick_params(axis='y', labelsize=12)
            
            if i == 0:
                ax.set_ylabel(metric_config['ylabel'], fontsize=14)
                if row == 0:  # Only show legend on first row, first column
                    ax.legend(fontsize=12)
    
    plt.suptitle('Detailed Performance Metrics Analysis (4 Threads)', 
                 fontsize=20, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Detailed metrics plot saved to: {output_path}")
    
    return fig

def main():
    parser = argparse.ArgumentParser(description='Generate Option 2: Detailed metrics plot')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output', default='option2_detailed_metrics.pdf', help='Output file path')
    
    args = parser.parse_args()
    
    try:
        # Load data
        vanilla_df = load_vanilla_data(args.vanilla_csv)
        optimized_df = load_optimized_data(args.optimized_csv)
        
        # Create plot
        fig = create_detailed_metrics_plot(vanilla_df, optimized_df, args.output)
        
        print("Option 2 detailed metrics plot generation completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()