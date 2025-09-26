#!/usr/bin/env python3
"""
Cache Hit Ratio Heatmap

This script creates heatmaps to visualize cache hit ratios across different operations,
providing clean and intuitive insights for the performance patterns observed in spider plots.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def load_and_process_data(csv_path):
    """Load CSV data and process cache metrics."""
    print(f"Loading data from: {csv_path}")
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    
    # Calculate throughput for reference
    df['ops_per_sec'] = df['record_count'] / (df['time_ns'] / 1e9)
    
    # Calculate total cache accesses
    df['total_accesses'] = df['cache_hits'] + df['cache_misses']
    
    # Calculate hit ratio percentage
    df['hit_ratio_pct'] = (df['cache_hits'] / df['total_accesses']) * 100
    
    return df

def prepare_cumulative_metrics_data(df, thread_count):
    """Prepare cumulative cache metrics data averaged across runs."""
    # Filter for specific thread count
    thread_data = df[df['thread_count'] == thread_count].copy()
    
    if len(thread_data) == 0:
        print(f"Warning: No data found for thread_count = {thread_count}")
        return None
    
    cache_types = ['CLOCK', 'LRU', 'SSARC']
    metrics = ['cache_hits', 'cache_misses', 'evictions', 'dirty_evictions']
    
    # Prepare data structure for plotting
    cumulative_data = {}
    
    for cache_type in cache_types:
        cache_data = thread_data[thread_data['cache_type'] == cache_type]
        
        if len(cache_data) == 0:
            cumulative_data[cache_type] = [0, 0, 0, 0]
            continue
        
        # Calculate cumulative totals for each run, then average across runs
        run_totals = []
        
        # Group by run_id to get totals per run
        for run_id in cache_data['run_id'].unique():
            run_data = cache_data[cache_data['run_id'] == run_id]
            
            # Sum across all operations for this run
            run_total = [
                run_data['cache_hits'].sum(),
                run_data['cache_misses'].sum(), 
                run_data['evictions'].sum(),
                run_data['dirty_evictions'].sum()
            ]
            run_totals.append(run_total)
        
        # Average across all runs
        if run_totals:
            avg_totals = np.mean(run_totals, axis=0)
            cumulative_data[cache_type] = avg_totals.tolist()
        else:
            cumulative_data[cache_type] = [0, 0, 0, 0]
    
    return cumulative_data, metrics

def create_cumulative_metrics_heatmap(cumulative_data_1, cumulative_data_4, metrics, output_path):
    """Create heatmap for cumulative cache metrics with different scales per metric."""
    
    # Set up the figure with 2 subplots (1 for each thread count)
    fig, axes = plt.subplots(1, 2, figsize=(12, 6))
    fig.suptitle('Cumulative Cache Metrics Heatmap (Averaged Across Runs)', fontsize=16, fontweight='bold', y=0.95)
    
    cache_types = ['CLOCK', 'LRU', 'SSARC']
    metric_labels = ['Cache Hits', 'Cache Misses', 'Evictions', 'Dirty Evictions']
    
    # Prepare data for heatmaps
    def prepare_heatmap_data(cumulative_data):
        if not cumulative_data:
            return np.zeros((len(cache_types), len(metrics)))
        
        heatmap_data = []
        for cache_type in cache_types:
            if cache_type in cumulative_data:
                heatmap_data.append(cumulative_data[cache_type])
            else:
                heatmap_data.append([0] * len(metrics))
        
        return np.array(heatmap_data)
    
    # Create heatmap data
    heatmap_data_1 = prepare_heatmap_data(cumulative_data_1)
    heatmap_data_4 = prepare_heatmap_data(cumulative_data_4)
    
    # Normalize data by columns (metrics) to use different scales with proper best/worst logic
    def normalize_by_columns(data):
        normalized_data = np.zeros_like(data)
        
        # Define which metrics are "higher is better" vs "lower is better"
        # metrics = ['cache_hits', 'cache_misses', 'evictions', 'dirty_evictions']
        higher_is_better = [0]  # Index 0: cache_hits - higher is better
        lower_is_better = [1, 2, 3]  # Indices 1,2,3: misses, evictions, dirty_evictions - lower is better
        
        for j in range(data.shape[1]):  # For each metric column
            col_data = data[:, j]
            if col_data.max() > col_data.min():
                if j in higher_is_better:
                    # For cache hits: higher values should be white (0), lower values red (1)
                    normalized_data[:, j] = 1 - (col_data - col_data.min()) / (col_data.max() - col_data.min())
                else:
                    # For misses/evictions: lower values should be white (0), higher values red (1)
                    normalized_data[:, j] = (col_data - col_data.min()) / (col_data.max() - col_data.min())
            else:
                normalized_data[:, j] = 0
        return normalized_data
    
    # Normalize data for consistent color scaling across different metric ranges
    norm_data_1 = normalize_by_columns(heatmap_data_1)
    norm_data_4 = normalize_by_columns(heatmap_data_4)
    
    # Plot for Thread Count = 1
    ax1 = axes[0]
    im1 = ax1.imshow(norm_data_1, cmap='Greens', aspect='auto', vmin=0, vmax=1)
    
    # Add text annotations with actual values
    for i in range(len(cache_types)):
        for j in range(len(metrics)):
            value = heatmap_data_1[i, j]
            # Format large numbers with appropriate units
            if value >= 1e6:
                display_value = f'{value/1e6:.1f}M'
            elif value >= 1e3:
                display_value = f'{value/1e3:.0f}K'
            else:
                display_value = f'{value:.0f}'
            
            # Choose text color based on normalized value (white background = black text, green background = white text)
            color = 'black' if norm_data_1[i, j] < 0.5 else 'white'
            ax1.text(j, i, display_value, ha='center', va='center', 
                    fontsize=9, fontweight='bold', color=color)
    
    ax1.set_title('Thread Count = 1', fontsize=14, fontweight='bold')
    ax1.set_xticks(range(len(metrics)))
    ax1.set_xticklabels(metric_labels, rotation=45, ha='right')
    ax1.set_yticks(range(len(cache_types)))
    ax1.set_yticklabels(cache_types)
    ax1.set_xlabel('Cache Metrics', fontsize=12)
    ax1.set_ylabel('Cache Types', fontsize=12)
    
    # Plot for Thread Count = 4
    ax2 = axes[1]
    im2 = ax2.imshow(norm_data_4, cmap='Greens', aspect='auto', vmin=0, vmax=1)
    
    # Add text annotations with actual values
    for i in range(len(cache_types)):
        for j in range(len(metrics)):
            value = heatmap_data_4[i, j]
            # Format large numbers with appropriate units
            if value >= 1e6:
                display_value = f'{value/1e6:.1f}M'
            elif value >= 1e3:
                display_value = f'{value/1e3:.0f}K'
            else:
                display_value = f'{value:.0f}'
            
            # Choose text color based on normalized value (white background = black text, green background = white text)
            color = 'black' if norm_data_4[i, j] < 0.5 else 'white'
            ax2.text(j, i, display_value, ha='center', va='center', 
                    fontsize=9, fontweight='bold', color=color)
    
    ax2.set_title('Thread Count = 4', fontsize=14, fontweight='bold')
    ax2.set_xticks(range(len(metrics)))
    ax2.set_xticklabels(metric_labels, rotation=45, ha='right')
    ax2.set_yticks(range(len(cache_types)))
    ax2.set_yticklabels(cache_types)
    ax2.set_xlabel('Cache Metrics', fontsize=12)
    ax2.set_ylabel('Cache Types', fontsize=12)
    
    # Add colorbar
    cbar = fig.colorbar(im2, ax=axes, orientation='horizontal', 
                       fraction=0.05, pad=0.15, aspect=30)
    cbar.set_label('Performance Quality (White = Best, Green = Worst)', fontsize=12, fontweight='bold')
    cbar.ax.tick_params(labelsize=10)
    
    # Add explanation text
    fig.text(0.5, 0.02, 'Each metric uses independent scaling | White = Best performance, Green = Worst performance | Numbers show actual values', 
             ha='center', fontsize=10, style='italic')
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.88, bottom=0.25)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Cumulative cache metrics heatmap saved to: {output_path}")
    
    return fig

def print_cumulative_metrics_statistics(cumulative_data_1, cumulative_data_4, metrics):
    """Print detailed cumulative cache metrics statistics."""
    print("\n" + "="*80)
    print("CUMULATIVE CACHE METRICS ANALYSIS (AVERAGED ACROSS RUNS)")
    print("="*80)
    
    metric_labels = ['Cache Hits', 'Cache Misses', 'Evictions', 'Dirty Evictions']
    cache_types = ['CLOCK', 'LRU', 'SSARC']
    
    for thread_count, cumulative_data in [("1", cumulative_data_1), ("4", cumulative_data_4)]:
        if not cumulative_data:
            continue
            
        print(f"\n🧵 THREAD COUNT = {thread_count}")
        print("-" * 80)
        
        # Print header
        print(f"{'Cache Type':<10} {'Hits':<12} {'Misses':<12} {'Evictions':<12} {'Dirty Evict':<12} {'Hit Ratio':<10}")
        print("-" * 80)
        
        # Print metrics for each cache type
        for cache_type in cache_types:
            if cache_type in cumulative_data:
                data = cumulative_data[cache_type]
                hits, misses, evictions, dirty_evictions = data
                
                # Calculate hit ratio
                total_accesses = hits + misses
                hit_ratio = (hits / total_accesses * 100) if total_accesses > 0 else 0
                
                # Format large numbers
                def format_number(num):
                    if num >= 1e6:
                        return f"{num/1e6:.1f}M"
                    elif num >= 1e3:
                        return f"{num/1e3:.0f}K"
                    else:
                        return f"{num:.0f}"
                
                print(f"{cache_type:<10} {format_number(hits):<12} {format_number(misses):<12} "
                      f"{format_number(evictions):<12} {format_number(dirty_evictions):<12} {hit_ratio:<10.1f}%")
        
        # Compare cache types
        print(f"\n🏆 CACHE EFFICIENCY COMPARISON (Thread Count = {thread_count}):")
        print("-" * 60)
        
        # Find best performers for each metric
        best_hits = max(cumulative_data.items(), key=lambda x: x[1][0])
        best_hit_ratio = max(cumulative_data.items(), key=lambda x: x[1][0]/(x[1][0]+x[1][1]) if (x[1][0]+x[1][1]) > 0 else 0)
        least_evictions = min(cumulative_data.items(), key=lambda x: x[1][2])
        least_dirty_evictions = min(cumulative_data.items(), key=lambda x: x[1][3])
        
        print(f"  Most Cache Hits: {best_hits[0]} ({best_hits[1][0]/1e6:.1f}M)")
        
        hit_ratio_val = best_hit_ratio[1][0]/(best_hit_ratio[1][0]+best_hit_ratio[1][1]) * 100
        print(f"  Best Hit Ratio: {best_hit_ratio[0]} ({hit_ratio_val:.1f}%)")
        
        print(f"  Fewest Evictions: {least_evictions[0]} ({least_evictions[1][2]/1e6:.1f}M)")
        print(f"  Fewest Dirty Evictions: {least_dirty_evictions[0]} ({least_dirty_evictions[1][3]/1e3:.0f}K)")
        
        # Performance insights
        print(f"\n💡 INSIGHTS:")
        for cache_type in cache_types:
            if cache_type in cumulative_data:
                data = cumulative_data[cache_type]
                hits, misses, evictions, dirty_evictions = data
                hit_ratio = (hits / (hits + misses) * 100) if (hits + misses) > 0 else 0
                
                insights = []
                if hit_ratio > 80:
                    insights.append("High hit ratio")
                elif hit_ratio < 70:
                    insights.append("Low hit ratio")
                
                if evictions < 2e6:
                    insights.append("Low eviction pressure")
                elif evictions > 4e6:
                    insights.append("High eviction pressure")
                
                if dirty_evictions > 0:
                    insights.append(f"Dirty evictions: {dirty_evictions/1e3:.0f}K")
                
                if insights:
                    print(f"  {cache_type}: {', '.join(insights)}")

def main():
    # File paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250922_123326/combined_benchmark_results_with_perf_20250922_132611.csv"
    output_path = os.path.join(script_dir, 'cache_metrics_stacked_bars.png')
    
    try:
        # Load and process data
        df = load_and_process_data(csv_path)
        
        # Prepare cumulative cache metrics data for both thread counts
        cumulative_data_1, metrics = prepare_cumulative_metrics_data(df, 1)
        cumulative_data_4, _ = prepare_cumulative_metrics_data(df, 4)
        
        if not cumulative_data_1 and not cumulative_data_4:
            print("Error: No valid data found for cumulative cache metrics analysis")
            return
        
        # Create cumulative metrics heatmap
        fig = create_cumulative_metrics_heatmap(cumulative_data_1, cumulative_data_4, metrics, output_path)
        
        # Print statistics
        print_cumulative_metrics_statistics(cumulative_data_1, cumulative_data_4, metrics)
        
        print(f"\n✅ Cache metrics analysis complete!")
        print(f"📁 Plot saved as: {output_path}")
        
    except Exception as e:
        print(f"Error creating cache metrics visualization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()