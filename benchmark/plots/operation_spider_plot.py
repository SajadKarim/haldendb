#!/usr/bin/env python3
"""
Spider/Radar Plot for Cache Operation Performance Comparison

This script creates spider plots to visualize cache performance across different operations,
providing an intuitive way to see the "performance fingerprint" of each cache algorithm.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import pi
import os

def load_and_process_data(csv_path):
    """Load CSV data and calculate throughput."""
    print(f"Loading data from: {csv_path}")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    
    # Calculate throughput (ops/sec) from record_count and time_ns
    df['ops_per_sec'] = df['record_count'] / (df['time_ns'] / 1e9)
    
    return df

def prepare_spider_data(df, thread_count):
    """Prepare data for spider plot for a specific thread count."""
    # Filter for specific thread count
    thread_data = df[df['thread_count'] == thread_count].copy()
    
    if len(thread_data) == 0:
        print(f"Warning: No data found for thread_count = {thread_count}")
        return None
    
    # Replace SSARC with A2Q in the data (do this early)
    thread_data['cache_type'] = thread_data['cache_type'].replace('SSARC', 'A2Q')
    
    # Define operation order for consistent spider plot axes (original names for data lookup)
    operations_data = ['delete', 'insert', 'search_random', 'search_sequential', 'search_uniform', 'search_zipfian']
    # Display names for the plot (two lines for search operations)
    operations_display = ['delete', 'insert', 'search\n(random)', 'search\n(sequential)', 'search\n(uniform)', 'search\n(zipfian)']
    cache_types = ['CLOCK', 'LRU', 'A2Q']
    
    # Calculate mean performance for each cache type and operation
    spider_data = {}
    
    for cache_type in cache_types:
        cache_data = thread_data[thread_data['cache_type'] == cache_type]
        performance = []
        
        for operation in operations_data:
            op_data = cache_data[cache_data['operation'] == operation]['ops_per_sec']
            if len(op_data) > 0:
                mean_perf = op_data.mean()
                performance.append(mean_perf)
            else:
                performance.append(0)
        
        spider_data[cache_type] = performance
    
    return spider_data, operations_display

def create_spider_plot(spider_data_1, spider_data_4, operations, output_path):
    """Create spider plot comparing cache performance."""
    
    # Set up the figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), subplot_kw=dict(projection='polar'))
    
    # Number of variables (operations)
    N = len(operations)
    
    # Compute angle for each axis
    angles = [n / float(N) * 2 * pi for n in range(N)]
    angles += angles[:1]  # Complete the circle
    
    # Colors for each cache type (A2Q instead of SSARC)
    colors = {'CLOCK': '#1f77b4', 'LRU': '#9467bd', 'A2Q': '#ff7f0e'}
    
    # Find max value for consistent scaling
    all_values = []
    if spider_data_1:
        for cache_type in spider_data_1:
            all_values.extend(spider_data_1[cache_type])
    if spider_data_4:
        for cache_type in spider_data_4:
            all_values.extend(spider_data_4[cache_type])
    
    max_value = max(all_values) if all_values else 1000000
    
    # Plot for Thread Count = 1
    if spider_data_1:
        ax1.set_title('Thread Count = 1', size=16, fontweight='bold', pad=20)
        
        for cache_type in ['CLOCK', 'LRU', 'A2Q']:
            if cache_type in spider_data_1:
                values = spider_data_1[cache_type]
                values += values[:1]  # Complete the circle
                
                ax1.plot(angles, values, 'o-', linewidth=2, label=cache_type, 
                        color=colors[cache_type], markersize=6)
                ax1.fill(angles, values, alpha=0.15, color=colors[cache_type])
        
        # Customize the plot
        ax1.set_xticks(angles[:-1])
        ax1.set_xticklabels(operations, fontsize=10)
        ax1.set_ylim(0, max_value)
        ax1.grid(True, alpha=0.3)
        # No legend on first subplot
    
    # Plot for Thread Count = 4
    if spider_data_4:
        ax2.set_title('Thread Count = 4', size=16, fontweight='bold', pad=20)
        
        for cache_type in ['CLOCK', 'LRU', 'A2Q']:
            if cache_type in spider_data_4:
                values = spider_data_4[cache_type]
                values += values[:1]  # Complete the circle
                
                ax2.plot(angles, values, 'o-', linewidth=2, label=cache_type, 
                        color=colors[cache_type], markersize=6)
                ax2.fill(angles, values, alpha=0.15, color=colors[cache_type])
        
        # Customize the plot
        ax2.set_xticks(angles[:-1])
        ax2.set_xticklabels(operations, fontsize=10)
        ax2.set_ylim(0, max_value)
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
    
    # Remove main title (as requested)
    
    # Add performance scale annotation
    fig.text(0.5, 0.02, f'Radial Scale: 0 to {max_value/1e6:.1f}M ops/sec', 
             ha='center', fontsize=12, style='italic')
    
    plt.tight_layout()
    plt.savefig(output_path, bbox_inches='tight', facecolor='white')
    print(f"Spider plot saved to: {output_path}")
    
    return fig

def print_spider_statistics(spider_data_1, spider_data_4, operations):
    """Print detailed statistics for the spider plot data."""
    print("\n" + "="*80)
    print("SPIDER PLOT PERFORMANCE STATISTICS")
    print("="*80)
    
    for thread_count, spider_data in [("1", spider_data_1), ("4", spider_data_4)]:
        if not spider_data:
            continue
            
        print(f"\n🧵 THREAD COUNT = {thread_count}")
        print("-" * 50)
        
        # Print performance for each cache type
        for cache_type in ['CLOCK', 'LRU', 'A2Q']:
            if cache_type in spider_data:
                print(f"\n📊 {cache_type} Cache Performance:")
                values = spider_data[cache_type]
                
                for i, operation in enumerate(operations):
                    ops_per_sec = values[i]
                    print(f"  {operation:18}: {ops_per_sec:>10,.0f} ops/sec")
                
                # Calculate statistics
                avg_perf = np.mean(values)
                max_perf = max(values)
                min_perf = min(values)
                std_perf = np.std(values)
                
                print(f"  {'Average':18}: {avg_perf:>10,.0f} ops/sec")
                print(f"  {'Max':18}: {max_perf:>10,.0f} ops/sec")
                print(f"  {'Min':18}: {min_perf:>10,.0f} ops/sec")
                print(f"  {'Std Dev':18}: {std_perf:>10,.0f} ops/sec")
                print(f"  {'Range Ratio':18}: {max_perf/min_perf:>10.1f}x")
        
        # Compare cache types
        print(f"\n🏆 CACHE TYPE COMPARISON (Thread Count = {thread_count}):")
        print("-" * 50)
        
        for i, operation in enumerate(operations):
            print(f"\n{operation}:")
            op_results = []
            for cache_type in ['CLOCK', 'LRU', 'A2Q']:
                if cache_type in spider_data:
                    perf = spider_data[cache_type][i]
                    op_results.append((cache_type, perf))
            
            # Sort by performance
            op_results.sort(key=lambda x: x[1], reverse=True)
            
            for rank, (cache_type, perf) in enumerate(op_results, 1):
                print(f"  {rank}. {cache_type:6}: {perf:>10,.0f} ops/sec")

def main():
    # File paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250922_123326/combined_benchmark_results_with_perf_20250922_132611.csv"
    output_path = os.path.join(script_dir, 'operation_spider_plot.pdf')
    
    try:
        # Load and process data
        df = load_and_process_data(csv_path)
        
        # Prepare spider data for both thread counts
        spider_data_1, operations = prepare_spider_data(df, 1)
        spider_data_4, _ = prepare_spider_data(df, 4)
        
        if not spider_data_1 and not spider_data_4:
            print("Error: No valid data found for spider plot")
            return
        
        # Create spider plot
        fig = create_spider_plot(spider_data_1, spider_data_4, operations, output_path)
        
        # Print statistics
        print_spider_statistics(spider_data_1, spider_data_4, operations)
        
        print(f"\n✅ Spider plot analysis complete!")
        print(f"📁 Plot saved as: {output_path}")
        
    except Exception as e:
        print(f"Error creating spider plot: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()