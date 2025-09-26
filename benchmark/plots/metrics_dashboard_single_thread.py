#!/usr/bin/env python3
"""
Cache and Performance Metrics Dashboard - Single Thread
Creates a comprehensive dashboard similar to metrics_dashboard.pdf but for 1 thread only
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
    
    # Check if we need to rename columns (optimized data might already have cache_type)
    if 'policy_name' in df.columns and 'cache_type' not in df.columns:
        df = df.rename(columns={'policy_name': 'cache_type'})
    
    # Check if we need to convert time units
    if 'time_us' in df.columns and 'time_ns' not in df.columns:
        df = df.rename(columns={'time_us': 'time_ns'})
        # Convert time from microseconds to nanoseconds
        df['time_ns'] = df['time_ns'] * 1000
    
    # Map config_name to thread_count if needed
    if 'config_name' in df.columns:
        df['thread_count'] = df['config_name'].map({
            'non_concurrent_default': 1,
            'concurrent_default': 4
        })
        # Filter out any unmapped configs
        df = df.dropna(subset=['thread_count'])
        df['thread_count'] = df['thread_count'].astype(int)
    
    return df

def create_single_thread_dashboard(vanilla_df, optimized_df, output_path):
    """Create a comprehensive dashboard with all metrics for single thread"""
    
    # Filter for single thread only
    vanilla_df = vanilla_df[vanilla_df['thread_count'] == 1].copy()
    optimized_df = optimized_df[optimized_df['thread_count'] == 1].copy()
    
    print(f"Filtered to single thread: {len(vanilla_df)} vanilla, {len(optimized_df)} optimized records")
    
    # Add variant labels
    vanilla_df['variant'] = 'Vanilla'
    optimized_df['variant'] = 'Optimized'
    
    # Combine data
    combined_df = pd.concat([vanilla_df, optimized_df], ignore_index=True)
    
    # Storage type mapping
    storage_type_mapping = {
        'FileStorage': 'SSD NVMe',
        'PMemStorage': 'NVM',
        'VolatileStorage': 'NVDIMM'
    }
    combined_df['storage_type'] = combined_df['storage_type'].map(storage_type_mapping)
    
    # Focus on VolatileStorage (NVDIMM) as it's available in both datasets for single thread
    storage_data = combined_df[combined_df['storage_type'] == 'NVDIMM']
    storage_name = 'NVDIMM'
    
    if len(storage_data) == 0:
        # Fallback to any available storage type
        available_storage = combined_df['storage_type'].unique()
        if len(available_storage) > 0:
            storage_data = combined_df[combined_df['storage_type'] == available_storage[0]]
            storage_name = available_storage[0]
    
    print(f"Using {storage_name} data: {len(storage_data)} records")
    
    cache_types = sorted(storage_data['cache_type'].unique())
    print(f"Available cache types: {cache_types}")
    
    # Create figure with subplots in a 2x3 grid
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Calculate summary statistics
    summary_stats = storage_data.groupby(['cache_type', 'variant'], as_index=False).agg({
        'cache_hits': 'mean',
        'cache_misses': 'mean', 
        'perf_instructions': 'mean',
        'perf_user_time': 'mean',
        'perf_sys_time': 'mean',
        'time_ns': 'mean',
        'record_count': 'mean'
    })
    
    # Calculate throughput
    summary_stats['throughput'] = summary_stats['record_count'] * 1e9 / summary_stats['time_ns']
    
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
        
        # Get data for both variants
        vanilla_data = summary_stats[summary_stats['variant'] == 'Vanilla']
        optimized_data = summary_stats[summary_stats['variant'] == 'Optimized']
        
        vanilla_values = []
        optimized_values = []
        improvements = []
        
        for cache_type in cache_types:
            vanilla_cache = vanilla_data[vanilla_data['cache_type'] == cache_type]
            optimized_cache = optimized_data[optimized_data['cache_type'] == cache_type]
            
            vanilla_val = vanilla_cache[metric].iloc[0] if len(vanilla_cache) > 0 else 0
            optimized_val = optimized_cache[metric].iloc[0] if len(optimized_cache) > 0 else 0
            
            vanilla_values.append(vanilla_val)
            optimized_values.append(optimized_val)
            
            # Calculate improvement (for throughput and cache hits, higher is better)
            if metric in ['throughput', 'cache_hits']:
                improvement = (optimized_val / vanilla_val) if vanilla_val > 0 else 0
            else:  # For misses, instructions, times - lower is better
                improvement = (vanilla_val / optimized_val) if optimized_val > 0 else 0
            improvements.append(improvement)
        
        # Plot bars
        bars1 = ax.bar(x_pos - bar_width/2, vanilla_values, bar_width, 
                      color=color, alpha=0.6, label='Vanilla')
        bars2 = ax.bar(x_pos + bar_width/2, optimized_values, bar_width, 
                      color=color, alpha=1.0, label='Optimized')
        
        # Add improvement annotations
        for i, (pos, improvement) in enumerate(zip(x_pos, improvements)):
            if improvement > 0:
                y_pos = max(vanilla_values[i], optimized_values[i])
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
    
    plt.suptitle(f'Performance Metrics Dashboard - {storage_name} (Single Thread)', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Single thread dashboard saved to: {output_path}")
    
    return fig, summary_stats

def create_all_storage_dashboard(vanilla_df, optimized_df, output_path):
    """Create dashboard showing all storage types for single thread"""
    
    # Filter for single thread only
    vanilla_df = vanilla_df[vanilla_df['thread_count'] == 1].copy()
    optimized_df = optimized_df[optimized_df['thread_count'] == 1].copy()
    
    # Add variant labels
    vanilla_df['variant'] = 'Vanilla'
    optimized_df['variant'] = 'Optimized'
    
    # Combine data
    combined_df = pd.concat([vanilla_df, optimized_df], ignore_index=True)
    
    # Storage type mapping
    storage_type_mapping = {
        'FileStorage': 'SSD NVMe',
        'PMemStorage': 'NVM',
        'VolatileStorage': 'NVDIMM'
    }
    combined_df['storage_type'] = combined_df['storage_type'].map(storage_type_mapping)
    
    storage_types = sorted(combined_df['storage_type'].unique())
    cache_types = sorted(combined_df['cache_type'].unique())
    
    # Create figure with subplots for each storage type
    fig, axes = plt.subplots(2, len(storage_types), figsize=(6*len(storage_types), 12))
    if len(storage_types) == 1:
        axes = axes.reshape(-1, 1)
    
    # Focus on two key metrics: throughput and system time
    metrics = [
        ('throughput', 'Throughput (M ops/sec)', '#228B22'),
        ('perf_sys_time', 'System Time (seconds)', '#8B008B')
    ]
    
    for storage_idx, storage_type in enumerate(storage_types):
        storage_data = combined_df[combined_df['storage_type'] == storage_type]
        
        if len(storage_data) == 0:
            continue
            
        # Calculate summary statistics
        summary_stats = storage_data.groupby(['cache_type', 'variant'], as_index=False).agg({
            'perf_sys_time': 'mean',
            'time_ns': 'mean',
            'record_count': 'mean'
        })
        
        # Calculate throughput
        summary_stats['throughput'] = summary_stats['record_count'] * 1e9 / summary_stats['time_ns']
        
        for metric_idx, (metric, title, color) in enumerate(metrics):
            ax = axes[metric_idx, storage_idx]
            
            x_pos = np.arange(len(cache_types))
            bar_width = 0.35
            
            # Get data for both variants
            vanilla_data = summary_stats[summary_stats['variant'] == 'Vanilla']
            optimized_data = summary_stats[summary_stats['variant'] == 'Optimized']
            
            vanilla_values = []
            optimized_values = []
            
            for cache_type in cache_types:
                vanilla_cache = vanilla_data[vanilla_data['cache_type'] == cache_type]
                optimized_cache = optimized_data[optimized_data['cache_type'] == cache_type]
                
                vanilla_val = vanilla_cache[metric].iloc[0] if len(vanilla_cache) > 0 else 0
                optimized_val = optimized_cache[metric].iloc[0] if len(optimized_cache) > 0 else 0
                
                vanilla_values.append(vanilla_val)
                optimized_values.append(optimized_val)
            
            # Plot bars
            bars1 = ax.bar(x_pos - bar_width/2, vanilla_values, bar_width, 
                          color=color, alpha=0.6, label='Vanilla')
            bars2 = ax.bar(x_pos + bar_width/2, optimized_values, bar_width, 
                          color=color, alpha=1.0, label='Optimized')
            
            ax.set_title(f'{storage_type}\\n{title}', fontsize=12, fontweight='bold')
            ax.set_xticks(x_pos)
            ax.set_xticklabels(cache_types, fontsize=10)
            ax.grid(True, alpha=0.3, axis='y')
            ax.tick_params(axis='y', labelsize=9)
            
            if metric == 'throughput':
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x/1e6:.1f}M'))
            else:
                ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.1f}s'))
            
            if storage_idx == 0 and metric_idx == 0:  # Only show legend on first subplot
                ax.legend(fontsize=10)
    
    plt.suptitle('Performance Comparison Across Storage Types (Single Thread)', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"All storage dashboard saved to: {output_path}")
    
    return fig

def generate_summary_report(summary_stats, output_path):
    """Generate a summary report of the findings"""
    
    with open(output_path, 'w') as f:
        f.write("SINGLE THREAD PERFORMANCE METRICS DASHBOARD ANALYSIS\\n")
        f.write("=" * 60 + "\\n\\n")
        
        f.write("SUMMARY STATISTICS\\n")
        f.write("-" * 20 + "\\n")
        f.write(summary_stats.round(3).to_string(index=False))
        f.write("\\n\\n")
        
        f.write("KEY PERFORMANCE IMPROVEMENTS (Optimized vs Vanilla)\\n")
        f.write("-" * 50 + "\\n")
        
        cache_types = summary_stats['cache_type'].unique()
        
        for cache_type in cache_types:
            vanilla_data = summary_stats[
                (summary_stats['cache_type'] == cache_type) & 
                (summary_stats['variant'] == 'Vanilla')
            ]
            optimized_data = summary_stats[
                (summary_stats['cache_type'] == cache_type) & 
                (summary_stats['variant'] == 'Optimized')
            ]
            
            if len(vanilla_data) > 0 and len(optimized_data) > 0:
                vanilla_row = vanilla_data.iloc[0]
                optimized_row = optimized_data.iloc[0]
                
                throughput_improvement = optimized_row['throughput'] / vanilla_row['throughput']
                sys_time_reduction = vanilla_row['perf_sys_time'] / optimized_row['perf_sys_time']
                hit_ratio_vanilla = vanilla_row['cache_hits'] / (vanilla_row['cache_hits'] + vanilla_row['cache_misses'])
                hit_ratio_optimized = optimized_row['cache_hits'] / (optimized_row['cache_hits'] + optimized_row['cache_misses'])
                
                f.write(f"\\n{cache_type} Policy:\\n")
                f.write(f"  • Throughput: {vanilla_row['throughput']/1e6:.1f}M → {optimized_row['throughput']/1e6:.1f}M ops/sec ({throughput_improvement:.1f}x improvement)\\n")
                f.write(f"  • System Time: {vanilla_row['perf_sys_time']:.1f}s → {optimized_row['perf_sys_time']:.1f}s ({sys_time_reduction:.1f}x reduction)\\n")
                f.write(f"  • Cache Hit Ratio: {hit_ratio_vanilla:.3f} → {hit_ratio_optimized:.3f}\\n")
                f.write(f"  • Cache Hits: {vanilla_row['cache_hits']/1e6:.1f}M → {optimized_row['cache_hits']/1e6:.1f}M\\n")
                f.write(f"  • Cache Misses: {vanilla_row['cache_misses']/1e6:.1f}M → {optimized_row['cache_misses']/1e6:.1f}M\\n")
    
    print(f"Summary report saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Generate single thread metrics dashboard')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output-dir', default='/home/skarim/Code/haldendb_ex/haldendb/benchmark/plots/single_thread_dashboard', 
                       help='Output directory for plots')
    parser.add_argument('--plot-type', choices=['main', 'all-storage', 'both'], 
                       default='both', help='Type of dashboard to generate')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    try:
        # Load data
        vanilla_df = load_vanilla_data(args.vanilla_csv)
        optimized_df = load_optimized_data(args.optimized_csv)
        
        # Generate plots based on selection
        if args.plot_type in ['main', 'both']:
            dashboard_output = os.path.join(args.output_dir, 'metrics_dashboard_single_thread.pdf')
            fig, summary_stats = create_single_thread_dashboard(vanilla_df, optimized_df, dashboard_output)
            
            # Generate summary report
            report_output = os.path.join(args.output_dir, 'SINGLE_THREAD_DASHBOARD_ANALYSIS.md')
            generate_summary_report(summary_stats, report_output)
        
        if args.plot_type in ['all-storage', 'both']:
            all_storage_output = os.path.join(args.output_dir, 'all_storage_comparison_single_thread.pdf')
            create_all_storage_dashboard(vanilla_df, optimized_df, all_storage_output)
        
        print("\\n✅ Single thread metrics dashboard generation completed successfully!")
        print(f"📁 All outputs saved to: {args.output_dir}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()