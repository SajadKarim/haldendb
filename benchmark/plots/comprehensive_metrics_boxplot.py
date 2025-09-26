#!/usr/bin/env python3
"""
Comprehensive Metrics Box Plot Visualization
Creates a 2x3 subplot showing cache misses, cache hits, instructions, 
user time, system time, and throughput as box plots grouped by policy type,
storage type, and operation type.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import argparse
from pathlib import Path

def load_and_normalize_data(vanilla_csv, optimized_csv):
    """Load and normalize data from both CSV files"""
    
    # Load vanilla data (CLOCK policy)
    vanilla_df = pd.read_csv(vanilla_csv)
    vanilla_df['policy_type'] = 'CLOCK'
    
    # Normalize column names for vanilla data
    vanilla_normalized = vanilla_df.rename(columns={
        'cache_type': 'policy_name',
        'perf_instructions': 'instructions',
        'perf_user_time': 'user_time', 
        'perf_sys_time': 'system_time'
    })
    
    # Select relevant columns
    vanilla_cols = ['policy_type', 'storage_type', 'operation', 'cache_hits', 'cache_misses', 
                   'instructions', 'user_time', 'system_time', 'throughput_ops_sec']
    vanilla_clean = vanilla_normalized[vanilla_cols].copy()
    
    # Load optimized data (A2Q policy)  
    optimized_df = pd.read_csv(optimized_csv)
    optimized_df['policy_type'] = 'A2Q'
    
    # Normalize column names for optimized data
    optimized_normalized = optimized_df.rename(columns={
        'policy_name': 'policy_name_orig',
        'perf_instructions': 'instructions',
        'perf_user_time': 'user_time',
        'perf_sys_time': 'system_time'
    })
    
    # Select relevant columns
    optimized_cols = ['policy_type', 'storage_type', 'operation', 'cache_hits', 'cache_misses',
                     'instructions', 'user_time', 'system_time', 'throughput_ops_sec']
    optimized_clean = optimized_normalized[optimized_cols].copy()
    
    # Combine datasets
    combined_df = pd.concat([vanilla_clean, optimized_clean], ignore_index=True)
    
    # Convert metrics to more readable units
    combined_df['cache_hits_M'] = combined_df['cache_hits'] / 1e6  # Millions
    combined_df['cache_misses_M'] = combined_df['cache_misses'] / 1e6  # Millions  
    combined_df['instructions_B'] = combined_df['instructions'] / 1e9  # Billions
    combined_df['user_time_s'] = combined_df['user_time']  # Already in seconds
    combined_df['system_time_s'] = combined_df['system_time']  # Already in seconds
    combined_df['throughput_K'] = combined_df['throughput_ops_sec'] / 1000  # Thousands
    
    return combined_df

def create_comprehensive_boxplot(df, output_path):
    """Create 2x3 comprehensive metrics box plot"""
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("husl")
    
    # Create figure with 2x3 subplots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Performance Metrics Comparison: CLOCK vs A2Q Cache Policies\nGrouped by Storage Type and Operation Type', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Define metrics and their properties
    metrics = [
        {'col': 'cache_misses_M', 'title': 'Cache Misses', 'ylabel': 'Cache Misses (Millions)', 'pos': (0, 0)},
        {'col': 'cache_hits_M', 'title': 'Cache Hits', 'ylabel': 'Cache Hits (Millions)', 'pos': (0, 1)},
        {'col': 'instructions_B', 'title': 'Instructions', 'ylabel': 'Instructions (Billions)', 'pos': (0, 2)},
        {'col': 'user_time_s', 'title': 'User CPU Time', 'ylabel': 'User Time (seconds)', 'pos': (1, 0)},
        {'col': 'system_time_s', 'title': 'System CPU Time', 'ylabel': 'System Time (seconds)', 'pos': (1, 1)},
        {'col': 'throughput_K', 'title': 'Throughput', 'ylabel': 'Throughput (K ops/sec)', 'pos': (1, 2)}
    ]
    
    # Create box plots for each metric
    for metric in metrics:
        row, col = metric['pos']
        ax = axes[row, col]
        
        # Create combined grouping variable for better visualization
        df['group'] = df['policy_type'] + '_' + df['storage_type'] + '_' + df['operation']
        
        # Create box plot
        box_plot = sns.boxplot(data=df, x='policy_type', y=metric['col'], 
                              hue='storage_type', ax=ax, dodge=True)
        
        # Customize the subplot
        ax.set_title(metric['title'], fontsize=14, fontweight='bold', pad=10)
        ax.set_xlabel('Policy Type', fontsize=12, fontweight='bold')
        ax.set_ylabel(metric['ylabel'], fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Rotate x-axis labels if needed
        ax.tick_params(axis='x', rotation=0)
        ax.tick_params(axis='both', labelsize=10)
        
        # Add legend only to the first subplot to avoid clutter
        if row == 0 and col == 0:
            ax.legend(title='Storage Type', title_fontsize=10, fontsize=9, loc='upper right')
        else:
            ax.get_legend().remove() if ax.get_legend() else None
    
    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.93, hspace=0.3, wspace=0.3)
    
    # Save the plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Comprehensive box plot saved to: {output_path}")
    
    return fig

def create_detailed_analysis_boxplot(df, output_path):
    """Create detailed analysis with operation type breakdown"""
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("Set2")
    
    # Create figure with 2x3 subplots
    fig, axes = plt.subplots(2, 3, figsize=(20, 14))
    fig.suptitle('Detailed Performance Analysis: Policy × Storage × Operation Breakdown\nBox Plots Showing Distribution Across Multiple Runs', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Define metrics and their properties
    metrics = [
        {'col': 'cache_misses_M', 'title': 'Cache Misses Distribution', 'ylabel': 'Cache Misses (Millions)', 'pos': (0, 0)},
        {'col': 'cache_hits_M', 'title': 'Cache Hits Distribution', 'ylabel': 'Cache Hits (Millions)', 'pos': (0, 1)},
        {'col': 'instructions_B', 'title': 'Instructions Distribution', 'ylabel': 'Instructions (Billions)', 'pos': (0, 2)},
        {'col': 'user_time_s', 'title': 'User CPU Time Distribution', 'ylabel': 'User Time (seconds)', 'pos': (1, 0)},
        {'col': 'system_time_s', 'title': 'System CPU Time Distribution', 'ylabel': 'System Time (seconds)', 'pos': (1, 1)},
        {'col': 'throughput_K', 'title': 'Throughput Distribution', 'ylabel': 'Throughput (K ops/sec)', 'pos': (1, 2)}
    ]
    
    # Create box plots for each metric with operation type breakdown
    for metric in metrics:
        row, col = metric['pos']
        ax = axes[row, col]
        
        # Create box plot with policy type on x-axis and operation type as hue
        sns.boxplot(data=df, x='policy_type', y=metric['col'], 
                   hue='operation', ax=ax, dodge=True)
        
        # Customize the subplot
        ax.set_title(metric['title'], fontsize=14, fontweight='bold', pad=10)
        ax.set_xlabel('Policy Type', fontsize=12, fontweight='bold')
        ax.set_ylabel(metric['ylabel'], fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # Rotate x-axis labels if needed
        ax.tick_params(axis='x', rotation=0)
        ax.tick_params(axis='both', labelsize=10)
        
        # Add legend only to the top row to avoid clutter
        if row == 0:
            ax.legend(title='Operation Type', title_fontsize=10, fontsize=9, 
                     bbox_to_anchor=(1.05, 1), loc='upper left')
        else:
            ax.get_legend().remove() if ax.get_legend() else None
    
    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.93, hspace=0.3, wspace=0.25, right=0.85)
    
    # Save the plot
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Detailed analysis box plot saved to: {output_path}")
    
    return fig

def print_data_summary(df):
    """Print summary statistics about the data"""
    print("\n" + "="*60)
    print("DATA SUMMARY")
    print("="*60)
    
    print(f"Total records: {len(df)}")
    print(f"Policy types: {df['policy_type'].unique()}")
    print(f"Storage types: {df['storage_type'].unique()}")
    print(f"Operation types: {df['operation'].unique()}")
    
    print("\nRecords per policy:")
    print(df['policy_type'].value_counts())
    
    print("\nRecords per storage type:")
    print(df['storage_type'].value_counts())
    
    print("\nRecords per operation:")
    print(df['operation'].value_counts())
    
    # Performance comparison summary
    print("\n" + "="*60)
    print("PERFORMANCE COMPARISON SUMMARY")
    print("="*60)
    
    summary_stats = df.groupby('policy_type').agg({
        'cache_hits_M': ['mean', 'std'],
        'cache_misses_M': ['mean', 'std'], 
        'instructions_B': ['mean', 'std'],
        'user_time_s': ['mean', 'std'],
        'system_time_s': ['mean', 'std'],
        'throughput_K': ['mean', 'std']
    }).round(2)
    
    print(summary_stats)

def main():
    parser = argparse.ArgumentParser(description='Create comprehensive metrics box plots')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output-dir', default='.', help='Output directory for plots')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print("Loading and processing data...")
    df = load_and_normalize_data(args.vanilla_csv, args.optimized_csv)
    
    # Print data summary
    print_data_summary(df)
    
    print("\nCreating comprehensive box plot...")
    comprehensive_plot = create_comprehensive_boxplot(
        df, output_dir / 'comprehensive_metrics_boxplot.png'
    )
    
    print("Creating detailed analysis box plot...")
    detailed_plot = create_detailed_analysis_boxplot(
        df, output_dir / 'detailed_analysis_boxplot.png'
    )
    
    print("\n" + "="*60)
    print("VISUALIZATION INSIGHTS")
    print("="*60)
    print("""
    📊 WHAT THESE PLOTS SHOW:
    
    1. **Comprehensive Box Plot**: Shows distribution of each metric grouped by policy type and storage type
       - Compares CLOCK vs A2Q policies across different storage backends
       - Box plots show median, quartiles, and outliers for each metric
    
    2. **Detailed Analysis Plot**: Shows breakdown by operation type (insert, delete, search_*)
       - Reveals which operations benefit most from the A2Q policy
       - Shows variability across different workload patterns
    
    📈 KEY INSIGHTS TO LOOK FOR:
    
    • **Cache Efficiency**: A2Q should show higher cache hits and lower cache misses
    • **CPU Efficiency**: A2Q should show lower instruction counts and CPU times
    • **Throughput**: A2Q should show higher throughput across most operations
    • **Consistency**: A2Q should show less variability (smaller boxes) indicating more predictable performance
    
    🎯 PRESENTATION STRATEGY:
    
    • Use these plots to explain WHY your throughput improvements occurred
    • The box plots show the distribution and consistency of improvements
    • Different operations may show different levels of improvement
    • Storage type differences reveal where optimizations are most effective
    """)
    
    plt.show()

if __name__ == "__main__":
    main()