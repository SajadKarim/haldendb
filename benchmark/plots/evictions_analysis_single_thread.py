#!/usr/bin/env python3
"""
Cache Policy Evictions Analysis - Single Thread
Compares LRU, A2Q (SSARC), and CLOCK policies between vanilla and optimized variants,
showing evictions instead of throughput, filtered for single thread only.
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
    optimized_df['policy'] = optimized_df['cache_type']  # Use cache_type instead of policy_name
    
    # Normalize optimized column names
    optimized_normalized = optimized_df.rename(columns={
        'perf_instructions': 'instructions',
        'perf_user_time': 'user_time',
        'perf_sys_time': 'system_time'
    })
    
    # Select common columns
    common_cols = ['variant', 'policy', 'storage_type', 'operation', 'cache_hits', 'cache_misses',
                   'instructions', 'user_time', 'system_time', 'evictions', 'thread_count']
    
    vanilla_clean = vanilla_normalized[common_cols].copy()
    optimized_clean = optimized_normalized[common_cols].copy()
    
    # Filter for single thread only (thread_count == 1)
    vanilla_clean = vanilla_clean[vanilla_clean['thread_count'] == 1]
    optimized_clean = optimized_clean[optimized_clean['thread_count'] == 1]
    
    # Combine datasets
    combined_df = pd.concat([vanilla_clean, optimized_clean], ignore_index=True)
    
    # Replace SSARC with A2Q for consistency
    combined_df['policy'] = combined_df['policy'].replace('SSARC', 'A2Q')
    
    # Filter for common policies (LRU, CLOCK, A2Q)
    available_policies = combined_df['policy'].unique()
    print(f"Available policies: {available_policies}")
    
    # Convert metrics to readable units
    combined_df['cache_hits_M'] = combined_df['cache_hits'] / 1e6
    combined_df['cache_misses_M'] = combined_df['cache_misses'] / 1e6
    combined_df['instructions_B'] = combined_df['instructions'] / 1e9
    combined_df['evictions_K'] = combined_df['evictions'] / 1000
    
    # Calculate cache hit ratio
    combined_df['cache_hit_ratio'] = combined_df['cache_hits'] / (combined_df['cache_hits'] + combined_df['cache_misses'])
    
    print(f"Total measurements: {len(combined_df)}")
    print(f"Policies by variant:")
    print(combined_df.groupby(['variant', 'policy']).size())
    
    return combined_df

def create_policy_comparison_plot(df, output_path):
    """Create comprehensive policy comparison plot with evictions"""
    
    # Set up the plotting style
    plt.style.use('default')
    sns.set_palette("Set2")
    
    # Create figure with 2x3 subplots
    fig, axes = plt.subplots(2, 3, figsize=(20, 14))
    fig.suptitle('Cache Policy Comparison: Vanilla vs Optimized Variants (Single Thread)\nLRU, CLOCK, and A2Q Performance Analysis', 
                 fontsize=16, fontweight='bold', y=0.98)
    
    # Define metrics
    metrics = [
        {'col': 'cache_misses_M', 'title': 'Cache Misses', 'ylabel': 'Cache Misses (Millions)', 'pos': (0, 0)},
        {'col': 'cache_hits_M', 'title': 'Cache Hits', 'ylabel': 'Cache Hits (Millions)', 'pos': (0, 1)},
        {'col': 'instructions_B', 'title': 'Instructions', 'ylabel': 'Instructions (Billions)', 'pos': (0, 2)},
        {'col': 'user_time', 'title': 'User CPU Time', 'ylabel': 'User Time (seconds)', 'pos': (1, 0)},
        {'col': 'system_time', 'title': 'System CPU Time', 'ylabel': 'System Time (seconds)', 'pos': (1, 1)},
        {'col': 'evictions_K', 'title': 'Cache Evictions', 'ylabel': 'Evictions (Thousands)', 'pos': (1, 2)}
    ]
    
    # Create box plots for each metric
    for metric in metrics:
        row, col = metric['pos']
        ax = axes[row, col]
        
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
    """Create heatmap showing evictions across storage types and operations"""
    
    # Calculate mean evictions for each combination
    heatmap_data = df.groupby(['storage_type', 'operation', 'policy', 'variant'])['evictions_K'].mean().reset_index()
    
    # Create pivot table for heatmap
    pivot_data = heatmap_data.pivot_table(
        index=['storage_type', 'operation'], 
        columns=['policy', 'variant'], 
        values='evictions_K'
    )
    
    # Create figure
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Create heatmap
    sns.heatmap(pivot_data, annot=True, fmt='.0f', cmap='YlOrRd', 
                ax=ax, cbar_kws={'label': 'Evictions (K)'})
    
    ax.set_title('Cache Evictions Heatmap: Storage Type × Operation × Policy × Variant (Single Thread)', 
                 fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Policy × Variant', fontsize=12, fontweight='bold')
    ax.set_ylabel('Storage Type × Operation', fontsize=12, fontweight='bold')
    
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Storage-operation heatmap saved to: {output_path}")
    
    return fig

def create_detailed_storage_comparison(df, output_path):
    """Create detailed comparison by storage type"""
    
    # Calculate statistics by storage type
    storage_stats = df.groupby(['storage_type', 'policy', 'variant']).agg({
        'evictions_K': ['mean', 'std', 'count'],
        'cache_hit_ratio': ['mean', 'std']
    }).round(2)
    
    # Flatten column names
    storage_stats.columns = ['_'.join(col).strip() for col in storage_stats.columns]
    storage_stats = storage_stats.reset_index()
    
    # Create figure with subplots for each storage type
    storage_types = df['storage_type'].unique()
    n_storage = len(storage_types)
    
    fig, axes = plt.subplots(1, n_storage, figsize=(6*n_storage, 8))
    if n_storage == 1:
        axes = [axes]
    
    fig.suptitle('Cache Evictions by Storage Type and Policy (Single Thread)', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    for i, storage in enumerate(storage_types):
        ax = axes[i]
        storage_data = df[df['storage_type'] == storage]
        
        # Create box plot for this storage type
        sns.boxplot(data=storage_data, x='policy', y='evictions_K', hue='variant', ax=ax, dodge=True)
        
        ax.set_title(f'{storage}', fontsize=14, fontweight='bold')
        ax.set_xlabel('Cache Policy', fontsize=12, fontweight='bold')
        ax.set_ylabel('Evictions (Thousands)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', rotation=45)
        
        # Add legend only to first subplot
        if i == 0:
            ax.legend(title='Variant', title_fontsize=10, fontsize=9)
        else:
            if ax.get_legend():
                ax.get_legend().remove()
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.88)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Detailed storage comparison saved to: {output_path}")
    
    return fig, storage_stats

def generate_summary_statistics(df, output_path):
    """Generate comprehensive summary statistics"""
    
    # Overall statistics by policy and variant
    overall_stats = df.groupby(['policy', 'variant']).agg({
        'evictions_K': ['count', 'mean', 'std', 'min', 'max'],
        'cache_hits_M': ['mean', 'std'],
        'cache_misses_M': ['mean', 'std'],
        'cache_hit_ratio': ['mean', 'std'],
        'user_time': ['mean', 'std'],
        'system_time': ['mean', 'std'],
        'instructions_B': ['mean', 'std']
    }).round(3)
    
    # Flatten column names
    overall_stats.columns = ['_'.join(col).strip() for col in overall_stats.columns]
    overall_stats = overall_stats.reset_index()
    
    # Calculate improvement ratios (Optimized vs Vanilla)
    improvement_analysis = []
    
    for policy in df['policy'].unique():
        vanilla_data = df[(df['policy'] == policy) & (df['variant'] == 'Vanilla')]
        optimized_data = df[(df['policy'] == policy) & (df['variant'] == 'Optimized')]
        
        if len(vanilla_data) > 0 and len(optimized_data) > 0:
            vanilla_evictions = vanilla_data['evictions_K'].mean()
            optimized_evictions = optimized_data['evictions_K'].mean()
            
            vanilla_hit_ratio = vanilla_data['cache_hit_ratio'].mean()
            optimized_hit_ratio = optimized_data['cache_hit_ratio'].mean()
            
            vanilla_sys_time = vanilla_data['system_time'].mean()
            optimized_sys_time = optimized_data['system_time'].mean()
            
            improvement_analysis.append({
                'Policy': policy,
                'Evictions_Change_%': ((optimized_evictions - vanilla_evictions) / vanilla_evictions * 100) if vanilla_evictions > 0 else 0,
                'Hit_Ratio_Improvement_%': ((optimized_hit_ratio - vanilla_hit_ratio) / vanilla_hit_ratio * 100) if vanilla_hit_ratio > 0 else 0,
                'System_Time_Reduction_%': ((vanilla_sys_time - optimized_sys_time) / vanilla_sys_time * 100) if vanilla_sys_time > 0 else 0,
                'Vanilla_Evictions_K': vanilla_evictions,
                'Optimized_Evictions_K': optimized_evictions,
                'Vanilla_Hit_Ratio': vanilla_hit_ratio,
                'Optimized_Hit_Ratio': optimized_hit_ratio
            })
    
    improvement_df = pd.DataFrame(improvement_analysis)
    
    # Save to file
    with open(output_path, 'w') as f:
        f.write("CACHE POLICY EVICTIONS ANALYSIS - SINGLE THREAD\\n")
        f.write("=" * 60 + "\\n\\n")
        
        f.write("OVERALL STATISTICS BY POLICY AND VARIANT\\n")
        f.write("-" * 45 + "\\n")
        f.write(overall_stats.to_string(index=False))
        f.write("\\n\\n")
        
        f.write("IMPROVEMENT ANALYSIS (Optimized vs Vanilla)\\n")
        f.write("-" * 45 + "\\n")
        f.write(improvement_df.round(2).to_string(index=False))
        f.write("\\n\\n")
        
        f.write("KEY INSIGHTS:\\n")
        f.write("-" * 15 + "\\n")
        
        for _, row in improvement_df.iterrows():
            f.write(f"\\n{row['Policy']} Policy:\\n")
            f.write(f"  • Evictions: {row['Vanilla_Evictions_K']:.1f}K → {row['Optimized_Evictions_K']:.1f}K ")
            f.write(f"({row['Evictions_Change_%']:+.1f}% change)\\n")
            f.write(f"  • Hit Ratio: {row['Vanilla_Hit_Ratio']:.3f} → {row['Optimized_Hit_Ratio']:.3f} ")
            f.write(f"({row['Hit_Ratio_Improvement_%']:+.1f}% improvement)\\n")
            f.write(f"  • System Time Reduction: {row['System_Time_Reduction_%']:.1f}%\\n")
    
    print(f"Summary statistics saved to: {output_path}")
    return overall_stats, improvement_df

def main():
    parser = argparse.ArgumentParser(description='Cache Policy Evictions Analysis - Single Thread')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output-dir', default='/home/skarim/Code/haldendb_ex/haldendb/benchmark/plots/evictions_analysis_single_thread', 
                       help='Output directory for plots and analysis')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load and process data
    print("Loading and processing data...")
    df = load_and_process_data(args.vanilla_csv, args.optimized_csv)
    
    # Generate visualizations
    print("\\nGenerating policy comparison plot...")
    create_policy_comparison_plot(df, output_dir / 'policy_comparison_evictions_single_thread.png')
    
    print("\\nGenerating storage-operation heatmap...")
    create_storage_operation_heatmap(df, output_dir / 'storage_operation_evictions_heatmap_single_thread.png')
    
    print("\\nGenerating detailed storage comparison...")
    fig, storage_stats = create_detailed_storage_comparison(df, output_dir / 'detailed_storage_evictions_comparison_single_thread.png')
    
    print("\\nGenerating summary statistics...")
    overall_stats, improvement_df = generate_summary_statistics(df, output_dir / 'EVICTIONS_ANALYSIS_SINGLE_THREAD.md')
    
    print(f"\\n✅ Analysis complete! All outputs saved to: {output_dir}")
    print(f"\\n📊 Key Findings:")
    print("=" * 50)
    
    for _, row in improvement_df.iterrows():
        print(f"\\n{row['Policy']} Policy:")
        print(f"  • Evictions: {row['Vanilla_Evictions_K']:.1f}K → {row['Optimized_Evictions_K']:.1f}K ({row['Evictions_Change_%']:+.1f}%)")
        print(f"  • Hit Ratio: {row['Vanilla_Hit_Ratio']:.3f} → {row['Optimized_Hit_Ratio']:.3f} ({row['Hit_Ratio_Improvement_%']:+.1f}%)")
        print(f"  • System Time Reduction: {row['System_Time_Reduction_%']:.1f}%")

if __name__ == "__main__":
    main()