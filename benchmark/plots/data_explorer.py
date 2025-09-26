#!/usr/bin/env python3
"""
Data Explorer: Check the structure of vanilla and optimized CSV files
"""

import pandas as pd

def explore_data():
    # Load data
    vanilla_csv = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250924_171318/combined_benchmark_results_with_perf_20250924_220907.csv"
    optimized_csv = "/home/skarim/Code/haldendb_ex/haldendb_pvt/benchmark/build/cache_profiling_results_20250925_004057_default_configs_only/combined_benchmark_results_with_perf_20250925_151521.csv"
    
    print("VANILLA DATA STRUCTURE:")
    print("=" * 40)
    vanilla_df = pd.read_csv(vanilla_csv)
    print(f"Shape: {vanilla_df.shape}")
    print(f"Columns: {list(vanilla_df.columns)}")
    print("\nFirst few rows:")
    print(vanilla_df.head())
    print("\nUnique values in key columns:")
    for col in ['storage_type', 'cache_type', 'thread_count']:
        if col in vanilla_df.columns:
            print(f"{col}: {sorted(vanilla_df[col].unique())}")
    
    # Check for operation-related columns
    op_cols = [col for col in vanilla_df.columns if 'operation' in col.lower() or 'op' in col.lower()]
    print(f"Operation-related columns: {op_cols}")
    
    print("\n" + "="*60)
    print("OPTIMIZED DATA STRUCTURE:")
    print("=" * 40)
    optimized_df = pd.read_csv(optimized_csv)
    print(f"Shape: {optimized_df.shape}")
    print(f"Columns: {list(optimized_df.columns)}")
    print("\nFirst few rows:")
    print(optimized_df.head())
    print("\nUnique values in key columns:")
    for col in ['policy_name', 'config_name']:
        if col in optimized_df.columns:
            print(f"{col}: {sorted(optimized_df[col].unique())}")
    
    # Check for operation-related columns
    op_cols = [col for col in optimized_df.columns if 'operation' in col.lower() or 'op' in col.lower()]
    print(f"Operation-related columns: {op_cols}")

if __name__ == "__main__":
    explore_data()