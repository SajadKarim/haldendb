#!/usr/bin/env python3
"""
Error Bar Analysis: Compare aggregation methods
Demonstrates why Option 1 Overlay has negative error bars
"""

import pandas as pd
import numpy as np
import os

def load_and_analyze_data():
    """Load data and compare error bar calculation methods"""
    
    # Use the same CSV paths as used in thread comparison
    vanilla_csv = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250924_171318/combined_benchmark_results_with_perf_20250924_220907.csv"
    optimized_csv = "/home/skarim/Code/haldendb_ex/haldendb_pvt/benchmark/build/cache_profiling_results_20250925_004057_default_configs_only/combined_benchmark_results_with_perf_20250925_151521.csv"
    
    # Load vanilla data
    vanilla_df = pd.read_csv(vanilla_csv)
    vanilla_df['cache_type'] = vanilla_df['cache_type'].replace('SSARC', 'A2Q')
    vanilla_df['throughput'] = vanilla_df['record_count'] * 1e9 / vanilla_df['time_ns']
    vanilla_df['variant'] = 'Vanilla'
    
    # Load optimized data
    optimized_df = pd.read_csv(optimized_csv)
    optimized_df = optimized_df.rename(columns={'policy_name': 'cache_type', 'time_us': 'time_ns'})
    optimized_df['time_ns'] = optimized_df['time_ns'] * 1000
    optimized_df['thread_count'] = optimized_df['config_name'].map({
        'non_concurrent_default': 1,
        'concurrent_default': 4
    })
    optimized_df = optimized_df.dropna(subset=['thread_count'])
    optimized_df['thread_count'] = optimized_df['thread_count'].astype(int)
    optimized_df['throughput'] = optimized_df['record_count'] * 1e9 / optimized_df['time_ns']
    optimized_df['variant'] = 'Optimized'
    
    # Combine data
    combined_df = pd.concat([vanilla_df, optimized_df], ignore_index=True)
    
    print("="*80)
    print("ERROR BAR ANALYSIS: Why Option 1 Overlay has negative error bars")
    print("="*80)
    
    # Focus on FileStorage + CLOCK (the problematic case)
    test_data = combined_df[
        (combined_df['storage_type'] == 'FileStorage') & 
        (combined_df['cache_type'] == 'CLOCK') &
        (combined_df['variant'] == 'Vanilla') &
        (combined_df['thread_count'] == 1)
    ]
    
    print(f"\nAnalyzing: FileStorage + CLOCK + Vanilla + 1T")
    print(f"Number of data points: {len(test_data)}")
    print(f"Operations included: {sorted(test_data['operation'].unique())}")
    
    # Method 1: Option 1 Overlay approach (aggregate all operations)
    print(f"\n📊 METHOD 1 (Option 1 Overlay): Aggregate ALL operations")
    print("-" * 60)
    all_throughput = test_data['throughput']
    mean_all = all_throughput.mean()
    std_all = all_throughput.std()
    
    print(f"Mean throughput: {mean_all/1e6:.2f}M ops/sec")
    print(f"Standard deviation: {std_all/1e6:.2f}M ops/sec")
    print(f"Error bar range: [{(mean_all-std_all)/1e6:.2f}M, {(mean_all+std_all)/1e6:.2f}M]")
    print(f"❌ Negative lower bound: {mean_all-std_all < 0}")
    
    # Show individual operation throughputs
    print(f"\nIndividual operation throughputs:")
    for operation in sorted(test_data['operation'].unique()):
        op_data = test_data[test_data['operation'] == operation]['throughput']
        if len(op_data) > 0:
            print(f"  {operation:15}: {op_data.mean()/1e6:8.2f}M ops/sec")
    
    # Method 2: Option 1 Extended approach (per operation)
    print(f"\n📊 METHOD 2 (Option 1 Extended): Per-operation calculation")
    print("-" * 60)
    
    for operation in sorted(test_data['operation'].unique()):
        op_data = test_data[test_data['operation'] == operation]['throughput']
        if len(op_data) > 0:
            mean_op = op_data.mean()
            std_op = op_data.std() if len(op_data) > 1 else 0
            print(f"{operation:15}: Mean={mean_op/1e6:6.2f}M, Std={std_op/1e6:6.2f}M, Range=[{(mean_op-std_op)/1e6:6.2f}M, {(mean_op+std_op)/1e6:6.2f}M]")
            if mean_op - std_op < 0:
                print(f"                ❌ Negative lower bound!")
            else:
                print(f"                ✅ Positive range")
    
    # Explain the variance
    print(f"\n🔍 VARIANCE ANALYSIS:")
    print("-" * 60)
    print(f"When aggregating all operations together:")
    print(f"• Different operations have vastly different throughputs")
    search_ops = test_data[test_data['operation'].str.contains('search')]
    non_search_ops = test_data[~test_data['operation'].str.contains('search')]
    print(f"• SEARCH operations: ~{search_ops['throughput'].mean()/1e6:.1f}M ops/sec")
    print(f"• INSERT/DELETE ops: ~{non_search_ops['throughput'].mean()/1e6:.1f}M ops/sec")
    print(f"• This creates HIGH variance across the combined dataset")
    print(f"• High variance → Large std → Error bars extend below zero")
    
    print(f"\n💡 SOLUTION:")
    print("-" * 60)
    print(f"Option 1 Extended calculates error bars per operation type separately")
    print(f"This gives more accurate error bars that represent actual measurement variance")
    print(f"Rather than artificial variance from mixing different operation types")

if __name__ == "__main__":
    load_and_analyze_data()