#!/usr/bin/env python3
"""
Throughput Analysis Plots
Focuses on performance comparison across cache types and operations
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# Set style
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
plt.style.use('default')
sns.set_palette("husl")
plt.rcParams['figure.facecolor'] = 'white'

def main():
    # Load data
    csv_file = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250922_123326/combined_benchmark_results_with_perf_20250922_132611.csv"
    df = pd.read_csv(csv_file)
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(20, 16))
    
    # 1. Box plot comparison
    sns.boxplot(data=df, x='operation', y='throughput_ops_sec', hue='cache_type', ax=axes[0,0])
    axes[0,0].set_title('Throughput Distribution by Operation and Cache Type', fontsize=14, fontweight='bold')
    axes[0,0].tick_params(axis='x', rotation=45)
    axes[0,0].set_ylabel('Throughput (ops/sec)')
    
    # 2. Heatmap
    perf_pivot = df.groupby(['cache_type', 'operation'])['throughput_ops_sec'].mean().unstack()
    sns.heatmap(perf_pivot, annot=True, fmt='.0f', cmap='YlOrRd', ax=axes[0,1])
    axes[0,1].set_title('Average Throughput Heatmap', fontsize=14, fontweight='bold')
    
    # 3. Bar plot with error bars
    df_summary = df.groupby(['cache_type', 'operation'])['throughput_ops_sec'].agg(['mean', 'std']).reset_index()
    df_summary['operation_cache'] = df_summary['operation'] + '_' + df_summary['cache_type']
    
    x_pos = np.arange(len(df_summary))
    colors = {'LRU': '#1f77b4', 'SSARC': '#ff7f0e', 'CLOCK': '#2ca02c'}
    
    for i, (cache, group) in enumerate(df_summary.groupby('cache_type')):
        indices = group.index
        axes[1,0].bar(x_pos[indices] + i*0.25, group['mean'], 0.25, 
                     yerr=group['std'], label=cache, color=colors[cache], alpha=0.8)
    
    axes[1,0].set_title('Average Throughput with Standard Deviation', fontsize=14, fontweight='bold')
    axes[1,0].set_xlabel('Operation')
    axes[1,0].set_ylabel('Throughput (ops/sec)')
    axes[1,0].set_xticks(x_pos + 0.25)
    axes[1,0].set_xticklabels(df_summary['operation'].unique(), rotation=45)
    axes[1,0].legend()
    
    # 4. Violin plot for distribution shape
    sns.violinplot(data=df, x='cache_type', y='throughput_ops_sec', ax=axes[1,1])
    axes[1,1].set_title('Throughput Distribution Shape by Cache Type', fontsize=14, fontweight='bold')
    axes[1,1].set_ylabel('Throughput (ops/sec)')
    
    plt.tight_layout()
    plt.savefig('/home/skarim/Code/haldendb_ex/haldendb/benchmark/plots/throughput_analysis.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✓ Generated: throughput_analysis.png")

if __name__ == "__main__":
    main()