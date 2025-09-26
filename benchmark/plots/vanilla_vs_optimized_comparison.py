#!/usr/bin/env python3
"""
Vanilla vs Optimized Cache Policy Comparison
Compares LRU, A2Q, and CLOCK policies between vanilla and optimized variants,
grouped by operations and storage devices.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import argparse
from pathlib import Path

def load_and_process_data(vanilla_csv, optimized_csv):
    """Load and process data from both CSV files"""
    
    # Load vanilla data
    vanilla_df = pd.read_csv(vanilla_csv)
    vanilla_df['variant'] = 'Vanilla'
    vanilla_df['policy'] = vanilla_df['cache_type']
    
    # Normalize vanilla column names
    vanilla_normalized = vanilla_df.rename(columns={
        'perf_instructions': 'instructions',
        'perf_user_time': 'user_time', 
        'perf_sys_time': 'system_time'
    })
    
    # Load optimized data
    optimized_df = pd.read_csv(optimized_csv)
    optimized_df['variant'] = 'Optimized'
    optimized_df['policy'] = optimized_df['policy_name']
    
    # Normalize optimized column names
    optimized_normalized = optimized_df.rename(columns={
        'perf_instructions': 'instructions',
        'perf_user_time': 'user_time',
        'perf_sys_time': 'system_time'
    })
    
    # Select common columns
    common_cols = ['variant', 'policy', 'storage_type', 'operation', 'cache_hits', 'cache_misses',
                   'instructions', 'user_time', 'system_time', 'throughput_ops_sec']
    
    vanilla_clean = vanilla_normalized[common_cols].copy()
    optimized_clean = optimized_normalized[common_cols].copy()
    
    # Combine datasets
    combined_df = pd.concat([vanilla_clean, optimized_clean], ignore_index=True)
    
    # Filter for common policies (LRU, CLOCK, A2Q)
    # Note: A2Q only exists in optimized, so we'll handle this appropriately
    available_policies = combined_df['policy'].unique()
    print(f"Available policies: {available_policies}")
    
    # Convert metrics to readable units
    combined_df['cache_hits_M'] = combined_df['cache_hits'] / 1e6
    combined_df['cache_misses_M'] = combined_df['cache_misses'] / 1e6
    combined_df['instructions_B'] = combined_df['instructions'] / 1e9
    combined_df['throughput_K'] = combined_df['throughput_ops_sec'] / 1000
    
    # Calculate cache hit ratio
    combined_df['cache_hit_ratio'] = combined_df['cache_hits'] / (combined_df['cache_hits'] + combined_df['cache_misses'])
    
    return combined_df

def create_policy_comparison_plot(df, output_path):
    """Create comprehensive policy comparison plot"""
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("Set2")
    
    # Create figure with 2x3 subplots
    fig, axes = plt.subplots(2, 3, figsize=(20, 14))
    fig.suptitle('Cache Policy Comparison: Vanilla vs Optimized Variants\nLRU, CLOCK, and A2Q Performance Analysis', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Define metrics
    metrics = [
        {'col': 'cache_misses_M', 'title': 'Cache Misses', 'ylabel': 'Cache Misses (Millions)', 'pos': (0, 0)},
        {'col': 'cache_hits_M', 'title': 'Cache Hits', 'ylabel': 'Cache Hits (Millions)', 'pos': (0, 1)},
        {'col': 'instructions_B', 'title': 'Instructions', 'ylabel': 'Instructions (Billions)', 'pos': (0, 2)},
        {'col': 'user_time', 'title': 'User CPU Time', 'ylabel': 'User Time (seconds)', 'pos': (1, 0)},
        {'col': 'system_time', 'title': 'System CPU Time', 'ylabel': 'System Time (seconds)', 'pos': (1, 1)},
        {'col': 'throughput_K', 'title': 'Throughput', 'ylabel': 'Throughput (K ops/sec)', 'pos': (1, 2)}
    ]
    
    # Create box plots for each metric
    for metric in metrics:
        row, col = metric['pos']
        ax = axes[row, col]
        
        # Create combined grouping for better visualization
        df['policy_variant'] = df['policy'] + '_' + df['variant']
        
        # Create box plot
        sns.boxplot(data=df, x='policy', y=metric['col'], hue='variant', ax=ax, dodge=True)
        
        # Customize subplot
        ax.set_title(metric['title'], fontsize=14, fontweight='bold', pad=10)
        ax.set_xlabel('Cache Policy', fontsize=12, fontweight='bold')
        ax.set_ylabel(metric['ylabel'], fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='both', labelsize=10)
        
        # Rotate x-axis labels for better readability
        ax.tick_params(axis='x', rotation=45)
        
        # Add legend only to first subplot
        if row == 0 and col == 0:
            ax.legend(title='Variant', title_fontsize=10, fontsize=9, loc='upper right')
        else:
            if ax.get_legend():
                ax.get_legend().remove()
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.93, hspace=0.3, wspace=0.3)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Policy comparison plot saved to: {output_path}")
    
    return fig

def create_storage_operation_heatmap(df, output_path):
    """Create heatmap showing performance across storage types and operations"""
    
    # Calculate mean throughput for each combination
    heatmap_data = df.groupby(['storage_type', 'operation', 'policy', 'variant'])['throughput_K'].mean().reset_index()
    
    # Create pivot table for heatmap
    pivot_data = heatmap_data.pivot_table(
        index=['storage_type', 'operation'], 
        columns=['policy', 'variant'], 
        values='throughput_K'
    )
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Create heatmap
    sns.heatmap(pivot_data, annot=True, fmt='.0f', cmap='RdYlGn', 
                ax=ax, cbar_kws={'label': 'Throughput (K ops/sec)'})
    
    ax.set_title('Throughput Heatmap: Storage Type × Operation × Policy × Variant', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Policy × Variant', fontsize=12, fontweight='bold')
    ax.set_ylabel('Storage Type × Operation', fontsize=12, fontweight='bold')
    
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Storage-operation heatmap saved to: {output_path}")
    
    return fig

def create_detailed_comparison_by_storage(df, output_path):
    """Create detailed comparison grouped by storage type"""
    
    storage_types = df['storage_type'].unique()
    
    fig, axes = plt.subplots(len(storage_types), 2, figsize=(16, 6*len(storage_types)))
    if len(storage_types) == 1:
        axes = axes.reshape(1, -1)
    
    fig.suptitle('Detailed Performance Analysis by Storage Type\nThroughput and Cache Hit Ratio Comparison', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    for i, storage in enumerate(storage_types):
        storage_data = df[df['storage_type'] == storage]
        
        # Throughput comparison
        ax1 = axes[i, 0]
        sns.boxplot(data=storage_data, x='operation', y='throughput_K', 
                   hue='policy_variant', ax=ax1, dodge=True)
        ax1.set_title(f'{storage} - Throughput by Operation', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Operation', fontsize=10)
        ax1.set_ylabel('Throughput (K ops/sec)', fontsize=10)
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, alpha=0.3)
        
        # Cache hit ratio comparison
        ax2 = axes[i, 1]
        sns.boxplot(data=storage_data, x='operation', y='cache_hit_ratio', 
                   hue='policy_variant', ax=ax2, dodge=True)
        ax2.set_title(f'{storage} - Cache Hit Ratio by Operation', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Operation', fontsize=10)
        ax2.set_ylabel('Cache Hit Ratio', fontsize=10)
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, alpha=0.3)
        
        # Handle legends
        if i == 0:
            ax1.legend(title='Policy × Variant', bbox_to_anchor=(1.05, 1), loc='upper left')
            ax2.legend(title='Policy × Variant', bbox_to_anchor=(1.05, 1), loc='upper left')
        else:
            if ax1.get_legend():
                ax1.get_legend().remove()
            if ax2.get_legend():
                ax2.get_legend().remove()
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.95, right=0.85)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Detailed storage comparison saved to: {output_path}")
    
    return fig

def print_comprehensive_analysis(df):
    """Print comprehensive statistical analysis"""
    
    print("\n" + "="*80)
    print("COMPREHENSIVE PERFORMANCE ANALYSIS")
    print("="*80)
    
    # Overall summary
    print(f"Total records: {len(df)}")
    print(f"Policies: {sorted(df['policy'].unique())}")
    print(f"Variants: {sorted(df['variant'].unique())}")
    print(f"Storage types: {sorted(df['storage_type'].unique())}")
    print(f"Operations: {sorted(df['operation'].unique())}")
    
    # Performance summary by policy and variant
    print("\n" + "-"*60)
    print("THROUGHPUT COMPARISON (K ops/sec)")
    print("-"*60)
    
    throughput_summary = df.groupby(['policy', 'variant'])['throughput_K'].agg(['mean', 'std', 'count']).round(2)
    print(throughput_summary)
    
    # Cache efficiency comparison
    print("\n" + "-"*60)
    print("CACHE HIT RATIO COMPARISON")
    print("-"*60)
    
    cache_summary = df.groupby(['policy', 'variant'])['cache_hit_ratio'].agg(['mean', 'std']).round(3)
    print(cache_summary)
    
    # System resource usage
    print("\n" + "-"*60)
    print("SYSTEM RESOURCE USAGE (seconds)")
    print("-"*60)
    
    resource_summary = df.groupby(['policy', 'variant'])[['user_time', 'system_time']].agg(['mean', 'std']).round(2)
    print(resource_summary)
    
    # Best performing combinations
    print("\n" + "-"*60)
    print("TOP 10 BEST PERFORMING COMBINATIONS (by throughput)")
    print("-"*60)
    
    best_combinations = df.groupby(['policy', 'variant', 'storage_type', 'operation'])['throughput_K'].mean().reset_index()
    best_combinations = best_combinations.sort_values('throughput_K', ascending=False).head(10)
    print(best_combinations.to_string(index=False))

def main():
    parser = argparse.ArgumentParser(description='Compare vanilla vs optimized cache policies')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output-dir', default='.', help='Output directory for plots')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print("Loading and processing data...")
    df = load_and_process_data(args.vanilla_csv, args.optimized_csv)
    
    # Print comprehensive analysis
    print_comprehensive_analysis(df)
    
    print("\nCreating policy comparison plot...")
    policy_plot = create_policy_comparison_plot(
        df, output_dir / 'policy_comparison_vanilla_vs_optimized.png'
    )
    
    print("Creating storage-operation heatmap...")
    heatmap_plot = create_storage_operation_heatmap(
        df, output_dir / 'storage_operation_heatmap.png'
    )
    
    print("Creating detailed storage comparison...")
    storage_plot = create_detailed_comparison_by_storage(
        df, output_dir / 'detailed_storage_comparison.png'
    )
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE!")
    print("="*80)
    print(f"""
📊 Generated Visualizations:
1. Policy Comparison (2×3 box plots): Shows LRU, CLOCK, A2Q across vanilla/optimized
2. Storage-Operation Heatmap: Shows throughput across all combinations
3. Detailed Storage Analysis: Breakdown by storage type with throughput and cache hit ratios

🎯 Key Insights:
• Compare how each policy performs in vanilla vs optimized variants
• Identify which storage types benefit most from optimizations
• See which operations show the biggest improvements
• Understand cache efficiency improvements across policies

📈 Use these plots to:
• Show the impact of your optimizations across different cache policies
• Demonstrate that improvements aren't limited to one policy
• Identify the best policy-storage-operation combinations
• Support technical discussions about cache policy effectiveness
    """)
    
    plt.show()

if __name__ == "__main__":
    main()