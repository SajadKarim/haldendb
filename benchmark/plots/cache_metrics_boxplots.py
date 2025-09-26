#!/usr/bin/env python3
"""
Cache Metrics Box Plots - 2x3 Layout
Shows cache metrics and performance data as box plots by cache policy.
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

def load_data():
    """Load the benchmark data."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, '..', 'build', 'cache_profiling_results_20250922_123326')
    csv_file = os.path.join(data_dir, 'combined_benchmark_results_with_perf_20250922_132611.csv')
    
    if not os.path.exists(csv_file):
        print(f"Data file not found: {csv_file}")
        return None
    
    print(f"Loading data from: {csv_file}")
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    
    return df

def prepare_data(df):
    """Prepare data for box plots."""
    # Filter for thread_count = 4 (as shown in the example file)
    df_filtered = df[df['thread_count'] == 4].copy()
    
    # Rename SSARC to A2Q for consistency with other plots
    df_filtered.loc[df_filtered['cache_type'] == 'SSARC', 'cache_type'] = 'A2Q'
    
    # Convert performance metrics to appropriate units
    df_filtered['cache_hits_M'] = df_filtered['cache_hits'] / 1e6
    df_filtered['cache_misses_M'] = df_filtered['cache_misses'] / 1e6
    df_filtered['evictions_M'] = df_filtered['evictions'] / 1e6
    df_filtered['dirty_evictions_M'] = df_filtered['dirty_evictions'] / 1e6
    df_filtered['instructions_B'] = df_filtered['perf_instructions'] / 1e9  # Billions
    
    return df_filtered

def create_boxplots(df, output_path):
    """Create 2x3 box plot layout using matplotlib."""
    # Set up the plot style
    plt.style.use('default')
    
    # Create figure with 2x3 subplots
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Define cache policies order for consistent coloring
    cache_policies = ['CLOCK', 'LRU', 'A2Q']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Blue, Orange, Green
    
    def create_single_boxplot(ax, metric_col, title, ylabel):
        """Helper function to create a single box plot."""
        data_by_policy = []
        labels = []
        for policy in cache_policies:
            policy_data = df[df['cache_type'] == policy][metric_col].values
            data_by_policy.append(policy_data)
            labels.append(policy)
        
        bp = ax.boxplot(data_by_policy, tick_labels=labels, patch_artist=True)
        
        # Color the boxes
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel('Cache Policy', fontsize=12)
        ax.set_ylabel(ylabel, fontsize=12)
        ax.grid(True, alpha=0.3)
    
    # 1. Cache Hits (top-left)
    create_single_boxplot(axes[0, 0], 'cache_hits_M', 'Cache Hits', 'Cache Hits (Millions)')
    
    # 2. Cache Misses (top-middle)
    create_single_boxplot(axes[0, 1], 'cache_misses_M', 'Cache Misses', 'Cache Misses (Millions)')
    
    # 3. Evictions (top-right)
    create_single_boxplot(axes[0, 2], 'evictions_M', 'Evictions', 'Evictions (Millions)')
    
    # 4. Dirty Evictions (bottom-left)
    create_single_boxplot(axes[1, 0], 'dirty_evictions_M', 'Dirty Evictions', 'Dirty Evictions (Millions)')
    
    # 5. Instructions (bottom-middle)
    create_single_boxplot(axes[1, 1], 'instructions_B', 'Instructions', 'Instructions (Billions)')
    
    # 6. User and System Time (bottom-right)
    ax6 = axes[1, 2]
    
    # Prepare data for user/system time comparison
    user_data = []
    sys_data = []
    for policy in cache_policies:
        policy_data = df[df['cache_type'] == policy]
        user_data.append(policy_data['perf_user_time'].values)
        sys_data.append(policy_data['perf_sys_time'].values)
    
    # Create positions for grouped box plots
    positions_user = [1, 4, 7]  # Positions for user time boxes
    positions_sys = [2, 5, 8]   # Positions for system time boxes
    
    # Create box plots for user and system time
    bp_user = ax6.boxplot(user_data, positions=positions_user, widths=0.6, patch_artist=True)
    bp_sys = ax6.boxplot(sys_data, positions=positions_sys, widths=0.6, patch_artist=True)
    
    # Color the boxes
    for patch in bp_user['boxes']:
        patch.set_facecolor('lightblue')
        patch.set_alpha(0.7)
    
    for patch in bp_sys['boxes']:
        patch.set_facecolor('lightcoral')
        patch.set_alpha(0.7)
    
    # Set labels and formatting
    ax6.set_title('User vs System Time', fontsize=14, fontweight='bold')
    ax6.set_xlabel('Cache Policy', fontsize=12)
    ax6.set_ylabel('Time (Seconds)', fontsize=12)
    ax6.set_xticks([1.5, 4.5, 7.5])
    ax6.set_xticklabels(cache_policies)
    ax6.grid(True, alpha=0.3)
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor='lightblue', alpha=0.7, label='User Time'),
                      Patch(facecolor='lightcoral', alpha=0.7, label='System Time')]
    ax6.legend(handles=legend_elements, title='Time Type', loc='upper right')
    
    # Adjust layout and save
    plt.tight_layout()
    plt.subplots_adjust(top=0.95, hspace=0.3, wspace=0.3)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"Cache metrics box plots saved to: {output_path}")
    
    return fig

def print_statistics(df):
    """Print summary statistics for each cache policy."""
    print("\n" + "="*80)
    print("CACHE METRICS STATISTICS BY POLICY (Thread Count = 4)")
    print("="*80)
    
    cache_policies = ['CLOCK', 'LRU', 'A2Q']
    metrics = [
        ('cache_hits_M', 'Cache Hits (M)'),
        ('cache_misses_M', 'Cache Misses (M)'),
        ('evictions_M', 'Evictions (M)'),
        ('dirty_evictions_M', 'Dirty Evictions (M)'),
        ('instructions_B', 'Instructions (B)'),
        ('perf_user_time', 'User Time (s)'),
        ('perf_sys_time', 'System Time (s)')
    ]
    
    for policy in cache_policies:
        policy_data = df[df['cache_type'] == policy]
        print(f"\n🔧 {policy} POLICY:")
        print("-" * 60)
        
        for metric, label in metrics:
            values = policy_data[metric]
            print(f"{label:<20}: Mean={values.mean():.2f}, Std={values.std():.2f}, "
                  f"Min={values.min():.2f}, Max={values.max():.2f}")
    
    # Compare policies
    print(f"\n🏆 POLICY COMPARISON:")
    print("-" * 60)
    
    for metric, label in metrics:
        print(f"\n{label}:")
        for policy in cache_policies:
            policy_data = df[df['cache_type'] == policy]
            mean_val = policy_data[metric].mean()
            print(f"  {policy}: {mean_val:.2f}")

def main():
    """Main function."""
    # Load data
    df = load_data()
    if df is None:
        return
    
    # Prepare data
    df_prepared = prepare_data(df)
    
    # Create output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'cache_metrics_boxplots.pdf')
    
    # Create box plots
    fig = create_boxplots(df_prepared, output_path)
    
    # Print statistics
    print_statistics(df_prepared)
    
    print(f"\n✅ Cache metrics box plots analysis complete!")
    print(f"📁 Plot saved as: {output_path}")

if __name__ == "__main__":
    main()