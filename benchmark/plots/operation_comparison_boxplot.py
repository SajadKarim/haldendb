#!/usr/bin/env python3
"""
Generate box plots comparing operations with different cache types for different thread counts
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os

def load_data():
    """Load the benchmark data"""
    csv_path = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250922_123326/combined_benchmark_results_with_perf_20250922_132611.csv"
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} records from CSV")
    return df

def calculate_throughput(df):
    """Calculate throughput from record_count and time_ns"""
    # Throughput = record_count / (time_ns / 1e9) = record_count * 1e9 / time_ns
    df['calculated_throughput'] = df['record_count'] * 1e9 / df['time_ns']
    return df

def create_operation_comparison_boxplot():
    """Create box plots comparing operations with different cache types for different thread counts"""
    
    # Load and prepare data
    df = load_data()
    df = calculate_throughput(df)
    
    # Filter for thread counts 1 and 4
    df_filtered = df[df['thread_count'].isin([1, 4])].copy()
    
    print(f"Data after filtering for thread counts 1 and 4: {len(df_filtered)} records")
    print(f"Thread count distribution:")
    print(df_filtered['thread_count'].value_counts().sort_index())
    print(f"Operation distribution:")
    print(df_filtered['operation'].value_counts())
    print(f"Cache type distribution:")
    print(df_filtered['cache_type'].value_counts())
    
    # Get unique operations and cache types
    operations = sorted(df_filtered['operation'].unique())
    cache_types = sorted(df_filtered['cache_type'].unique())
    print(f"Operations: {operations}")
    print(f"Cache types: {cache_types}")
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    
    # Prepare data for box plots
    thread_1_data = df_filtered[df_filtered['thread_count'] == 1]
    thread_4_data = df_filtered[df_filtered['thread_count'] == 4]
    
    print(f"Thread 1 data: {len(thread_1_data)} records")
    print(f"Thread 4 data: {len(thread_4_data)} records")
    
    # Calculate y-axis limits to use same scale
    all_throughput = df_filtered['calculated_throughput'].values
    y_min = 0
    y_max = np.max(all_throughput) * 1.1
    
    print(f"Y-axis range: {y_min:.0f} to {y_max:.0f} ops/sec")
    
    # Colors for each cache type
    colors = {'CLOCK': '#2E86AB', 'LRU': '#A23B72', 'SSARC': '#F18F01'}
    
    def plot_operations_by_cache(ax, data, title, thread_count):
        """Plot operations grouped by cache type"""
        
        # Prepare data for grouped box plots
        all_data = []
        all_labels = []
        all_colors = []
        positions = []
        
        pos = 1
        group_positions = []
        group_labels = []
        
        for i, operation in enumerate(operations):
            op_data = data[data['operation'] == operation]
            
            if len(op_data) == 0:
                continue
                
            group_start = pos
            cache_data_for_op = []
            
            for j, cache_type in enumerate(cache_types):
                cache_op_data = op_data[op_data['cache_type'] == cache_type]['calculated_throughput']
                
                if len(cache_op_data) > 0:
                    all_data.append(cache_op_data.values)
                    all_labels.append(f"{operation}\n{cache_type}")
                    all_colors.append(colors.get(cache_type, '#666666'))
                    positions.append(pos)
                    cache_data_for_op.append(cache_op_data.values)
                    pos += 1
                else:
                    # Add empty data to maintain structure
                    all_data.append([])
                    all_labels.append(f"{operation}\n{cache_type}")
                    all_colors.append(colors.get(cache_type, '#666666'))
                    positions.append(pos)
                    cache_data_for_op.append([])
                    pos += 1
            
            # Calculate group center position
            group_center = (group_start + pos - 1) / 2
            group_positions.append(group_center)
            group_labels.append(operation.replace('search_', ''))
            
            # Add spacing between operation groups
            pos += 1
        
        # Create box plots
        if all_data:
            # Filter out empty data for plotting
            plot_data = [data for data in all_data if len(data) > 0]
            plot_positions = [pos for i, pos in enumerate(positions) if len(all_data[i]) > 0]
            plot_colors = [color for i, color in enumerate(all_colors) if len(all_data[i]) > 0]
            
            if plot_data:
                bp = ax.boxplot(plot_data, positions=plot_positions, patch_artist=True, 
                               showmeans=True, meanline=True, widths=0.6)
                
                # Color the boxes
                for patch, color in zip(bp['boxes'], plot_colors):
                    patch.set_facecolor(color)
                    patch.set_alpha(0.7)
                
                # Style the plot
                for element in ['whiskers', 'fliers', 'medians', 'caps']:
                    plt.setp(bp[element], color='black')
                plt.setp(bp['means'], color='red', linewidth=2)
        
        # Set labels and formatting
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Operation Type', fontsize=12)
        ax.set_ylabel('Operations per Second', fontsize=12)
        ax.set_ylim(y_min, y_max)
        ax.grid(True, alpha=0.3)
        
        # Set x-axis ticks to show operation names
        if group_positions:
            ax.set_xticks(group_positions)
            ax.set_xticklabels(group_labels, rotation=45, ha='right')
        
        ax.tick_params(axis='y', labelsize=10)
        ax.tick_params(axis='x', labelsize=10)
        
        # Add cache type indicators
        if positions:
            # Add subtle vertical lines to separate operation groups
            for i in range(len(operations) - 1):
                if i < len(group_positions) - 1:
                    sep_pos = (group_positions[i] + group_positions[i + 1]) / 2
                    ax.axvline(x=sep_pos, color='gray', linestyle='--', alpha=0.3)
    
    # Plot 1: Thread count = 1
    plot_operations_by_cache(ax1, thread_1_data, 
                           'Operation Performance by Cache Type\n(Thread Count = 1)', 1)
    
    # Plot 2: Thread count = 4
    plot_operations_by_cache(ax2, thread_4_data, 
                           'Operation Performance by Cache Type\n(Thread Count = 4)', 4)
    
    # Add overall title
    fig.suptitle('Operation Performance Comparison by Cache Type and Thread Count', 
                 fontsize=16, fontweight='bold', y=0.95)
    
    # Add legend
    legend_elements = [plt.Rectangle((0,0),1,1, facecolor=colors[cache], alpha=0.7, label=cache) 
                      for cache in cache_types if cache in colors]
    fig.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 0.02), 
               ncol=len(cache_types), fontsize=12)
    
    # Adjust layout
    plt.tight_layout()
    plt.subplots_adjust(top=0.88, bottom=0.15)
    
    # Save the plot
    output_path = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/plots/operation_comparison_boxplot.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Plot saved to: {output_path}")
    
    # Print summary statistics
    print("\n=== SUMMARY STATISTICS BY OPERATION AND CACHE TYPE ===")
    
    for thread_count in [1, 4]:
        print(f"\n{'='*50}")
        print(f"THREAD COUNT = {thread_count}")
        print(f"{'='*50}")
        thread_data = df_filtered[df_filtered['thread_count'] == thread_count]
        
        for operation in operations:
            print(f"\n{operation.upper()}:")
            op_data = thread_data[thread_data['operation'] == operation]
            
            if len(op_data) == 0:
                print("  No data available")
                continue
            
            for cache_type in cache_types:
                cache_data = op_data[op_data['cache_type'] == cache_type]['calculated_throughput']
                if len(cache_data) > 0:
                    print(f"  {cache_type}:")
                    print(f"    Count: {len(cache_data)}")
                    print(f"    Mean:  {cache_data.mean():.0f} ops/sec")
                    print(f"    Median: {cache_data.median():.0f} ops/sec")
                    print(f"    Std:   {cache_data.std():.0f} ops/sec")
                    print(f"    Min:   {cache_data.min():.0f} ops/sec")
                    print(f"    Max:   {cache_data.max():.0f} ops/sec")
    
    plt.close()

if __name__ == "__main__":
    try:
        create_operation_comparison_boxplot()
        print("Operation comparison box plot generated successfully!")
    except Exception as e:
        print(f"Error generating plot: {e}")
        import traceback
        traceback.print_exc()