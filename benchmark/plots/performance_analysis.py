#!/usr/bin/env python3
"""
Comprehensive Performance Analysis: Vanilla vs Optimized
Analyzes the performance differences across storage types, cache policies, and operations
"""

import pandas as pd
import numpy as np
import os

def load_vanilla_data(csv_path):
    """Load the vanilla benchmark data"""
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} records from vanilla CSV")
    
    # Replace SSARC with A2Q in vanilla data for consistency
    df['cache_type'] = df['cache_type'].replace('SSARC', 'A2Q')
    
    return df

def load_optimized_data(csv_path):
    """Load the optimized benchmark data and normalize column names"""
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

def calculate_throughput(df):
    """Calculate throughput in operations per second"""
    df = df.copy()
    # Throughput = record_count / (time_ns / 1e9) = record_count * 1e9 / time_ns
    df['throughput'] = df['record_count'] * 1e9 / df['time_ns']
    return df

def analyze_performance():
    """Comprehensive performance analysis"""
    
    # Load data
    vanilla_csv = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250924_171318/combined_benchmark_results_with_perf_20250924_220907.csv"
    optimized_csv = "/home/skarim/Code/haldendb_ex/haldendb_pvt/benchmark/build/cache_profiling_results_20250925_004057_default_configs_only/combined_benchmark_results_with_perf_20250925_151521.csv"
    
    vanilla_df = load_vanilla_data(vanilla_csv)
    optimized_df = load_optimized_data(optimized_csv)
    
    # Calculate throughput
    vanilla_df = calculate_throughput(vanilla_df)
    optimized_df = calculate_throughput(optimized_df)
    
    # Add variant labels
    vanilla_df['variant'] = 'Vanilla'
    optimized_df['variant'] = 'Optimized'
    
    # Combine data
    combined_df = pd.concat([vanilla_df, optimized_df], ignore_index=True)
    
    print("="*80)
    print("COMPREHENSIVE PERFORMANCE ANALYSIS: VANILLA vs OPTIMIZED")
    print("="*80)
    
    # 1. Overall Statistics
    print("\n1. OVERALL DATASET STATISTICS")
    print("-" * 40)
    
    storage_types = sorted(combined_df['storage_type'].unique())
    cache_types = sorted(combined_df['cache_type'].unique())
    operations = sorted(combined_df['operation'].unique())
    thread_counts = sorted(combined_df['thread_count'].unique())
    
    print(f"Storage Types: {storage_types}")
    print(f"Cache Policies: {cache_types}")
    print(f"Operations: {operations}")
    print(f"Thread Counts: {thread_counts}")
    
    # 2. Performance Summary by Storage Type
    print("\n2. PERFORMANCE SUMMARY BY STORAGE TYPE")
    print("-" * 50)
    
    for storage_type in storage_types:
        print(f"\n📁 {storage_type.upper()}")
        storage_data = combined_df[combined_df['storage_type'] == storage_type]
        
        # Calculate overall statistics
        vanilla_stats = storage_data[storage_data['variant'] == 'Vanilla']['throughput'].agg(['mean', 'min', 'max', 'std'])
        optimized_stats = storage_data[storage_data['variant'] == 'Optimized']['throughput'].agg(['mean', 'min', 'max', 'std'])
        
        overall_speedup = optimized_stats['mean'] / vanilla_stats['mean']
        
        print(f"  Vanilla   - Mean: {vanilla_stats['mean']/1e6:.2f}M ops/sec, Range: [{vanilla_stats['min']/1e6:.2f}M, {vanilla_stats['max']/1e6:.2f}M]")
        print(f"  Optimized - Mean: {optimized_stats['mean']/1e6:.2f}M ops/sec, Range: [{optimized_stats['min']/1e6:.2f}M, {optimized_stats['max']/1e6:.2f}M]")
        print(f"  📈 Overall Speedup: {overall_speedup:.2f}x")
    
    # 3. Detailed Analysis by Storage Type and Cache Policy
    print("\n3. DETAILED ANALYSIS BY STORAGE TYPE AND CACHE POLICY")
    print("-" * 60)
    
    for storage_type in storage_types:
        print(f"\n🏪 {storage_type.upper()} STORAGE")
        print("=" * 30)
        
        storage_data = combined_df[combined_df['storage_type'] == storage_type]
        
        for cache_type in cache_types:
            cache_data = storage_data[storage_data['cache_type'] == cache_type]
            if len(cache_data) == 0:
                continue
                
            print(f"\n  🔄 {cache_type} Cache Policy:")
            
            for thread_count in thread_counts:
                thread_data = cache_data[cache_data['thread_count'] == thread_count]
                if len(thread_data) == 0:
                    continue
                
                vanilla_data = thread_data[thread_data['variant'] == 'Vanilla']
                optimized_data = thread_data[thread_data['variant'] == 'Optimized']
                
                if len(vanilla_data) == 0 or len(optimized_data) == 0:
                    continue
                
                vanilla_mean = vanilla_data['throughput'].mean()
                optimized_mean = optimized_data['throughput'].mean()
                speedup = optimized_mean / vanilla_mean
                
                print(f"    🧵 {thread_count} Thread{'s' if thread_count > 1 else ''}:")
                print(f"      Vanilla: {vanilla_mean/1e6:.2f}M ops/sec")
                print(f"      Optimized: {optimized_mean/1e6:.2f}M ops/sec")
                print(f"      Speedup: {speedup:.2f}x {'✅' if speedup > 1.5 else '⚠️' if speedup > 1.0 else '❌'}")
    
    # 4. Operation-Level Analysis
    print("\n4. OPERATION-LEVEL PERFORMANCE ANALYSIS")
    print("-" * 50)
    
    for operation in operations:
        print(f"\n⚙️  {operation.upper()} OPERATION")
        print("=" * 30)
        
        op_data = combined_df[combined_df['operation'] == operation]
        
        for storage_type in storage_types:
            storage_op_data = op_data[op_data['storage_type'] == storage_type]
            if len(storage_op_data) == 0:
                continue
                
            vanilla_data = storage_op_data[storage_op_data['variant'] == 'Vanilla']
            optimized_data = storage_op_data[storage_op_data['variant'] == 'Optimized']
            
            if len(vanilla_data) == 0 or len(optimized_data) == 0:
                continue
            
            vanilla_stats = vanilla_data['throughput'].agg(['mean', 'min', 'max'])
            optimized_stats = optimized_data['throughput'].agg(['mean', 'min', 'max'])
            speedup = optimized_stats['mean'] / vanilla_stats['mean']
            
            print(f"  📁 {storage_type}:")
            print(f"    Vanilla   - Mean: {vanilla_stats['mean']/1e6:.2f}M, Range: [{vanilla_stats['min']/1e6:.2f}M, {vanilla_stats['max']/1e6:.2f}M]")
            print(f"    Optimized - Mean: {optimized_stats['mean']/1e6:.2f}M, Range: [{optimized_stats['min']/1e6:.2f}M, {optimized_stats['max']/1e6:.2f}M]")
            print(f"    Speedup: {speedup:.2f}x {'🚀' if speedup > 2.0 else '✅' if speedup > 1.5 else '⚠️' if speedup > 1.0 else '❌'}")
    
    # 5. Best and Worst Performers
    print("\n5. BEST AND WORST PERFORMING CONFIGURATIONS")
    print("-" * 55)
    
    # Calculate speedups for all configurations
    speedup_data = []
    
    for storage_type in storage_types:
        for cache_type in cache_types:
            for thread_count in thread_counts:
                for operation in operations:
                    config_data = combined_df[
                        (combined_df['storage_type'] == storage_type) &
                        (combined_df['cache_type'] == cache_type) &
                        (combined_df['thread_count'] == thread_count) &
                        (combined_df['operation'] == operation)
                    ]
                    
                    vanilla_data = config_data[config_data['variant'] == 'Vanilla']
                    optimized_data = config_data[config_data['variant'] == 'Optimized']
                    
                    if len(vanilla_data) > 0 and len(optimized_data) > 0:
                        vanilla_mean = vanilla_data['throughput'].mean()
                        optimized_mean = optimized_data['throughput'].mean()
                        speedup = optimized_mean / vanilla_mean
                        
                        speedup_data.append({
                            'storage_type': storage_type,
                            'cache_type': cache_type,
                            'thread_count': thread_count,
                            'operation': operation,
                            'vanilla_throughput': vanilla_mean,
                            'optimized_throughput': optimized_mean,
                            'speedup': speedup
                        })
    
    speedup_df = pd.DataFrame(speedup_data)
    
    # Top 10 best speedups
    print("\n🏆 TOP 10 BEST SPEEDUPS:")
    best_speedups = speedup_df.nlargest(10, 'speedup')
    for idx, row in best_speedups.iterrows():
        print(f"  {row['speedup']:.2f}x - {row['storage_type']}/{row['cache_type']}/{row['operation']}/{row['thread_count']}T")
        print(f"    ({row['vanilla_throughput']/1e6:.2f}M → {row['optimized_throughput']/1e6:.2f}M ops/sec)")
    
    # Bottom 10 worst speedups
    print("\n⚠️  BOTTOM 10 SPEEDUPS (Areas for Improvement):")
    worst_speedups = speedup_df.nsmallest(10, 'speedup')
    for idx, row in worst_speedups.iterrows():
        print(f"  {row['speedup']:.2f}x - {row['storage_type']}/{row['cache_type']}/{row['operation']}/{row['thread_count']}T")
        print(f"    ({row['vanilla_throughput']/1e6:.2f}M → {row['optimized_throughput']/1e6:.2f}M ops/sec)")
    
    # 6. Summary Statistics
    print("\n6. SUMMARY STATISTICS")
    print("-" * 30)
    
    total_configs = len(speedup_df)
    improved_configs = len(speedup_df[speedup_df['speedup'] > 1.0])
    significantly_improved = len(speedup_df[speedup_df['speedup'] > 1.5])
    degraded_configs = len(speedup_df[speedup_df['speedup'] < 1.0])
    
    print(f"Total Configurations Analyzed: {total_configs}")
    print(f"Improved Configurations: {improved_configs} ({improved_configs/total_configs*100:.1f}%)")
    print(f"Significantly Improved (>1.5x): {significantly_improved} ({significantly_improved/total_configs*100:.1f}%)")
    print(f"Degraded Configurations: {degraded_configs} ({degraded_configs/total_configs*100:.1f}%)")
    print(f"Average Speedup: {speedup_df['speedup'].mean():.2f}x")
    print(f"Median Speedup: {speedup_df['speedup'].median():.2f}x")
    print(f"Best Speedup: {speedup_df['speedup'].max():.2f}x")
    print(f"Worst Speedup: {speedup_df['speedup'].min():.2f}x")
    
    # 7. Recommendations
    print("\n7. OPTIMIZATION RECOMMENDATIONS")
    print("-" * 40)
    
    print("\n✅ STRENGTHS:")
    # Find operations with consistently good speedups
    op_speedups = speedup_df.groupby('operation')['speedup'].agg(['mean', 'min', 'max'])
    best_ops = op_speedups[op_speedups['mean'] > 1.5].sort_values('mean', ascending=False)
    
    for op in best_ops.index:
        stats = best_ops.loc[op]
        print(f"  • {op}: Average {stats['mean']:.2f}x speedup (range: {stats['min']:.2f}x - {stats['max']:.2f}x)")
    
    print("\n⚠️  AREAS FOR IMPROVEMENT:")
    # Find operations with poor speedups
    poor_ops = op_speedups[op_speedups['mean'] < 1.2].sort_values('mean')
    
    for op in poor_ops.index:
        stats = poor_ops.loc[op]
        print(f"  • {op}: Only {stats['mean']:.2f}x speedup (range: {stats['min']:.2f}x - {stats['max']:.2f}x)")
    
    print("\n🎯 FOCUS AREAS:")
    # Find storage/cache combinations that need attention
    combo_speedups = speedup_df.groupby(['storage_type', 'cache_type'])['speedup'].mean().sort_values()
    worst_combos = combo_speedups.head(3)
    
    for (storage, cache), speedup in worst_combos.items():
        print(f"  • {storage} + {cache}: {speedup:.2f}x average speedup")

if __name__ == "__main__":
    analyze_performance()