#!/usr/bin/env python3
"""
Cache and Performance Metrics Visualization
Shows cache hits, cache misses, instructions, user time, and system time
Complements the throughput improvement plot with detailed performance analysis
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import argparse
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

def create_cache_metrics_plot(vanilla_df, optimized_df, output_path):
    """Create cache metrics comparison plot (hits vs misses)"""
    
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
    
    # Define order
    storage_types = ['NVDIMM', 'NVM', 'SSD NVMe']
    cache_types = sorted(combined_df['cache_type'].unique())
    thread_counts = sorted(combined_df['thread_count'].unique())
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    
    # Colors for cache hits (green) and misses (red)
    colors = {'hits': '#2E8B57', 'misses': '#DC143C'}
    
    for i, storage_type in enumerate(storage_types):
        storage_data = combined_df[combined_df['storage_type'] == storage_type]
        
        # Cache hits subplot (top row)
        ax_hits = axes[0, i]
        # Cache misses subplot (bottom row)  
        ax_misses = axes[1, i]
        
        # Calculate mean values for each combination
        summary_stats = storage_data.groupby(['cache_type', 'thread_count', 'variant']).agg({
            'cache_hits': ['mean', 'std'],
            'cache_misses': ['mean', 'std']
        }).reset_index()
        
        # Flatten column names
        summary_stats.columns = ['cache_type', 'thread_count', 'variant', 
                               'hits_mean', 'hits_std', 'misses_mean', 'misses_std']
        
        # Set up bar positions
        x_pos = np.arange(len(cache_types))
        bar_width = 0.35
        
        # Plot for each thread count and variant
        for j, thread_count in enumerate(thread_counts):
            v1_data = summary_stats[
                (summary_stats['thread_count'] == thread_count) & 
                (summary_stats['variant'] == 'Version 1')
            ]
            v2_data = summary_stats[
                (summary_stats['thread_count'] == thread_count) & 
                (summary_stats['variant'] == 'Version 2')
            ]
            
            if len(v1_data) == 0 or len(v2_data) == 0:
                continue
                
            # Prepare data arrays
            v1_hits = []
            v1_misses = []
            v2_hits = []
            v2_misses = []
            
            for cache_type in cache_types:
                v1_cache = v1_data[v1_data['cache_type'] == cache_type]
                v2_cache = v2_data[v2_data['cache_type'] == cache_type]
                
                v1_hits.append(v1_cache['hits_mean'].iloc[0] if len(v1_cache) > 0 else 0)
                v1_misses.append(v1_cache['misses_mean'].iloc[0] if len(v1_cache) > 0 else 0)
                v2_hits.append(v2_cache['hits_mean'].iloc[0] if len(v2_cache) > 0 else 0)
                v2_misses.append(v2_cache['misses_mean'].iloc[0] if len(v2_cache) > 0 else 0)
            
            # Plot cache hits
            offset = j * bar_width - bar_width/2
            ax_hits.bar(x_pos + offset, v1_hits, bar_width/2, 
                       color=colors['hits'], alpha=0.7, 
                       label=f'V1 ({thread_count}T)' if i == 0 else "")
            ax_hits.bar(x_pos + offset + bar_width/2, v2_hits, bar_width/2, 
                       color=colors['hits'], alpha=1.0,
                       label=f'V2 ({thread_count}T)' if i == 0 else "")
            
            # Plot cache misses
            ax_misses.bar(x_pos + offset, v1_misses, bar_width/2, 
                         color=colors['misses'], alpha=0.7,
                         label=f'V1 ({thread_count}T)' if i == 0 else "")
            ax_misses.bar(x_pos + offset + bar_width/2, v2_misses, bar_width/2, 
                         color=colors['misses'], alpha=1.0,
                         label=f'V2 ({thread_count}T)' if i == 0 else "")
        
        # Customize subplots
        ax_hits.set_title(f'{storage_type} - Cache Hits', fontsize=16, fontweight='bold')
        ax_misses.set_title(f'{storage_type} - Cache Misses', fontsize=16, fontweight='bold')
        
        for ax in [ax_hits, ax_misses]:
            ax.set_xticks(x_pos)
            ax.set_xticklabels(cache_types, fontsize=12)
            ax.grid(True, alpha=0.3, axis='y')
            ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
            ax.tick_params(axis='y', labelsize=10)
        
        if i == 0:
            ax_hits.set_ylabel('Cache Hits (Millions)', fontsize=12)
            ax_misses.set_ylabel('Cache Misses (Millions)', fontsize=12)
    
    # Add legend
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.95), 
               ncol=4, fontsize=12)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Cache metrics plot saved to: {output_path}")
    
    return fig

def create_performance_metrics_plot(vanilla_df, optimized_df, output_path):
    """Create performance metrics comparison plot (instructions, user time, system time)"""
    
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
    
    # Define order
    storage_types = ['NVDIMM', 'NVM', 'SSD NVMe']
    cache_types = sorted(combined_df['cache_type'].unique())
    thread_counts = sorted(combined_df['thread_count'].unique())
    
    # Create figure with subplots
    fig, axes = plt.subplots(3, 3, figsize=(20, 15))
    
    # Colors for different metrics
    colors = {
        'instructions': '#4169E1',
        'user_time': '#FF8C00', 
        'sys_time': '#8B008B'
    }
    
    for i, storage_type in enumerate(storage_types):
        storage_data = combined_df[combined_df['storage_type'] == storage_type]
        
        # Instructions subplot (top row)
        ax_inst = axes[0, i]
        # User time subplot (middle row)
        ax_user = axes[1, i]
        # System time subplot (bottom row)
        ax_sys = axes[2, i]
        
        # Calculate mean values for each combination
        summary_stats = storage_data.groupby(['cache_type', 'thread_count', 'variant']).agg({
            'perf_instructions': ['mean', 'std'],
            'perf_user_time': ['mean', 'std'],
            'perf_sys_time': ['mean', 'std']
        }).reset_index()
        
        # Flatten column names
        summary_stats.columns = ['cache_type', 'thread_count', 'variant', 
                               'inst_mean', 'inst_std', 'user_mean', 'user_std', 
                               'sys_mean', 'sys_std']
        
        # Set up bar positions
        x_pos = np.arange(len(cache_types))
        bar_width = 0.35
        
        # Plot for each thread count
        for j, thread_count in enumerate(thread_counts):
            v1_data = summary_stats[
                (summary_stats['thread_count'] == thread_count) & 
                (summary_stats['variant'] == 'Version 1')
            ]
            v2_data = summary_stats[
                (summary_stats['thread_count'] == thread_count) & 
                (summary_stats['variant'] == 'Version 2')
            ]
            
            if len(v1_data) == 0 or len(v2_data) == 0:
                continue
                
            # Prepare data arrays
            v1_inst = []
            v1_user = []
            v1_sys = []
            v2_inst = []
            v2_user = []
            v2_sys = []
            
            for cache_type in cache_types:
                v1_cache = v1_data[v1_data['cache_type'] == cache_type]
                v2_cache = v2_data[v2_data['cache_type'] == cache_type]
                
                v1_inst.append(v1_cache['inst_mean'].iloc[0] if len(v1_cache) > 0 else 0)
                v1_user.append(v1_cache['user_mean'].iloc[0] if len(v1_cache) > 0 else 0)
                v1_sys.append(v1_cache['sys_mean'].iloc[0] if len(v1_cache) > 0 else 0)
                v2_inst.append(v2_cache['inst_mean'].iloc[0] if len(v2_cache) > 0 else 0)
                v2_user.append(v2_cache['user_mean'].iloc[0] if len(v2_cache) > 0 else 0)
                v2_sys.append(v2_cache['sys_mean'].iloc[0] if len(v2_cache) > 0 else 0)
            
            # Plot instructions
            offset = j * bar_width - bar_width/2
            ax_inst.bar(x_pos + offset, v1_inst, bar_width/2, 
                       color=colors['instructions'], alpha=0.7,
                       label=f'V1 ({thread_count}T)' if i == 0 else "")
            ax_inst.bar(x_pos + offset + bar_width/2, v2_inst, bar_width/2, 
                       color=colors['instructions'], alpha=1.0,
                       label=f'V2 ({thread_count}T)' if i == 0 else "")
            
            # Plot user time
            ax_user.bar(x_pos + offset, v1_user, bar_width/2, 
                       color=colors['user_time'], alpha=0.7,
                       label=f'V1 ({thread_count}T)' if i == 0 else "")
            ax_user.bar(x_pos + offset + bar_width/2, v2_user, bar_width/2, 
                       color=colors['user_time'], alpha=1.0,
                       label=f'V2 ({thread_count}T)' if i == 0 else "")
            
            # Plot system time
            ax_sys.bar(x_pos + offset, v1_sys, bar_width/2, 
                      color=colors['sys_time'], alpha=0.7,
                      label=f'V1 ({thread_count}T)' if i == 0 else "")
            ax_sys.bar(x_pos + offset + bar_width/2, v2_sys, bar_width/2, 
                      color=colors['sys_time'], alpha=1.0,
                      label=f'V2 ({thread_count}T)' if i == 0 else "")
        
        # Customize subplots
        ax_inst.set_title(f'{storage_type} - Instructions', fontsize=16, fontweight='bold')
        ax_user.set_title(f'{storage_type} - User Time', fontsize=16, fontweight='bold')
        ax_sys.set_title(f'{storage_type} - System Time', fontsize=16, fontweight='bold')
        
        for ax in [ax_inst, ax_user, ax_sys]:
            ax.set_xticks(x_pos)
            ax.set_xticklabels(cache_types, fontsize=12)
            ax.grid(True, alpha=0.3, axis='y')
            ax.tick_params(axis='y', labelsize=10)
        
        # Format y-axes
        ax_inst.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e9:.1f}B'))
        ax_user.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}s'))
        ax_sys.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}s'))
        
        if i == 0:
            ax_inst.set_ylabel('Instructions (Billions)', fontsize=12)
            ax_user.set_ylabel('User Time (seconds)', fontsize=12)
            ax_sys.set_ylabel('System Time (seconds)', fontsize=12)
    
    # Add legend
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.97), 
               ncol=4, fontsize=12)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Performance metrics plot saved to: {output_path}")
    
    return fig

def create_combined_dashboard(vanilla_df, optimized_df, output_path):
    """Create a comprehensive dashboard with all metrics"""
    
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
    
    # Focus on one storage type for clarity (SSD NVMe as it's most common)
    storage_data = combined_df[combined_df['storage_type'] == 'SSD NVMe']
    
    cache_types = sorted(storage_data['cache_type'].unique())
    thread_counts = sorted(storage_data['thread_count'].unique())
    
    # Create figure with subplots in a 2x3 grid
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Calculate summary statistics
    summary_stats = storage_data.groupby(['cache_type', 'thread_count', 'variant']).agg({
        'cache_hits': 'mean',
        'cache_misses': 'mean', 
        'perf_instructions': 'mean',
        'perf_user_time': 'mean',
        'perf_sys_time': 'mean',
        'time_ns': 'mean'
    }).reset_index()
    
    # Calculate throughput
    summary_stats['throughput'] = summary_stats.apply(
        lambda row: storage_data[
            (storage_data['cache_type'] == row['cache_type']) &
            (storage_data['thread_count'] == row['thread_count']) &
            (storage_data['variant'] == row['variant'])
        ]['record_count'].iloc[0] * 1e9 / row['time_ns'] if len(storage_data[
            (storage_data['cache_type'] == row['cache_type']) &
            (storage_data['thread_count'] == row['thread_count']) &
            (storage_data['variant'] == row['variant'])
        ]) > 0 else 0, axis=1
    )
    
    metrics = [
        ('cache_hits', 'Cache Hits', '#2E8B57', lambda x, p: f'{x/1e6:.1f}M'),
        ('cache_misses', 'Cache Misses', '#DC143C', lambda x, p: f'{x/1e6:.1f}M'),
        ('perf_instructions', 'Instructions', '#4169E1', lambda x, p: f'{x/1e9:.1f}B'),
        ('perf_user_time', 'User Time', '#FF8C00', lambda x, p: f'{x:.1f}s'),
        ('perf_sys_time', 'System Time', '#8B008B', lambda x, p: f'{x:.1f}s'),
        ('throughput', 'Throughput', '#228B22', lambda x, p: f'{x/1e6:.1f}M')
    ]
    
    for idx, (metric, title, color, formatter) in enumerate(metrics):
        row = idx // 3
        col = idx % 3
        ax = axes[row, col]
        
        x_pos = np.arange(len(cache_types))
        bar_width = 0.35
        
        # Plot for 4 threads (most relevant)
        thread_count = 4
        v1_data = summary_stats[
            (summary_stats['thread_count'] == thread_count) & 
            (summary_stats['variant'] == 'Version 1')
        ]
        v2_data = summary_stats[
            (summary_stats['thread_count'] == thread_count) & 
            (summary_stats['variant'] == 'Version 2')
        ]
        
        v1_values = []
        v2_values = []
        improvements = []
        
        for cache_type in cache_types:
            v1_cache = v1_data[v1_data['cache_type'] == cache_type]
            v2_cache = v2_data[v2_data['cache_type'] == cache_type]
            
            v1_val = v1_cache[metric].iloc[0] if len(v1_cache) > 0 else 0
            v2_val = v2_cache[metric].iloc[0] if len(v2_cache) > 0 else 0
            
            v1_values.append(v1_val)
            v2_values.append(v2_val)
            
            # Calculate improvement (for throughput and cache hits, higher is better)
            if metric in ['throughput', 'cache_hits']:
                improvement = (v2_val / v1_val) if v1_val > 0 else 0
            else:  # For misses, instructions, times - lower is better
                improvement = (v1_val / v2_val) if v2_val > 0 else 0
            improvements.append(improvement)
        
        # Plot bars
        bars1 = ax.bar(x_pos - bar_width/2, v1_values, bar_width, 
                      color=color, alpha=0.6, label='Version 1')
        bars2 = ax.bar(x_pos + bar_width/2, v2_values, bar_width, 
                      color=color, alpha=1.0, label='Version 2')
        
        # Add improvement annotations
        for i, (pos, improvement) in enumerate(zip(x_pos, improvements)):
            if improvement > 0:
                y_pos = max(v1_values[i], v2_values[i])
                color_text = 'darkgreen' if improvement > 1.1 else 'darkred'
                ax.annotate(f'{improvement:.1f}x', 
                          xy=(pos, y_pos), 
                          xytext=(0, 5), 
                          textcoords='offset points',
                          ha='center', va='bottom',
                          fontsize=10, fontweight='bold',
                          color=color_text)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(cache_types, fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(formatter))
        ax.tick_params(axis='y', labelsize=9)
        
        if idx == 0:  # Only show legend on first subplot
            ax.legend(fontsize=10)
    
    plt.suptitle('Performance Metrics Dashboard - SSD NVMe (4 Threads)', 
                 fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Combined dashboard saved to: {output_path}")
    
    return fig

def main():
    parser = argparse.ArgumentParser(description='Generate cache and performance metrics visualizations')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output-dir', default='.', help='Output directory for plots')
    parser.add_argument('--plot-type', choices=['cache', 'performance', 'dashboard', 'all'], 
                       default='all', help='Type of plot to generate')
    
    args = parser.parse_args()
    
    try:
        # Load data
        vanilla_df = load_vanilla_data(args.vanilla_csv)
        optimized_df = load_optimized_data(args.optimized_csv)
        
        # Generate plots based on selection
        if args.plot_type in ['cache', 'all']:
            cache_output = os.path.join(args.output_dir, 'cache_metrics_comparison.pdf')
            create_cache_metrics_plot(vanilla_df, optimized_df, cache_output)
        
        if args.plot_type in ['performance', 'all']:
            perf_output = os.path.join(args.output_dir, 'performance_metrics_comparison.pdf')
            create_performance_metrics_plot(vanilla_df, optimized_df, perf_output)
        
        if args.plot_type in ['dashboard', 'all']:
            dashboard_output = os.path.join(args.output_dir, 'metrics_dashboard.pdf')
            create_combined_dashboard(vanilla_df, optimized_df, dashboard_output)
        
        print("Metrics visualization generation completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()