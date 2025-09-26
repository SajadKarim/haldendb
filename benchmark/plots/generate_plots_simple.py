#!/usr/bin/env python3
"""
Simple Cache Benchmark Analysis and Visualization Script
Compatible with older matplotlib/seaborn versions
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['font.size'] = 10

def load_and_prepare_data(csv_file):
    """Load CSV data and prepare derived metrics"""
    print(f"Loading data from: {csv_file}")
    df = pd.read_csv(csv_file)
    
    # Calculate derived metrics
    df['ipc'] = df['perf_instructions'] / df['perf_cycles']
    df['cache_miss_rate'] = df['perf_cache_misses'] / df['perf_cache_references']
    df['l1_miss_rate'] = df['perf_l1_dcache_load_misses'] / df['perf_l1_dcache_loads']
    df['llc_miss_rate'] = df['perf_llc_load_misses'] / df['perf_llc_loads']
    df['ops_per_cycle'] = df['throughput_ops_sec'] / (df['perf_cycles'] / df['perf_time_elapsed'])
    
    # Categorize operations
    df['operation_type'] = df['operation'].apply(lambda x: 'Write' if x in ['insert', 'delete'] else 'Read')
    
    print(f"Data loaded: {len(df)} rows, {len(df.columns)} columns")
    print(f"Cache types: {df['cache_type'].unique()}")
    print(f"Operations: {df['operation'].unique()}")
    
    return df

def plot_1_throughput_comparison(df, output_dir):
    """Plot 1: Throughput Comparison by Cache Type and Operation"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Box plot
    operations = df['operation'].unique()
    cache_types = df['cache_type'].unique()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    positions = []
    data_to_plot = []
    labels = []
    colors_list = []
    
    for i, op in enumerate(operations):
        for j, cache in enumerate(cache_types):
            subset = df[(df['operation'] == op) & (df['cache_type'] == cache)]
            if len(subset) > 0:
                data_to_plot.append(subset['throughput_ops_sec'].values)
                positions.append(i * len(cache_types) + j)
                labels.append(f"{op}\n{cache}")
                colors_list.append(colors[j])
    
    bp = ax1.boxplot(data_to_plot, positions=positions, patch_artist=True)
    for patch, color in zip(bp['boxes'], colors_list):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax1.set_xticks(positions)
    ax1.set_xticklabels(labels, rotation=45, ha='right')
    ax1.set_ylabel('Throughput (ops/sec)')
    ax1.set_title('Throughput Distribution by Operation and Cache Type')
    ax1.grid(True, alpha=0.3)
    
    # Bar plot with averages
    avg_data = df.groupby(['operation', 'cache_type'])['throughput_ops_sec'].mean().unstack()
    avg_data.plot(kind='bar', ax=ax2, color=colors)
    ax2.set_title('Average Throughput by Operation and Cache Type')
    ax2.set_ylabel('Average Throughput (ops/sec)')
    ax2.set_xlabel('Operation')
    ax2.legend(title='Cache Type')
    ax2.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/1_throughput_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Generated: 1_throughput_comparison.png")

