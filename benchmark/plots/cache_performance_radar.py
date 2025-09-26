#!/usr/bin/env python3
"""
Cache Performance Radar Charts: Vanilla vs Optimized
Shows radar/spider charts comparing multiple metrics simultaneously
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import argparse
from math import pi

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

def normalize_metrics(data, metrics_config):
    """Normalize metrics to 0-1 scale for radar chart"""
    normalized_data = data.copy()
    
    for metric, config in metrics_config.items():
        if metric in data.columns:
            values = data[metric]
            if config['higher_better']:
                # For metrics where higher is better, normalize to 0-1 where 1 is best
                min_val, max_val = values.min(), values.max()
                if max_val > min_val:
                    normalized_data[f'{metric}_norm'] = (values - min_val) / (max_val - min_val)
                else:
                    normalized_data[f'{metric}_norm'] = 1.0
            else:
                # For metrics where lower is better, invert so 1 is best (lowest value)
                min_val, max_val = values.min(), values.max()
                if max_val > min_val:
                    normalized_data[f'{metric}_norm'] = 1 - (values - min_val) / (max_val - min_val)
                else:
                    normalized_data[f'{metric}_norm'] = 1.0
    
    return normalized_data

def create_radar_chart(ax, data, labels, title, color, alpha=0.7):
    """Create a single radar chart"""
    
    # Number of variables
    N = len(labels)
    
    # Compute angle for each axis
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]  # Complete the circle
    
    # Add data point to complete the circle
    data += data[:1]
    
    # Plot
    ax.plot(angles, data, 'o-', linewidth=2, label=title, color=color)
    ax.fill(angles, data, alpha=alpha, color=color)
    
    # Add labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    
    # Set y-axis limits
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], fontsize=8)
    ax.grid(True)

def create_radar_comparison(vanilla_df, optimized_df, output_path):
    """Create radar charts comparing vanilla vs optimized across all metrics"""
    
    # Add variant labels
    vanilla_df['variant'] = 'Vanilla'
    optimized_df['variant'] = 'Optimized'
    
    # Combine data
    combined_df = pd.concat([vanilla_df, optimized_df], ignore_index=True)
    
    # Get unique storage types and rename them
    storage_type_mapping = {
        'FileStorage': 'SSD NVMe',
        'PMemStorage': 'NVM',
        'VolatileStorage': 'NVDIMM'
    }
    combined_df['storage_type'] = combined_df['storage_type'].map(storage_type_mapping)
    
    # Define metrics configuration
    metrics_config = {
        'cache_hits': {'title': 'Cache Hits', 'higher_better': True},
        'cache_misses': {'title': 'Cache Misses', 'higher_better': False},
        'perf_instructions': {'title': 'Instructions', 'higher_better': False},
        'perf_user_time': {'title': 'User Time', 'higher_better': False},
        'perf_sys_time': {'title': 'System Time', 'higher_better': False}
    }
    
    # Define custom order
    storage_types = ['NVDIMM', 'NVM', 'SSD NVMe']
    cache_types = sorted(combined_df['cache_type'].unique())
    thread_counts = sorted(combined_df['thread_count'].unique())
    
    # Normalize metrics across the entire dataset
    combined_df = normalize_metrics(combined_df, metrics_config)
    
    # Create figure with subplots
    n_rows = len(cache_types)
    n_cols = len(storage_types)
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(18, 24), subplot_kw=dict(projection='polar'))
    
    # Ensure axes is 2D
    if n_rows == 1:
        axes = axes.reshape(1, -1)
    if n_cols == 1:
        axes = axes.reshape(-1, 1)
    
    # Colors for variants
    colors = {'Vanilla': '#FF6B6B', 'Optimized': '#4ECDC4'}
    
    # Metric labels for radar chart
    metric_labels = [config['title'] for config in metrics_config.values()]
    
    for cache_idx, cache_type in enumerate(cache_types):
        for storage_idx, storage_type in enumerate(storage_types):
            ax = axes[cache_idx, storage_idx]
            
            # Filter data for this combination
            cache_storage_data = combined_df[
                (combined_df['cache_type'] == cache_type) &
                (combined_df['storage_type'] == storage_type)
            ]
            
            if len(cache_storage_data) == 0:
                ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
                continue
            
            # For each thread count, create radar charts
            for thread_count in thread_counts:
                thread_data = cache_storage_data[cache_storage_data['thread_count'] == thread_count]
                
                if len(thread_data) == 0:
                    continue
                
                # Calculate mean normalized values for each variant
                for variant in ['Vanilla', 'Optimized']:
                    variant_data = thread_data[thread_data['variant'] == variant]
                    
                    if len(variant_data) == 0:
                        continue
                    
                    # Get normalized metric values
                    radar_values = []
                    for metric in metrics_config.keys():
                        norm_metric = f'{metric}_norm'
                        if norm_metric in variant_data.columns:
                            radar_values.append(variant_data[norm_metric].mean())
                        else:
                            radar_values.append(0)
                    
                    # Create radar chart
                    alpha = 0.3 if thread_count == 1 else 0.6
                    line_style = '-' if variant == 'Vanilla' else '--'
                    
                    create_radar_chart(
                        ax, radar_values, metric_labels,
                        f'{variant} ({thread_count}T)',
                        colors[variant], alpha
                    )
            
            # Set title
            if cache_idx == 0:
                ax.set_title(f'{storage_type}\n{cache_type}', fontsize=12, fontweight='bold', pad=20)
            else:
                ax.set_title(f'{cache_type}', fontsize=12, fontweight='bold', pad=20)
    
    # Add legend
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.98), 
               ncol=4, fontsize=12, frameon=False)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.95)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Radar comparison saved to: {output_path}")
    
    return fig

def create_summary_radar(vanilla_df, optimized_df, output_path):
    """Create summary radar charts showing overall performance by storage type"""
    
    # Add variant labels
    vanilla_df['variant'] = 'Vanilla'
    optimized_df['variant'] = 'Optimized'
    
    # Combine data
    combined_df = pd.concat([vanilla_df, optimized_df], ignore_index=True)
    
    # Get unique storage types and rename them
    storage_type_mapping = {
        'FileStorage': 'SSD NVMe',
        'PMemStorage': 'NVM',
        'VolatileStorage': 'NVDIMM'
    }
    combined_df['storage_type'] = combined_df['storage_type'].map(storage_type_mapping)
    
    # Define metrics configuration
    metrics_config = {
        'cache_hits': {'title': 'Cache Hits', 'higher_better': True},
        'cache_misses': {'title': 'Cache Misses', 'higher_better': False},
        'perf_instructions': {'title': 'Instructions', 'higher_better': False},
        'perf_user_time': {'title': 'User Time', 'higher_better': False},
        'perf_sys_time': {'title': 'System Time', 'higher_better': False}
    }
    
    # Normalize metrics
    combined_df = normalize_metrics(combined_df, metrics_config)
    
    # Create figure with subplots for each storage type
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), subplot_kw=dict(projection='polar'))
    
    # Colors for variants
    colors = {'Vanilla': '#FF6B6B', 'Optimized': '#4ECDC4'}
    
    # Metric labels for radar chart
    metric_labels = [config['title'] for config in metrics_config.values()]
    
    storage_types = ['NVDIMM', 'NVM', 'SSD NVMe']
    
    for storage_idx, storage_type in enumerate(storage_types):
        ax = axes[storage_idx]
        
        # Filter data for this storage type
        storage_data = combined_df[combined_df['storage_type'] == storage_type]
        
        if len(storage_data) == 0:
            ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
            continue
        
        # Calculate overall averages for each variant
        for variant in ['Vanilla', 'Optimized']:
            variant_data = storage_data[storage_data['variant'] == variant]
            
            if len(variant_data) == 0:
                continue
            
            # Get normalized metric values (average across all cache types and thread counts)
            radar_values = []
            for metric in metrics_config.keys():
                norm_metric = f'{metric}_norm'
                if norm_metric in variant_data.columns:
                    radar_values.append(variant_data[norm_metric].mean())
                else:
                    radar_values.append(0)
            
            # Create radar chart
            create_radar_chart(
                ax, radar_values, metric_labels,
                variant, colors[variant], 0.4
            )
        
        # Set title
        ax.set_title(f'{storage_type}', fontsize=14, fontweight='bold', pad=20)
    
    # Add legend
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 1.1), 
               ncol=2, fontsize=12, frameon=False)
    
    plt.tight_layout()
    plt.savefig(output_path.replace('.pdf', '_summary.pdf'), dpi=300, bbox_inches='tight')
    print(f"Summary radar saved to: {output_path.replace('.pdf', '_summary.pdf')}")
    
    return fig

def main():
    parser = argparse.ArgumentParser(description='Generate cache performance radar charts')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output', default='cache_performance_radar.pdf', help='Output file path')
    parser.add_argument('--plot-type', choices=['detailed', 'summary', 'both'], default='both',
                       help='Type of radar chart to generate')
    
    args = parser.parse_args()
    
    try:
        # Load data
        vanilla_df = load_vanilla_data(args.vanilla_csv)
        optimized_df = load_optimized_data(args.optimized_csv)
        
        # Create plots based on selection
        if args.plot_type in ['detailed', 'both']:
            fig1 = create_radar_comparison(vanilla_df, optimized_df, args.output)
        
        if args.plot_type in ['summary', 'both']:
            fig2 = create_summary_radar(vanilla_df, optimized_df, args.output)
        
        print("Cache performance radar charts generated successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()