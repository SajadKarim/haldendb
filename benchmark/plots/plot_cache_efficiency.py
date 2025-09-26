#!/usr/bin/env python3
"""
Cache Efficiency Analysis
Focuses on cache hit ratios, miss rates, and cache behavior
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
    
    # Create comprehensive cache efficiency analysis
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    
    # 1. Cache Hit Ratio vs Throughput
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    for i, cache in enumerate(df['cache_type'].unique()):
        cache_data = df[df['cache_type'] == cache]
        axes[0,0].scatter(cache_data['cache_hit_ratio'], cache_data['throughput_ops_sec'], 
                         label=cache, alpha=0.7, s=60, color=colors[i])
    
    axes[0,0].set_xlabel('Cache Hit Ratio')
    axes[0,0].set_ylabel('Throughput (ops/sec)')
    axes[0,0].set_title('Cache Hit Ratio vs Throughput', fontweight='bold')
    axes[0,0].legend()
    axes[0,0].grid(True, alpha=0.3)
    
    # 2. Hit Ratio by Operation
    sns.boxplot(data=df, x='operation', y='cache_hit_ratio', hue='cache_type', ax=axes[0,1])
    axes[0,1].set_title('Cache Hit Ratio by Operation', fontweight='bold')
    axes[0,1].tick_params(axis='x', rotation=45)
    axes[0,1].set_ylabel('Cache Hit Ratio')
    
    # 3. Cache Misses vs Evictions
    for i, cache in enumerate(df['cache_type'].unique()):
        cache_data = df[df['cache_type'] == cache]
        axes[1,0].scatter(cache_data['cache_misses'], cache_data['evictions'], 
                         label=cache, alpha=0.7, s=60, color=colors[i])
    
    axes[1,0].set_xlabel('Cache Misses')
    axes[1,0].set_ylabel('Evictions')
    axes[1,0].set_title('Cache Misses vs Evictions', fontweight='bold')
    axes[1,0].legend()
    axes[1,0].grid(True, alpha=0.3)
    
    # 4. Dirty Evictions Analysis
    sns.boxplot(data=df, x='cache_type', y='dirty_evictions', ax=axes[1,1])
    axes[1,1].set_title('Dirty Evictions by Cache Type', fontweight='bold')
    axes[1,1].set_ylabel('Dirty Evictions')
    
    # 5. Cache Efficiency Heatmap
    efficiency_metrics = ['cache_hit_ratio', 'cache_misses', 'evictions', 'dirty_evictions']
    efficiency_pivot = df.groupby(['cache_type', 'operation'])[efficiency_metrics].mean()
    
    # Normalize for better visualization
    efficiency_normalized = efficiency_pivot.copy()
    for col in efficiency_metrics:
        efficiency_normalized[col] = (efficiency_normalized[col] - efficiency_normalized[col].min()) / (efficiency_normalized[col].max() - efficiency_normalized[col].min())
    
    # Create heatmap for one metric at a time
    hit_ratio_pivot = df.groupby(['cache_type', 'operation'])['cache_hit_ratio'].mean().unstack()
    sns.heatmap(hit_ratio_pivot, annot=True, fmt='.3f', cmap='RdYlGn', ax=axes[2,0])
    axes[2,0].set_title('Cache Hit Ratio Heatmap', fontweight='bold')
    
    # 6. Cache Performance Summary
    cache_summary = df.groupby('cache_type').agg({
        'cache_hit_ratio': ['mean', 'std'],
        'cache_misses': ['mean', 'std'],
        'evictions': ['mean', 'std'],
        'throughput_ops_sec': ['mean', 'std']
    }).round(3)
    
    # Create a summary bar plot
    cache_means = df.groupby('cache_type')['cache_hit_ratio'].mean()
    cache_stds = df.groupby('cache_type')['cache_hit_ratio'].std()
    
    x_pos = np.arange(len(cache_means))
    axes[2,1].bar(x_pos, cache_means.values, yerr=cache_stds.values, 
                  color=colors, alpha=0.8, capsize=5)
    axes[2,1].set_xticks(x_pos)
    axes[2,1].set_xticklabels(cache_means.index)
    axes[2,1].set_title('Average Cache Hit Ratio by Cache Type', fontweight='bold')
    axes[2,1].set_ylabel('Cache Hit Ratio')
    
    plt.tight_layout()
    plt.savefig('/home/skarim/Code/haldendb_ex/haldendb/benchmark/plots/cache_efficiency_analysis.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✓ Generated: cache_efficiency_analysis.png")

if __name__ == "__main__":
    main()