def plot_2_cache_hit_ratio_analysis(df, output_dir):
    """Plot 2: Cache Hit Ratio Analysis"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Hit ratio vs throughput scatter
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    for i, cache in enumerate(df['cache_type'].unique()):
        cache_data = df[df['cache_type'] == cache]
        ax1.scatter(cache_data['cache_hit_ratio'], cache_data['throughput_ops_sec'], 
                   label=cache, alpha=0.7, s=60, color=colors[i])
    
    ax1.set_xlabel('Cache Hit Ratio')
    ax1.set_ylabel('Throughput (ops/sec)')
    ax1.set_title('Cache Hit Ratio vs Throughput')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Hit ratio by cache type
    cache_hit_data = []
    cache_labels = []
    for cache in df['cache_type'].unique():
        cache_data = df[df['cache_type'] == cache]['cache_hit_ratio']
        cache_hit_data.append(cache_data.values)
        cache_labels.append(cache)
    
    bp2 = ax2.boxplot(cache_hit_data, labels=cache_labels, patch_artist=True)
    for patch, color in zip(bp2['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax2.set_title('Cache Hit Ratio Distribution by Cache Type')
    ax2.set_ylabel('Cache Hit Ratio')
    
    # Cache misses vs evictions
    for i, cache in enumerate(df['cache_type'].unique()):
        cache_data = df[df['cache_type'] == cache]
        ax3.scatter(cache_data['cache_misses'], cache_data['evictions'], 
                   label=cache, alpha=0.7, s=60, color=colors[i])
    
    ax3.set_xlabel('Cache Misses')
    ax3.set_ylabel('Evictions')
    ax3.set_title('Cache Misses vs Evictions')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Average hit ratio by operation
    hit_ratio_by_op = df.groupby(['operation', 'cache_type'])['cache_hit_ratio'].mean().unstack()
    hit_ratio_by_op.plot(kind='bar', ax=ax4, color=colors)
    ax4.set_title('Average Cache Hit Ratio by Operation')
    ax4.set_ylabel('Cache Hit Ratio')
    ax4.set_xlabel('Operation')
    ax4.legend(title='Cache Type')
    ax4.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/2_cache_hit_ratio_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Generated: 2_cache_hit_ratio_analysis.png")

def plot_3_hardware_performance(df, output_dir):
    """Plot 3: Hardware Performance Analysis"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # IPC distribution
    ipc_data = []
    cache_labels = []
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    for cache in df['cache_type'].unique():
        cache_data = df[df['cache_type'] == cache]['ipc']
        ipc_data.append(cache_data.values)
        cache_labels.append(cache)
    
    bp1 = ax1.boxplot(ipc_data, labels=cache_labels, patch_artist=True)
    for patch, color in zip(bp1['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax1.set_title('Instructions Per Cycle (IPC) Distribution')
    ax1.set_ylabel('IPC')
    
    # Cache miss rate distribution
    miss_rate_data = []
    for cache in df['cache_type'].unique():
        cache_data = df[df['cache_type'] == cache]['cache_miss_rate']
        miss_rate_data.append(cache_data.values)
    
    bp2 = ax2.boxplot(miss_rate_data, labels=cache_labels, patch_artist=True)
    for patch, color in zip(bp2['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax2.set_title('Hardware Cache Miss Rate Distribution')
    ax2.set_ylabel('Cache Miss Rate')
    
    # IPC vs Throughput correlation
    for i, cache in enumerate(df['cache_type'].unique()):
        cache_data = df[df['cache_type'] == cache]
        ax3.scatter(cache_data['ipc'], cache_data['throughput_ops_sec'], 
                   label=cache, alpha=0.7, s=60, color=colors[i])
    
    ax3.set_xlabel('Instructions Per Cycle (IPC)')
    ax3.set_ylabel('Throughput (ops/sec)')
    ax3.set_title('IPC vs Throughput Correlation')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # L1 vs LLC miss rates
    for i, cache in enumerate(df['cache_type'].unique()):
        cache_data = df[df['cache_type'] == cache]
        ax4.scatter(cache_data['l1_miss_rate'], cache_data['llc_miss_rate'], 
                   label=cache, alpha=0.7, s=60, color=colors[i])
    
    ax4.set_xlabel('L1 Cache Miss Rate')
    ax4.set_ylabel('LLC Miss Rate')
    ax4.set_title('L1 vs LLC Miss Rates')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/3_hardware_performance.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Generated: 3_hardware_performance.png")

def plot_4_operation_analysis(df, output_dir):
    """Plot 4: Operation-Specific Analysis"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    # Search operations comparison
    search_ops = df[df['operation'].str.contains('search')]
    search_avg = search_ops.groupby(['operation', 'cache_type'])['throughput_ops_sec'].mean().unstack()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    search_avg.plot(kind='bar', ax=ax1, color=colors)
    ax1.set_title('Search Operation Performance by Access Pattern')
    ax1.set_ylabel('Average Throughput (ops/sec)')
    ax1.set_xlabel('Search Pattern')
    ax1.legend(title='Cache Type')
    ax1.tick_params(axis='x', rotation=45)
    
    # Read vs Write performance
    rw_avg = df.groupby(['operation_type', 'cache_type'])['throughput_ops_sec'].mean().unstack()
    rw_avg.plot(kind='bar', ax=ax2, color=colors)
    ax2.set_title('Read vs Write Performance')
    ax2.set_ylabel('Average Throughput (ops/sec)')
    ax2.set_xlabel('Operation Type')
    ax2.legend(title='Cache Type')
    ax2.tick_params(axis='x', rotation=0)
    
    # Operations per CPU cycle
    ops_cycle_avg = df.groupby(['operation', 'cache_type'])['ops_per_cycle'].mean().unstack()
    ops_cycle_avg.plot(kind='bar', ax=ax3, color=colors)
    ax3.set_title('Operations per CPU Cycle by Operation')
    ax3.set_ylabel('Operations per CPU Cycle')
    ax3.set_xlabel('Operation')
    ax3.legend(title='Cache Type')
    ax3.tick_params(axis='x', rotation=45)
    
    # Performance variability (coefficient of variation)
    cv_data = df.groupby(['cache_type', 'operation'])['throughput_ops_sec'].agg(['mean', 'std'])
    cv_data['cv'] = cv_data['std'] / cv_data['mean']
    cv_pivot = cv_data['cv'].unstack()
    
    im = ax4.imshow(cv_pivot.values, cmap='YlOrRd', aspect='auto')
    ax4.set_xticks(range(len(cv_pivot.columns)))
    ax4.set_xticklabels(cv_pivot.columns, rotation=45)
    ax4.set_yticks(range(len(cv_pivot.index)))
    ax4.set_yticklabels(cv_pivot.index)
    ax4.set_title('Performance Variability (Coefficient of Variation)')
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax4)
    cbar.set_label('Coefficient of Variation')
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/4_operation_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Generated: 4_operation_analysis.png")

def plot_5_correlation_and_pca(df, output_dir):
    """Plot 5: Correlation Matrix and PCA Analysis"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Correlation matrix
    numeric_cols = ['throughput_ops_sec', 'cache_hit_ratio', 'cache_misses', 'evictions', 
                    'ipc', 'cache_miss_rate', 'l1_miss_rate', 'llc_miss_rate']
    
    correlation_matrix = df[numeric_cols].corr()
    im1 = ax1.imshow(correlation_matrix.values, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')
    ax1.set_xticks(range(len(correlation_matrix.columns)))
    ax1.set_xticklabels(correlation_matrix.columns, rotation=45, ha='right')
    ax1.set_yticks(range(len(correlation_matrix.index)))
    ax1.set_yticklabels(correlation_matrix.index)
    ax1.set_title('Performance Metrics Correlation Matrix')
    
    # Add correlation values as text
    for i in range(len(correlation_matrix.index)):
        for j in range(len(correlation_matrix.columns)):
            ax1.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}', 
                    ha='center', va='center', fontsize=8)
    
    cbar1 = plt.colorbar(im1, ax=ax1)
    cbar1.set_label('Correlation Coefficient')
    
    # PCA Analysis
    features = ['throughput_ops_sec', 'cache_hit_ratio', 'ipc', 'cache_miss_rate', 
               'l1_miss_rate', 'llc_miss_rate']
    X = df[features].fillna(0)
    X_scaled = StandardScaler().fit_transform(X)
    
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    for i, cache in enumerate(df['cache_type'].unique()):
        mask = df['cache_type'] == cache
        ax2.scatter(X_pca[mask, 0], X_pca[mask, 1], label=cache, alpha=0.7, s=60, color=colors[i])
    
    ax2.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)')
    ax2.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)')
    ax2.set_title('PCA: Cache Algorithm Performance Characteristics')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/5_correlation_and_pca.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Generated: 5_correlation_and_pca.png")

def plot_6_comprehensive_dashboard(df, output_dir):
    """Plot 6: Comprehensive Performance Dashboard"""
    fig = plt.figure(figsize=(20, 16))
    
    # Create a 4x3 grid
    ax1 = plt.subplot(4, 3, 1)
    ax2 = plt.subplot(4, 3, 2)
    ax3 = plt.subplot(4, 3, 3)
    ax4 = plt.subplot(4, 3, 4)
    ax5 = plt.subplot(4, 3, 5)
    ax6 = plt.subplot(4, 3, 6)
    ax7 = plt.subplot(4, 3, 7)
    ax8 = plt.subplot(4, 3, 8)
    ax9 = plt.subplot(4, 3, 9)
    ax10 = plt.subplot(4, 3, (10, 12))  # Span last row
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    # 1. Average throughput by cache type
    throughput_avg = df.groupby('cache_type')['throughput_ops_sec'].mean()
    throughput_avg.plot(kind='bar', ax=ax1, color=colors)
    ax1.set_title('Avg Throughput by Cache')
    ax1.set_ylabel('Throughput (ops/sec)')
    ax1.tick_params(axis='x', rotation=0)
    
    # 2. Average hit ratio by cache type
    hit_ratio_avg = df.groupby('cache_type')['cache_hit_ratio'].mean()
    hit_ratio_avg.plot(kind='bar', ax=ax2, color=colors)
    ax2.set_title('Avg Hit Ratio by Cache')
    ax2.set_ylabel('Hit Ratio')
    ax2.tick_params(axis='x', rotation=0)
    
    # 3. Average IPC by cache type
    ipc_avg = df.groupby('cache_type')['ipc'].mean()
    ipc_avg.plot(kind='bar', ax=ax3, color=colors)
    ax3.set_title('Avg IPC by Cache')
    ax3.set_ylabel('IPC')
    ax3.tick_params(axis='x', rotation=0)
    
    # 4. Best operation for each cache
    best_ops = df.loc[df.groupby('cache_type')['throughput_ops_sec'].idxmax()]
    best_ops.plot(x='cache_type', y='throughput_ops_sec', kind='bar', ax=ax4, color=colors)
    ax4.set_title('Best Performance by Cache')
    ax4.set_ylabel('Best Throughput (ops/sec)')
    ax4.tick_params(axis='x', rotation=0)
    
    # 5. Search operations heatmap
    search_data = df[df['operation'].str.contains('search')]
    search_pivot = search_data.groupby(['cache_type', 'operation'])['throughput_ops_sec'].mean().unstack()
    im5 = ax5.imshow(search_pivot.values, cmap='YlOrRd', aspect='auto')
    ax5.set_xticks(range(len(search_pivot.columns)))
    ax5.set_xticklabels([col.replace('search_', '') for col in search_pivot.columns], rotation=45)
    ax5.set_yticks(range(len(search_pivot.index)))
    ax5.set_yticklabels(search_pivot.index)
    ax5.set_title('Search Patterns Performance')
    
    # 6. Read vs Write comparison
    rw_data = df.groupby(['cache_type', 'operation_type'])['throughput_ops_sec'].mean().unstack()
    rw_data.plot(kind='bar', ax=ax6, color=['lightcoral', 'lightblue'])
    ax6.set_title('Read vs Write Performance')
    ax6.set_ylabel('Throughput (ops/sec)')
    ax6.tick_params(axis='x', rotation=0)
    ax6.legend(['Read', 'Write'])
    
    # 7. Cache efficiency (hit ratio vs miss rate)
    for i, cache in enumerate(df['cache_type'].unique()):
        cache_data = df[df['cache_type'] == cache]
        ax7.scatter(cache_data['cache_hit_ratio'], cache_data['cache_miss_rate'], 
                   label=cache, alpha=0.7, color=colors[i])
    ax7.set_xlabel('App Cache Hit Ratio')
    ax7.set_ylabel('HW Cache Miss Rate')
    ax7.set_title('Cache Efficiency Correlation')
    ax7.legend()
    ax7.grid(True, alpha=0.3)
    
    # 8. Performance consistency (std dev)
    consistency = df.groupby('cache_type')['throughput_ops_sec'].std()
    consistency.plot(kind='bar', ax=ax8, color=colors)
    ax8.set_title('Performance Consistency')
    ax8.set_ylabel('Std Dev (ops/sec)')
    ax8.tick_params(axis='x', rotation=0)
    
    # 9. Operations per cycle efficiency
    efficiency_avg = df.groupby('cache_type')['ops_per_cycle'].mean()
    efficiency_avg.plot(kind='bar', ax=ax9, color=colors)
    ax9.set_title('CPU Efficiency')
    ax9.set_ylabel('Ops per Cycle')
    ax9.tick_params(axis='x', rotation=0)
    
    # 10. Summary table
    ax10.axis('tight')
    ax10.axis('off')
    
    summary_stats = df.groupby('cache_type').agg({
        'throughput_ops_sec': ['mean', 'std', 'max'],
        'cache_hit_ratio': ['mean', 'std'],
        'ipc': ['mean', 'std'],
        'cache_miss_rate': ['mean', 'std']
    }).round(2)
    
    # Flatten column names
    summary_stats.columns = ['Throughput Mean', 'Throughput Std', 'Throughput Max',
                            'Hit Ratio Mean', 'Hit Ratio Std', 'IPC Mean', 'IPC Std',
                            'Miss Rate Mean', 'Miss Rate Std']
    
    # Create table
    table_data = []
    for idx, row in summary_stats.iterrows():
        table_data.append([idx] + row.tolist())
    
    table = ax10.table(cellText=table_data,
                      colLabels=['Cache Type'] + list(summary_stats.columns),
                      cellLoc='center',
                      loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1.2, 1.5)
    ax10.set_title('Summary Statistics by Cache Type', fontweight='bold', pad=20)
    
    plt.suptitle('Cache Performance Comprehensive Dashboard', fontsize=20, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/6_comprehensive_dashboard.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Generated: 6_comprehensive_dashboard.png")

def generate_summary_report(df, output_dir):
    """Generate a text summary report"""
    report_path = f'{output_dir}/analysis_summary.txt'
    
    with open(report_path, 'w') as f:
        f.write("CACHE BENCHMARK ANALYSIS SUMMARY REPORT\n")
        f.write("=" * 50 + "\n\n")
        
        f.write(f"Dataset Overview:\n")
        f.write(f"- Total records: {len(df)}\n")
        f.write(f"- Cache types tested: {', '.join(df['cache_type'].unique())}\n")
        f.write(f"- Operations tested: {', '.join(df['operation'].unique())}\n")
        f.write(f"- Runs per configuration: {df['run_id'].nunique()}\n\n")
        
        f.write("Performance Summary by Cache Type:\n")
        f.write("-" * 40 + "\n")
        
        for cache in df['cache_type'].unique():
            cache_data = df[df['cache_type'] == cache]
            f.write(f"\n{cache} Cache:\n")
            f.write(f"  Average Throughput: {cache_data['throughput_ops_sec'].mean():.2f} ops/sec\n")
            f.write(f"  Average Hit Ratio: {cache_data['cache_hit_ratio'].mean():.4f}\n")
            f.write(f"  Average IPC: {cache_data['ipc'].mean():.4f}\n")
            f.write(f"  Best Operation: {cache_data.loc[cache_data['throughput_ops_sec'].idxmax(), 'operation']}\n")
            f.write(f"  Best Throughput: {cache_data['throughput_ops_sec'].max():.2f} ops/sec\n")
        
        f.write("\n\nOperation Analysis:\n")
        f.write("-" * 20 + "\n")
        
        for op in df['operation'].unique():
            op_data = df[df['operation'] == op]
            best_cache = op_data.loc[op_data['throughput_ops_sec'].idxmax(), 'cache_type']
            f.write(f"\n{op}:\n")
            f.write(f"  Best Cache: {best_cache}\n")
            f.write(f"  Best Throughput: {op_data['throughput_ops_sec'].max():.2f} ops/sec\n")
            f.write(f"  Average Hit Ratio: {op_data['cache_hit_ratio'].mean():.4f}\n")
        
        # Key insights
        f.write("\n\nKey Insights:\n")
        f.write("-" * 15 + "\n")
        
        # Best overall cache
        overall_best = df.groupby('cache_type')['throughput_ops_sec'].mean().idxmax()
        f.write(f"- Best overall cache: {overall_best}\n")
        
        # Best for sequential access
        seq_data = df[df['operation'] == 'search_sequential']
        seq_best = seq_data.loc[seq_data['throughput_ops_sec'].idxmax(), 'cache_type']
        f.write(f"- Best for sequential access: {seq_best}\n")
        
        # Best for random access
        rand_data = df[df['operation'] == 'search_random']
        rand_best = rand_data.loc[rand_data['throughput_ops_sec'].idxmax(), 'cache_type']
        f.write(f"- Best for random access: {rand_best}\n")
        
        # Highest hit ratio
        hit_ratio_best = df.groupby('cache_type')['cache_hit_ratio'].mean().idxmax()
        f.write(f"- Highest average hit ratio: {hit_ratio_best}\n")
        
        # Most CPU efficient
        ipc_best = df.groupby('cache_type')['ipc'].mean().idxmax()
        f.write(f"- Most CPU efficient (highest IPC): {ipc_best}\n")
    
    print(f"✓ Generated: analysis_summary.txt")

def main():
    """Main function to generate all plots"""
    # Configuration
    csv_file = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250922_123326/combined_benchmark_results_with_perf_20250922_132611.csv"
    output_dir = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/plots"
    
    print("Cache Benchmark Analysis - Generating All Plots")
    print("=" * 50)
    
    # Load and prepare data
    df = load_and_prepare_data(csv_file)
    
    # Generate all plots
    plot_functions = [
        plot_1_throughput_comparison,
        plot_2_cache_hit_ratio_analysis,
        plot_3_hardware_performance,
        plot_4_operation_analysis,
        plot_5_correlation_and_pca,
        plot_6_comprehensive_dashboard
    ]
    
    print(f"\nGenerating {len(plot_functions)} plots...")
    print("-" * 30)
    
    for plot_func in plot_functions:
        try:
            plot_func(df, output_dir)
        except Exception as e:
            print(f"✗ Error generating {plot_func.__name__}: {e}")
    
    # Generate summary report
    generate_summary_report(df, output_dir)
    
    print("\n" + "=" * 50)
    print("All plots generated successfully!")
    print(f"Output directory: {output_dir}")
    print("=" * 50)

if __name__ == "__main__":
    main()