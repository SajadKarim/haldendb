#!/usr/bin/env python3
"""
Cache Performance Comparison: Vanilla vs Optimized
Shows detailed comparison of cache hits, cache misses, instructions, user time, and system time
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import argparse
import seaborn as sns
from matplotlib.patches import Rectangle

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

def create_multi_metric_dashboard(vanilla_df, optimized_df, output_path):
    """Create comprehensive dashboard comparing cache and performance metrics"""
    
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
    
    # Define metrics to plot
    metrics = {
        'cache_hits': {'title': 'Cache Hits', 'unit': 'Millions', 'scale': 1e6, 'higher_better': True},
        'cache_misses': {'title': 'Cache Misses', 'unit': 'Millions', 'scale': 1e6, 'higher_better': False},
        'perf_instructions': {'title': 'Instructions', 'unit': 'Billions', 'scale': 1e9, 'higher_better': False},
        'perf_user_time': {'title': 'User Time', 'unit': 'Seconds', 'scale': 1, 'higher_better': False},
        'perf_sys_time': {'title': 'System Time', 'unit': 'Seconds', 'scale': 1, 'higher_better': False}
    }
    
    # Define custom order
    storage_types = ['NVDIMM', 'NVM', 'SSD NVMe']
    cache_types = sorted(combined_df['cache_type'].unique())
    thread_counts = sorted(combined_df['thread_count'].unique())
    
    # Create figure with subplots (5 metrics x 3 storage types)
    fig, axes = plt.subplots(len(metrics), len(storage_types), figsize=(18, 25))
    
    # Patterns for variants and threads (using same pattern as option1_overlay_comparison.py)
    patterns = {
        ('Version 1', 1): '///',        # Diagonal lines
        ('Version 1', 4): '\\\\\\',     # Reverse diagonal lines
        ('Version 2', 1): '...',      # Dots
        ('Version 2', 4): 'xxx'       # Crosses
    }
    
    for metric_idx, (metric_name, metric_info) in enumerate(metrics.items()):
        for storage_idx, storage_type in enumerate(storage_types):
            ax = axes[metric_idx, storage_idx]
            
            # Filter data for this storage type
            storage_data = combined_df[combined_df['storage_type'] == storage_type]
            
            if len(storage_data) == 0:
                ax.text(0.5, 0.5, 'No Data', ha='center', va='center', transform=ax.transAxes)
                continue
            
            # Calculate mean values for each combination
            summary_stats = storage_data.groupby(['cache_type', 'thread_count', 'variant'])[metric_name].agg(['mean', 'std']).reset_index()
            
            # Set up bar positions
            x_pos = np.arange(len(cache_types))
            bar_width = 0.15
            
            # Plot bars for each combination
            for thread_idx, thread_count in enumerate(thread_counts):
                for variant_idx, variant in enumerate(['Version 1', 'Version 2']):
                    data_subset = summary_stats[
                        (summary_stats['thread_count'] == thread_count) & 
                        (summary_stats['variant'] == variant)
                    ]
                    
                    if len(data_subset) == 0:
                        continue
                    
                    # Calculate bar positions
                    offset = (thread_idx * 2 + variant_idx - 1.5) * bar_width
                    positions = x_pos + offset
                    
                    means = []
                    stds = []
                    for cache_type in cache_types:
                        cache_data = data_subset[data_subset['cache_type'] == cache_type]
                        if len(cache_data) > 0:
                            mean_val = cache_data['mean'].iloc[0] / metric_info['scale']
                            std_val = cache_data['std'].iloc[0] / metric_info['scale'] if not pd.isna(cache_data['std'].iloc[0]) else 0
                            means.append(mean_val)
                            stds.append(std_val)
                        else:
                            means.append(0)
                            stds.append(0)
                    
                    # Plot bars with error bars using patterns
                    bars = ax.bar(positions, means, bar_width, 
                                 color='white',
                                 edgecolor='black',
                                 hatch=patterns[(variant, thread_count)],
                                 alpha=1.0,
                                 yerr=stds,
                                 capsize=3,
                                 label=f'{variant} ({thread_count} thread{"s" if thread_count > 1 else ""})' if metric_idx == 0 and storage_idx == 0 else "")
                    
                    # Add improvement annotations for optimized bars
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
                                    mean_vanilla = vanilla_data['mean'].iloc[0] / metric_info['scale']
                                    if mean_vanilla > 0:
                                        if metric_info['higher_better']:
                                            improvement = (mean_opt - mean_vanilla) / mean_vanilla * 100
                                            color = 'darkgreen' if improvement > 0 else 'darkred'
                                            symbol = '+' if improvement > 0 else ''
                                        else:
                                            improvement = (mean_vanilla - mean_opt) / mean_vanilla * 100
                                            color = 'darkgreen' if improvement > 0 else 'darkred'
                                            symbol = '+' if improvement > 0 else ''
                                        
                                        if abs(improvement) > 1:  # Only show if improvement > 1%
                                            ax.annotate(f'{symbol}{improvement:.0f}%', 
                                                      xy=(pos, mean_opt), 
                                                      xytext=(-5, 5), 
                                                      textcoords='offset points',
                                                      ha='center', va='bottom',
                                                      fontsize=18, fontweight='bold',
                                                      color=color,
                                                      rotation=90)
            
            # Customize subplot
            if metric_idx == 0:  # Top row - show storage type titles
                ax.set_title(f'{storage_type}', fontsize=28, fontweight='bold')
            if storage_idx == 0:  # Left column - show metric labels
                ax.set_ylabel(f'{metric_info["title"]}', fontsize=24, fontweight='bold')
            
            ax.set_xticks(x_pos)
            if metric_idx == len(metrics) - 1:  # Only show x-labels on bottom row
                ax.set_xticklabels(cache_types, fontsize=20, rotation=45)
            else:
                ax.set_xticklabels([])
            
            ax.grid(True, alpha=0.3, axis='y')
            ax.tick_params(axis='y', labelsize=18)
    
    # Add legend to the first subplot (top-left) in single column
    handles, labels = axes[0, 0].get_legend_handles_labels()
    axes[0, 0].legend(handles, labels, loc='upper left', bbox_to_anchor=(-0.02, 1), 
                     ncol=1, fontsize=20, frameon=True, fancybox=True, shadow=True)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.98)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Multi-metric dashboard saved to: {output_path}")
    
    return fig

def create_improvement_heatmap(vanilla_df, optimized_df, output_path):
    """Create heatmap showing percentage improvements across all metrics"""
    
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
    
    # Define metrics (negative improvement means better for these metrics)
    metrics = {
        'cache_hits': True,  # higher is better
        'cache_misses': False,  # lower is better
        'perf_instructions': False,  # lower is better
        'perf_user_time': False,  # lower is better
        'perf_sys_time': False  # lower is better
    }
    
    # Calculate improvements for each combination
    improvements = []
    
    for storage_type in ['NVDIMM', 'NVM', 'SSD NVMe']:
        for thread_count in sorted(combined_df['thread_count'].unique()):
            for cache_type in sorted(combined_df['cache_type'].unique()):
                
                # Get vanilla and optimized data
                vanilla_data = combined_df[
                    (combined_df['storage_type'] == storage_type) &
                    (combined_df['thread_count'] == thread_count) &
                    (combined_df['cache_type'] == cache_type) &
                    (combined_df['variant'] == 'Version 1')
                ]
                
                optimized_data = combined_df[
                    (combined_df['storage_type'] == storage_type) &
                    (combined_df['thread_count'] == thread_count) &
                    (combined_df['cache_type'] == cache_type) &
                    (combined_df['variant'] == 'Version 2')
                ]
                
                if len(vanilla_data) > 0 and len(optimized_data) > 0:
                    row = {
                        'Storage': storage_type,
                        'Threads': f'{thread_count}T',
                        'Cache': cache_type
                    }
                    
                    for metric, higher_better in metrics.items():
                        vanilla_mean = vanilla_data[metric].mean()
                        optimized_mean = optimized_data[metric].mean()
                        
                        if vanilla_mean > 0:
                            if higher_better:
                                improvement = (optimized_mean - vanilla_mean) / vanilla_mean * 100
                            else:
                                improvement = (vanilla_mean - optimized_mean) / vanilla_mean * 100
                            
                            row[metric.replace('perf_', '').replace('_', ' ').title()] = improvement
                    
                    improvements.append(row)
    
    if not improvements:
        print("No matching data found for heatmap")
        return None
    
    # Create DataFrame
    df_improvements = pd.DataFrame(improvements)
    
    # Create pivot table for heatmap
    fig, axes = plt.subplots(1, 3, figsize=(20, 8))
    
    metric_cols = [col for col in df_improvements.columns if col not in ['Storage', 'Threads', 'Cache']]
    
    for i, storage_type in enumerate(['NVDIMM', 'NVM', 'SSD NVMe']):
        storage_data = df_improvements[df_improvements['Storage'] == storage_type]
        
        if len(storage_data) == 0:
            continue
        
        # Create pivot table
        pivot_data = storage_data.pivot_table(
            index=['Cache', 'Threads'], 
            values=metric_cols, 
            aggfunc='mean'
        )
        
        # Create heatmap
        sns.heatmap(pivot_data, 
                   annot=True, 
                   fmt='.1f', 
                   cmap='RdYlGn', 
                   center=0,
                   ax=axes[i],
                   cbar_kws={'label': 'Improvement (%)'})
        
        axes[i].set_title(f'{storage_type}', fontsize=14, fontweight='bold')
        axes[i].set_xlabel('')
        if i == 0:
            axes[i].set_ylabel('Cache Policy & Threads', fontsize=12)
        else:
            axes[i].set_ylabel('')
    
    plt.tight_layout()
    plt.savefig(output_path.replace('.pdf', '_heatmap.pdf'), dpi=300, bbox_inches='tight')
    print(f"Improvement heatmap saved to: {output_path.replace('.pdf', '_heatmap.pdf')}")
    
    return fig

def main():
    parser = argparse.ArgumentParser(description='Generate cache performance comparison plots')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output', default='cache_performance_comparison.pdf', help='Output file path')
    parser.add_argument('--plot-type', choices=['dashboard', 'heatmap', 'both'], default='both',
                       help='Type of plot to generate')
    
    args = parser.parse_args()
    
    try:
        # Load data
        vanilla_df = load_vanilla_data(args.vanilla_csv)
        optimized_df = load_optimized_data(args.optimized_csv)
        
        # Create plots based on selection
        if args.plot_type in ['dashboard', 'both']:
            fig1 = create_multi_metric_dashboard(vanilla_df, optimized_df, args.output)
        
        if args.plot_type in ['heatmap', 'both']:
            fig2 = create_improvement_heatmap(vanilla_df, optimized_df, args.output)
        
        print("Cache performance comparison plots generated successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()