#!/usr/bin/env python3
"""
Hardware Performance Counter Analysis
Focuses on CPU-level metrics and hardware efficiency
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
    
    # Calculate derived metrics
    df['ipc'] = df['perf_instructions'] / df['perf_cycles']
    df['cache_miss_rate'] = df['perf_cache_misses'] / df['perf_cache_references']
    df['l1_miss_rate'] = df['perf_l1_dcache_load_misses'] / df['perf_l1_dcache_loads']
    df['llc_miss_rate'] = df['perf_llc_load_misses'] / df['perf_llc_loads']
    df['branch_miss_rate'] = df['perf_branch_misses'] / df['perf_instructions']
    
    # Create comprehensive hardware analysis
    fig, axes = plt.subplots(3, 2, figsize=(16, 18))
    
    # 1. Instructions Per Cycle (IPC)
    sns.boxplot(data=df, x='cache_type', y='ipc', ax=axes[0,0])
    axes[0,0].set_title('Instructions Per Cycle (IPC) Distribution', fontweight='bold')
    axes[0,0].set_ylabel('IPC')
    
    # 2. Hardware Cache Miss Rate
    sns.boxplot(data=df, x='cache_type', y='cache_miss_rate', ax=axes[0,1])
    axes[0,1].set_title('Hardware Cache Miss Rate Distribution', fontweight='bold')
    axes[0,1].set_ylabel('Cache Miss Rate')
    
    # 3. L1 vs LLC Miss Rates
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    for i, cache in enumerate(df['cache_type'].unique()):
        cache_data = df[df['cache_type'] == cache]
        axes[1,0].scatter(cache_data['l1_miss_rate'], cache_data['llc_miss_rate'], 
                         label=cache, alpha=0.7, s=60, color=colors[i])
    
    axes[1,0].set_xlabel('L1 Cache Miss Rate')
    axes[1,0].set_ylabel('LLC Miss Rate')
    axes[1,0].set_title('L1 vs LLC Miss Rates', fontweight='bold')
    axes[1,0].legend()
    axes[1,0].grid(True, alpha=0.3)
    
    # 4. IPC vs Throughput Correlation
    for i, cache in enumerate(df['cache_type'].unique()):
        cache_data = df[df['cache_type'] == cache]
        axes[1,1].scatter(cache_data['ipc'], cache_data['throughput_ops_sec'], 
                         label=cache, alpha=0.7, s=60, color=colors[i])
    
    axes[1,1].set_xlabel('Instructions Per Cycle (IPC)')
    axes[1,1].set_ylabel('Throughput (ops/sec)')
    axes[1,1].set_title('IPC vs Throughput Correlation', fontweight='bold')
    axes[1,1].legend()
    axes[1,1].grid(True, alpha=0.3)
    
    # 5. Hardware Metrics Heatmap
    hw_metrics = ['ipc', 'cache_miss_rate', 'l1_miss_rate', 'llc_miss_rate', 'branch_miss_rate']
    hw_pivot = df.groupby(['cache_type', 'operation'])[hw_metrics].mean()
    
    # Create correlation matrix
    hw_corr = df[hw_metrics + ['throughput_ops_sec']].corr()
    sns.heatmap(hw_corr, annot=True, cmap='coolwarm', center=0, 
                square=True, fmt='.2f', ax=axes[2,0])
    axes[2,0].set_title('Hardware Metrics Correlation Matrix', fontweight='bold')
    
    # 6. Performance Efficiency (Throughput per IPC)
    df['efficiency'] = df['throughput_ops_sec'] / df['ipc']
    sns.boxplot(data=df, x='operation', y='efficiency', hue='cache_type', ax=axes[2,1])
    axes[2,1].set_title('Performance Efficiency (Throughput/IPC)', fontweight='bold')
    axes[2,1].tick_params(axis='x', rotation=45)
    axes[2,1].set_ylabel('Efficiency (ops/sec per IPC)')
    
    plt.tight_layout()
    plt.savefig('/home/skarim/Code/haldendb_ex/haldendb/benchmark/plots/hardware_analysis.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    # Create a second figure for detailed hardware metrics by operation
    fig2, axes2 = plt.subplots(2, 2, figsize=(16, 12))
    
    # Hardware metrics by operation
    sns.boxplot(data=df, x='operation', y='ipc', hue='cache_type', ax=axes2[0,0])
    axes2[0,0].set_title('IPC by Operation and Cache Type', fontweight='bold')
    axes2[0,0].tick_params(axis='x', rotation=45)
    
    sns.boxplot(data=df, x='operation', y='cache_miss_rate', hue='cache_type', ax=axes2[0,1])
    axes2[0,1].set_title('Hardware Cache Miss Rate by Operation', fontweight='bold')
    axes2[0,1].tick_params(axis='x', rotation=45)
    
    sns.boxplot(data=df, x='operation', y='l1_miss_rate', hue='cache_type', ax=axes2[1,0])
    axes2[1,0].set_title('L1 Cache Miss Rate by Operation', fontweight='bold')
    axes2[1,0].tick_params(axis='x', rotation=45)
    
    sns.boxplot(data=df, x='operation', y='llc_miss_rate', hue='cache_type', ax=axes2[1,1])
    axes2[1,1].set_title('LLC Miss Rate by Operation', fontweight='bold')
    axes2[1,1].tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig('/home/skarim/Code/haldendb_ex/haldendb/benchmark/plots/hardware_by_operation.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    
    print("✓ Generated: hardware_analysis.png")
    print("✓ Generated: hardware_by_operation.png")

if __name__ == "__main__":
    main()