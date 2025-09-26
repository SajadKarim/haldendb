#!/usr/bin/env python3
"""
Cache Performance Differences: Vanilla vs Optimized
Shows absolute and relative differences between vanilla and optimized variants
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import sys
import argparse
import seaborn as sns

def load_vanilla_data(csv_path):
    """Load the vanilla benchmark data"""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} records from vanilla CSV")
    
    # Replace SSARC with A2Q in vanilla data for consistency
    df['cache_type'] = df['cache_type'].replace('SSARC', 'A2Q')
    
    return df

def load_optimized_data(csv_path):
    """Load the optimized benchmark data and normalize column names"""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
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

def calculate_differences(vanilla_df, optimized_df):
    """Calculate absolute and relative differences between vanilla and optimized"""
    
    # Add variant labels
    vanilla_df['variant'] = 'Vanilla'
    optimized_df['variant'] = 'Optimized'
    
    # Combine data
    combined_df = pd.concat([vanilla_df, optimized_df], ignore_index=True)
    
    # Get unique storage types and rename them
    storage_type_mapping = {
        'FileStorage': 'SSD NVMe',
        'PMemStorage': 'NVM',
        'VolatileStorage': 'NVDIMM'
    }
    combined_df['storage_type'] = combined_df['storage_type'].map(storage_type_mapping)
    
    # Define metrics and their properties
    metrics_config = {
        'cache_hits': {'title': 'Cache Hits', 'unit': 'M', 'scale': 1e6, 'higher_better': True},
        'cache_misses': {'title': 'Cache Misses', 'unit': 'M', 'scale': 1e6, 'higher_better': False},
        'perf_instructions': {'title': 'Instructions', 'unit': 'B', 'scale': 1e9, 'higher_better': False},
        'perf_user_time': {'title': 'User Time', 'unit': 's', 'scale': 1, 'higher_better': False},
        'perf_sys_time': {'title': 'System Time', 'unit': 's', 'scale': 1, 'higher_better': False}
    }
    
    # Calculate differences
    differences = []
    
    for storage_type in ['NVDIMM', 'NVM', 'SSD NVMe']:
        for thread_count in sorted(combined_df['thread_count'].unique()):
            for cache_type in sorted(combined_df['cache_type'].unique()):
                
                # Get vanilla and optimized data
                vanilla_data = combined_df[
                    (combined_df['storage_type'] == storage_type) &
                    (combined_df['thread_count'] == thread_count) &
                    (combined_df['cache_type'] == cache_type) &
                    (combined_df['variant'] == 'Vanilla')
                ]
                
                optimized_data = combined_df[
                    (combined_df['storage_type'] == storage_type) &
                    (combined_df['thread_count'] == thread_count) &
                    (combined_df['cache_type'] == cache_type) &
                    (combined_df['variant'] == 'Optimized')
                ]
                
                if len(vanilla_data) > 0 and len(optimized_data) > 0:
                    row = {
                        'Storage': storage_type,
                        'Threads': thread_count,
                        'Cache': cache_type,
                        'Config': f'{cache_type}_{storage_type}_{thread_count}T'
                    }
                    
                    for metric, config in metrics_config.items():
                        vanilla_mean = vanilla_data[metric].mean()
                        optimized_mean = optimized_data[metric].mean()
                        
                        # Absolute difference
                        abs_diff = optimized_mean - vanilla_mean
                        row[f'{metric}_abs_diff'] = abs_diff / config['scale']
                        
                        # Relative difference (percentage)
                        if vanilla_mean > 0:
                            rel_diff = (optimized_mean - vanilla_mean) / vanilla_mean * 100
                            row[f'{metric}_rel_diff'] = rel_diff
                        else:
                            row[f'{metric}_rel_diff'] = 0
                        
                        # Store raw values for reference
                        row[f'{metric}_vanilla'] = vanilla_mean / config['scale']
                        row[f'{metric}_optimized'] = optimized_mean / config['scale']
                    
                    differences.append(row)
    
    return pd.DataFrame(differences), metrics_config

def create_difference_plots(differences_df, metrics_config, output_path):
    """Create plots showing absolute and relative differences"""
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, len(metrics_config), figsize=(25, 12))
    
    storage_colors = {'NVDIMM': '#FF6B6B', 'NVM': '#4ECDC4', 'SSD NVMe': '#45B7D1'}
    
    for metric_idx, (metric, config) in enumerate(metrics_config.items()):
        
        # Absolute differences (top row)
        ax_abs = axes[0, metric_idx]
        
        # Group data by storage type
        for storage_type in ['NVDIMM', 'NVM', 'SSD NVMe']:
            storage_data = differences_df[differences_df['Storage'] == storage_type]
            
            if len(storage_data) == 0:
                continue
            
            # Create x positions for each cache type and thread count
            x_labels = []
            x_positions = []
            abs_values = []
            
            pos = 0
            for cache_type in sorted(storage_data['Cache'].unique()):
                for thread_count in sorted(storage_data['Threads'].unique()):
                    cache_thread_data = storage_data[
                        (storage_data['Cache'] == cache_type) &
                        (storage_data['Threads'] == thread_count)
                    ]
                    
                    if len(cache_thread_data) > 0:
                        x_labels.append(f'{cache_type}\n{thread_count}T')
                        x_positions.append(pos)
                        abs_values.append(cache_thread_data[f'{metric}_abs_diff'].iloc[0])
                        pos += 1
            
            if abs_values:
                bars = ax_abs.bar([p + metric_idx * 0.25 for p in x_positions], abs_values, 
                                 width=0.25, label=storage_type, color=storage_colors[storage_type], alpha=0.8)
                
                # Add value labels on bars
                for bar, value in zip(bars, abs_values):
                    height = bar.get_height()
                    ax_abs.annotate(f'{value:.1f}',
                                   xy=(bar.get_x() + bar.get_width() / 2, height),
                                   xytext=(0, 3 if height >= 0 else -15),
                                   textcoords="offset points",
                                   ha='center', va='bottom' if height >= 0 else 'top',
                                   fontsize=8, rotation=90)
        
        ax_abs.set_title(f'{config["title"]} - Absolute Difference\n(Optimized - Vanilla)', fontsize=12)
        ax_abs.set_ylabel(f'Difference ({config["unit"]})', fontsize=10)
        ax_abs.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax_abs.grid(True, alpha=0.3, axis='y')
        ax_abs.tick_params(axis='x', rotation=45, labelsize=8)
        
        # Relative differences (bottom row)
        ax_rel = axes[1, metric_idx]
        
        for storage_type in ['NVDIMM', 'NVM', 'SSD NVMe']:
            storage_data = differences_df[differences_df['Storage'] == storage_type]
            
            if len(storage_data) == 0:
                continue
            
            x_labels = []
            x_positions = []
            rel_values = []
            
            pos = 0
            for cache_type in sorted(storage_data['Cache'].unique()):
                for thread_count in sorted(storage_data['Threads'].unique()):
                    cache_thread_data = storage_data[
                        (storage_data['Cache'] == cache_type) &
                        (storage_data['Threads'] == thread_count)
                    ]
                    
                    if len(cache_thread_data) > 0:
                        x_labels.append(f'{cache_type}\n{thread_count}T')
                        x_positions.append(pos)
                        rel_values.append(cache_thread_data[f'{metric}_rel_diff'].iloc[0])
                        pos += 1
            
            if rel_values:
                bars = ax_rel.bar([p + metric_idx * 0.25 for p in x_positions], rel_values, 
                                 width=0.25, label=storage_type, color=storage_colors[storage_type], alpha=0.8)
                
                # Add value labels on bars
                for bar, value in zip(bars, rel_values):
                    height = bar.get_height()
                    ax_rel.annotate(f'{value:.1f}%',
                                   xy=(bar.get_x() + bar.get_width() / 2, height),
                                   xytext=(0, 3 if height >= 0 else -15),
                                   textcoords="offset points",
                                   ha='center', va='bottom' if height >= 0 else 'top',
                                   fontsize=8, rotation=90)
        
        ax_rel.set_title(f'{config["title"]} - Relative Difference\n(% Change)', fontsize=12)
        ax_rel.set_ylabel('Percentage Change (%)', fontsize=10)
        ax_rel.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        ax_rel.grid(True, alpha=0.3, axis='y')
        ax_rel.tick_params(axis='x', rotation=45, labelsize=8)
        
        # Set x-tick labels only for the first storage type to avoid overlap
        if len(x_labels) > 0:
            ax_abs.set_xticks(x_positions)
            ax_abs.set_xticklabels(x_labels)
            ax_rel.set_xticks(x_positions)
            ax_rel.set_xticklabels(x_labels)
    
    # Add legend
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper center', bbox_to_anchor=(0.5, 0.98), 
               ncol=3, fontsize=12, frameon=False)
    
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Difference plots saved to: {output_path}")
    
    return fig

def create_improvement_summary(differences_df, metrics_config, output_path):
    """Create summary table and visualization of improvements"""
    
    # Calculate summary statistics
    summary_stats = []
    
    for metric, config in metrics_config.items():
        rel_diff_col = f'{metric}_rel_diff'
        
        if rel_diff_col in differences_df.columns:
            # For metrics where higher is better, positive change is good
            # For metrics where lower is better, negative change is good
            if config['higher_better']:
                improvements = differences_df[differences_df[rel_diff_col] > 0][rel_diff_col]
                regressions = differences_df[differences_df[rel_diff_col] < 0][rel_diff_col]
            else:
                improvements = differences_df[differences_df[rel_diff_col] < 0][rel_diff_col].abs()
                regressions = differences_df[differences_df[rel_diff_col] > 0][rel_diff_col]
            
            summary_stats.append({
                'Metric': config['title'],
                'Avg Improvement (%)': improvements.mean() if len(improvements) > 0 else 0,
                'Max Improvement (%)': improvements.max() if len(improvements) > 0 else 0,
                'Avg Regression (%)': regressions.mean() if len(regressions) > 0 else 0,
                'Max Regression (%)': regressions.max() if len(regressions) > 0 else 0,
                'Improvement Cases': len(improvements),
                'Regression Cases': len(regressions),
                'Total Cases': len(differences_df)
            })
    
    summary_df = pd.DataFrame(summary_stats)
    
    # Create visualization
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # Plot 1: Average improvements vs regressions
    metrics = summary_df['Metric']
    improvements = summary_df['Avg Improvement (%)']
    regressions = -summary_df['Avg Regression (%)']  # Make negative for visualization
    
    x = np.arange(len(metrics))
    width = 0.35
    
    bars1 = ax1.bar(x - width/2, improvements, width, label='Average Improvement', 
                    color='green', alpha=0.7)
    bars2 = ax1.bar(x + width/2, regressions, width, label='Average Regression', 
                    color='red', alpha=0.7)
    
    ax1.set_xlabel('Metrics')
    ax1.set_ylabel('Percentage Change (%)')
    ax1.set_title('Average Improvements vs Regressions')
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics, rotation=45)
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if abs(height) > 0.1:  # Only show labels for significant values
                ax1.annotate(f'{height:.1f}%',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3 if height >= 0 else -15),
                           textcoords="offset points",
                           ha='center', va='bottom' if height >= 0 else 'top',
                           fontsize=10)
    
    # Plot 2: Number of improvement vs regression cases
    improvement_cases = summary_df['Improvement Cases']
    regression_cases = summary_df['Regression Cases']
    
    bars3 = ax2.bar(x - width/2, improvement_cases, width, label='Improvement Cases', 
                    color='green', alpha=0.7)
    bars4 = ax2.bar(x + width/2, regression_cases, width, label='Regression Cases', 
                    color='red', alpha=0.7)
    
    ax2.set_xlabel('Metrics')
    ax2.set_ylabel('Number of Cases')
    ax2.set_title('Number of Improvement vs Regression Cases')
    ax2.set_xticks(x)
    ax2.set_xticklabels(metrics, rotation=45)
    ax2.legend()
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bars in [bars3, bars4]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax2.annotate(f'{int(height)}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom',
                           fontsize=10)
    
    plt.tight_layout()
    plt.savefig(output_path.replace('.pdf', '_summary.pdf'), dpi=300, bbox_inches='tight')
    print(f"Improvement summary saved to: {output_path.replace('.pdf', '_summary.pdf')}")
    
    # Save summary table as CSV
    summary_df.to_csv(output_path.replace('.pdf', '_summary.csv'), index=False)
    print(f"Summary statistics saved to: {output_path.replace('.pdf', '_summary.csv')}")
    
    return fig, summary_df

def main():
    parser = argparse.ArgumentParser(description='Generate cache performance difference analysis')
    parser.add_argument('--vanilla-csv', required=True, help='Path to vanilla benchmark CSV file')
    parser.add_argument('--optimized-csv', required=True, help='Path to optimized benchmark CSV file')
    parser.add_argument('--output', default='cache_performance_differences.pdf', help='Output file path')
    
    args = parser.parse_args()
    
    try:
        # Load data
        vanilla_df = load_vanilla_data(args.vanilla_csv)
        optimized_df = load_optimized_data(args.optimized_csv)
        
        # Calculate differences
        differences_df, metrics_config = calculate_differences(vanilla_df, optimized_df)
        
        if len(differences_df) == 0:
            print("No matching data found for comparison")
            return
        
        # Create difference plots
        fig1 = create_difference_plots(differences_df, metrics_config, args.output)
        
        # Create improvement summary
        fig2, summary_df = create_improvement_summary(differences_df, metrics_config, args.output)
        
        print("Cache performance difference analysis completed successfully!")
        print("\nSummary Statistics:")
        print(summary_df.to_string(index=False))
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()