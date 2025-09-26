#!/usr/bin/env python3
"""
Basic Cache Benchmark Analysis and Visualization Script
Uses basic matplotlib functionality to avoid compatibility issues
"""

import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
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
    
    # Simple bar plot of averages
    cache_types = df['cache_type'].unique()
    operations = df['operation'].unique()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    # Average throughput by cache type
    cache_means = []
    cache_stds = []
    for cache in cache_types:
        cache_data = df[df['cache_type'] == cache]['throughput_ops_sec']
        cache_means.append(cache_data.mean())
        cache_stds.append(cache_data.std())
    
    x_pos = np.arange(len(cache_types))
    bars1 = ax1.bar(x_pos, cache_means, yerr=cache_stds, color=colors, alpha=0.8, capsize=5)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(cache_types)
    ax1.set_ylabel('Average Throughput (ops/sec)')
    ax1.set_title('Average Throughput by Cache Type')
    ax1.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for i, (mean, std) in enumerate(zip(cache_means, cache_stds)):
        ax1.text(i, mean + std + max(cache_means)*0.02, f'{mean:.0f}', 
                ha='center', va='bottom', fontweight='bold')
    
    # Throughput by operation (best cache for each)
    op_best_throughput = []
    op_best_cache = []
    for op in operations:
        op_data = df[df['operation'] == op]
        best_idx = op_data['throughput_ops_sec'].idxmax()
        op_best_throughput.append(op_data.loc[best_idx, 'throughput_ops_sec'])
        op_best_cache.append(op_data.loc[best_idx, 'cache_type'])
    
    # Color bars by best cache
    bar_colors = [colors[list(cache_types).index(cache)] for cache in op_best_cache]
    
    x_pos2 = np.arange(len(operations))
    bars2 = ax2.bar(x_pos2, op_best_throughput, color=bar_colors, alpha=0.8)
    ax2.set_xticks(x_pos2)
    ax2.set_xticklabels([op.replace('_', '\n') for op in operations], rotation=0, ha='center')
    ax2.set_ylabel('Best Throughput (ops/sec)')
    ax2.set_title('Best Performance by Operation')
    ax2.grid(True, alpha=0.3)
    
    # Add cache type labels on bars
    for i, (throughput, cache) in enumerate(zip(op_best_throughput, op_best_cache)):
        ax2.text(i, throughput + max(op_best_throughput)*0.02, cache, 
                ha='center', va='bottom', fontweight='bold', fontsize=8)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/1_throughput_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Generated: 1_throughput_comparison.png")

def plot_2_cache_efficiency(df, output_dir):
    """Plot 2: Cache Efficiency Analysis"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    cache_types = df['cache_type'].unique()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    # Hit ratio vs throughput scatter
    for i, cache in enumerate(cache_types):
        cache_data = df[df['cache_type'] == cache]
        ax1.scatter(cache_data['cache_hit_ratio'], cache_data['throughput_ops_sec'], 
                   label=cache, alpha=0.7, s=60, color=colors[i])
    
    ax1.set_xlabel('Cache Hit Ratio')
    ax1.set_ylabel('Throughput (ops/sec)')
    ax1.set_title('Cache Hit Ratio vs Throughput')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Average hit ratio by cache type
    hit_ratios = []
    hit_ratio_stds = []
    for cache in cache_types:
        cache_data = df[df['cache_type'] == cache]['cache_hit_ratio']
        hit_ratios.append(cache_data.mean())
        hit_ratio_stds.append(cache_data.std())
    
    x_pos = np.arange(len(cache_types))
    bars = ax2.bar(x_pos, hit_ratios, yerr=hit_ratio_stds, color=colors, alpha=0.8, capsize=5)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(cache_types)
    ax2.set_ylabel('Average Cache Hit Ratio')
    ax2.set_title('Cache Hit Ratio by Cache Type')
    ax2.grid(True, alpha=0.3)
    
    # Add value labels
    for i, (ratio, std) in enumerate(zip(hit_ratios, hit_ratio_stds)):
        ax2.text(i, ratio + std + 0.01, f'{ratio:.3f}', 
                ha='center', va='bottom', fontweight='bold')
    
    # Cache misses vs evictions
    for i, cache in enumerate(cache_types):
        cache_data = df[df['cache_type'] == cache]
        ax3.scatter(cache_data['cache_misses'], cache_data['evictions'], 
                   label=cache, alpha=0.7, s=60, color=colors[i])
    
    ax3.set_xlabel('Cache Misses')
    ax3.set_ylabel('Evictions')
    ax3.set_title('Cache Misses vs Evictions')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # Average evictions by cache type
    evictions = []
    eviction_stds = []
    for cache in cache_types:
        cache_data = df[df['cache_type'] == cache]['evictions']
        evictions.append(cache_data.mean())
        eviction_stds.append(cache_data.std())
    
    bars = ax4.bar(x_pos, evictions, yerr=eviction_stds, color=colors, alpha=0.8, capsize=5)
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(cache_types)
    ax4.set_ylabel('Average Evictions')
    ax4.set_title('Cache Evictions by Cache Type')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/2_cache_efficiency.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Generated: 2_cache_efficiency.png")

def plot_3_hardware_performance(df, output_dir):
    """Plot 3: Hardware Performance Analysis"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    
    cache_types = df['cache_type'].unique()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    # IPC by cache type
    ipc_means = []
    ipc_stds = []
    for cache in cache_types:
        cache_data = df[df['cache_type'] == cache]['ipc']
        ipc_means.append(cache_data.mean())
        ipc_stds.append(cache_data.std())
    
    x_pos = np.arange(len(cache_types))
    bars = ax1.bar(x_pos, ipc_means, yerr=ipc_stds, color=colors, alpha=0.8, capsize=5)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(cache_types)
    ax1.set_ylabel('Instructions Per Cycle (IPC)')
    ax1.set_title('CPU Efficiency by Cache Type')
    ax1.grid(True, alpha=0.3)
    
    # Hardware cache miss rate
    miss_rates = []
    miss_rate_stds = []
    for cache in cache_types:
        cache_data = df[df['cache_type'] == cache]['cache_miss_rate']
        miss_rates.append(cache_data.mean())
        miss_rate_stds.append(cache_data.std())
    
    bars = ax2.bar(x_pos, miss_rates, yerr=miss_rate_stds, color=colors, alpha=0.8, capsize=5)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(cache_types)
    ax2.set_ylabel('Hardware Cache Miss Rate')
    ax2.set_title('Hardware Cache Miss Rate by Cache Type')
    ax2.grid(True, alpha=0.3)
    
    # IPC vs Throughput correlation
    for i, cache in enumerate(cache_types):
        cache_data = df[df['cache_type'] == cache]
        ax3.scatter(cache_data['ipc'], cache_data['throughput_ops_sec'], 
                   label=cache, alpha=0.7, s=60, color=colors[i])
    
    ax3.set_xlabel('Instructions Per Cycle (IPC)')
    ax3.set_ylabel('Throughput (ops/sec)')
    ax3.set_title('IPC vs Throughput Correlation')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    # L1 vs LLC miss rates
    for i, cache in enumerate(cache_types):
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
    
    cache_types = df['cache_type'].unique()
    operations = df['operation'].unique()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    # Search operations comparison
    search_ops = [op for op in operations if 'search' in op]
    search_data = []
    search_labels = []
    
    for op in search_ops:
        op_data = df[df['operation'] == op]
        best_idx = op_data['throughput_ops_sec'].idxmax()
        search_data.append(op_data.loc[best_idx, 'throughput_ops_sec'])
        search_labels.append(op.replace('search_', '').title())
    
    x_pos = np.arange(len(search_ops))
    bars = ax1.bar(x_pos, search_data, color='skyblue', alpha=0.8)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(search_labels, rotation=45)
    ax1.set_ylabel('Best Throughput (ops/sec)')
    ax1.set_title('Search Pattern Performance (Best Cache)')
    ax1.grid(True, alpha=0.3)
    
    # Read vs Write performance
    read_ops = [op for op in operations if op not in ['insert', 'delete']]
    write_ops = ['insert', 'delete']
    
    read_throughput = df[df['operation'].isin(read_ops)]['throughput_ops_sec'].mean()
    write_throughput = df[df['operation'].isin(write_ops)]['throughput_ops_sec'].mean()
    
    read_std = df[df['operation'].isin(read_ops)]['throughput_ops_sec'].std()
    write_std = df[df['operation'].isin(write_ops)]['throughput_ops_sec'].std()
    
    categories = ['Read', 'Write']
    means = [read_throughput, write_throughput]
    stds = [read_std, write_std]
    
    bars = ax2.bar(categories, means, yerr=stds, color=['lightblue', 'lightcoral'], 
                   alpha=0.8, capsize=5)
    ax2.set_ylabel('Average Throughput (ops/sec)')
    ax2.set_title('Read vs Write Performance')
    ax2.grid(True, alpha=0.3)
    
    # Operations per CPU cycle
    ops_cycle_means = []
    for cache in cache_types:
        cache_data = df[df['cache_type'] == cache]['ops_per_cycle']
        ops_cycle_means.append(cache_data.mean())
    
    x_pos = np.arange(len(cache_types))
    bars = ax3.bar(x_pos, ops_cycle_means, color=colors, alpha=0.8)
    ax3.set_xticks(x_pos)
    ax3.set_xticklabels(cache_types)
    ax3.set_ylabel('Operations per CPU Cycle')
    ax3.set_title('CPU Efficiency by Cache Type')
    ax3.grid(True, alpha=0.3)
    
    # Performance by operation type (detailed)
    op_means = []
    op_labels = []
    for op in operations:
        op_data = df[df['operation'] == op]['throughput_ops_sec']
        op_means.append(op_data.mean())
        op_labels.append(op.replace('_', '\n'))
    
    x_pos = np.arange(len(operations))
    bars = ax4.bar(x_pos, op_means, color='lightgreen', alpha=0.8)
    ax4.set_xticks(x_pos)
    ax4.set_xticklabels(op_labels, rotation=0, ha='center')
    ax4.set_ylabel('Average Throughput (ops/sec)')
    ax4.set_title('Average Performance by Operation')
    ax4.grid(True, alpha=0.3)
    
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
    
    # Manual heatmap
    im = ax1.imshow(correlation_matrix.values, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')
    ax1.set_xticks(range(len(correlation_matrix.columns)))
    ax1.set_xticklabels([col.replace('_', '\n') for col in correlation_matrix.columns], 
                       rotation=45, ha='right', fontsize=8)
    ax1.set_yticks(range(len(correlation_matrix.index)))
    ax1.set_yticklabels([col.replace('_', '\n') for col in correlation_matrix.index], fontsize=8)
    ax1.set_title('Performance Metrics Correlation Matrix')
    
    # Add correlation values as text
    for i in range(len(correlation_matrix.index)):
        for j in range(len(correlation_matrix.columns)):
            text_color = 'white' if abs(correlation_matrix.iloc[i, j]) > 0.5 else 'black'
            ax1.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}', 
                    ha='center', va='center', fontsize=7, color=text_color)
    
    # Add colorbar
    cbar = plt.colorbar(im, ax=ax1)
    cbar.set_label('Correlation Coefficient')
    
    # PCA Analysis
    features = ['throughput_ops_sec', 'cache_hit_ratio', 'ipc', 'cache_miss_rate', 
               'l1_miss_rate', 'llc_miss_rate']
    X = df[features].fillna(0)
    X_scaled = StandardScaler().fit_transform(X)
    
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    cache_types = df['cache_type'].unique()
    
    for i, cache in enumerate(cache_types):
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

def plot_6_summary_dashboard(df, output_dir):
    """Plot 6: Summary Dashboard"""
    fig, ((ax1, ax2, ax3), (ax4, ax5, ax6)) = plt.subplots(2, 3, figsize=(18, 12))
    
    cache_types = df['cache_type'].unique()
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']
    
    # 1. Overall performance ranking
    overall_means = []
    for cache in cache_types:
        cache_data = df[df['cache_type'] == cache]['throughput_ops_sec']
        overall_means.append(cache_data.mean())
    
    # Sort by performance
    sorted_indices = np.argsort(overall_means)[::-1]  # Descending order
    sorted_caches = [cache_types[i] for i in sorted_indices]
    sorted_means = [overall_means[i] for i in sorted_indices]
    sorted_colors = [colors[i] for i in sorted_indices]
    
    bars = ax1.bar(range(len(sorted_caches)), sorted_means, color=sorted_colors, alpha=0.8)
    ax1.set_xticks(range(len(sorted_caches)))
    ax1.set_xticklabels(sorted_caches)
    ax1.set_ylabel('Average Throughput (ops/sec)')
    ax1.set_title('Overall Performance Ranking')
    ax1.grid(True, alpha=0.3)
    
    # Add ranking numbers
    for i, (cache, mean) in enumerate(zip(sorted_caches, sorted_means)):
        ax1.text(i, mean + max(sorted_means)*0.02, f'#{i+1}', 
                ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    # 2. Cache hit ratio comparison
    hit_ratios = []
    for cache in cache_types:
        cache_data = df[df['cache_type'] == cache]['cache_hit_ratio']
        hit_ratios.append(cache_data.mean())
    
    bars = ax2.bar(range(len(cache_types)), hit_ratios, color=colors, alpha=0.8)
    ax2.set_xticks(range(len(cache_types)))
    ax2.set_xticklabels(cache_types)
    ax2.set_ylabel('Average Cache Hit Ratio')
    ax2.set_title('Cache Hit Ratio Comparison')
    ax2.grid(True, alpha=0.3)
    
    # 3. CPU efficiency (IPC)
    ipc_means = []
    for cache in cache_types:
        cache_data = df[df['cache_type'] == cache]['ipc']
        ipc_means.append(cache_data.mean())
    
    bars = ax3.bar(range(len(cache_types)), ipc_means, color=colors, alpha=0.8)
    ax3.set_xticks(range(len(cache_types)))
    ax3.set_xticklabels(cache_types)
    ax3.set_ylabel('Average IPC')
    ax3.set_title('CPU Efficiency (IPC)')
    ax3.grid(True, alpha=0.3)
    
    # 4. Best operation for each cache
    best_ops = []
    best_throughputs = []
    for cache in cache_types:
        cache_data = df[df['cache_type'] == cache]
        best_idx = cache_data['throughput_ops_sec'].idxmax()
        best_ops.append(cache_data.loc[best_idx, 'operation'])
        best_throughputs.append(cache_data.loc[best_idx, 'throughput_ops_sec'])
    
    bars = ax4.bar(range(len(cache_types)), best_throughputs, color=colors, alpha=0.8)
    ax4.set_xticks(range(len(cache_types)))
    ax4.set_xticklabels(cache_types)
    ax4.set_ylabel('Best Throughput (ops/sec)')
    ax4.set_title('Peak Performance by Cache')
    ax4.grid(True, alpha=0.3)
    
    # Add operation labels
    for i, (cache, op, throughput) in enumerate(zip(cache_types, best_ops, best_throughputs)):
        ax4.text(i, throughput + max(best_throughputs)*0.02, op.replace('_', '\n'), 
                ha='center', va='bottom', fontsize=8)
    
    # 5. Performance consistency (coefficient of variation)
    cv_values = []
    for cache in cache_types:
        cache_data = df[df['cache_type'] == cache]['throughput_ops_sec']
        cv = cache_data.std() / cache_data.mean()
        cv_values.append(cv)
    
    bars = ax5.bar(range(len(cache_types)), cv_values, color=colors, alpha=0.8)
    ax5.set_xticks(range(len(cache_types)))
    ax5.set_xticklabels(cache_types)
    ax5.set_ylabel('Coefficient of Variation')
    ax5.set_title('Performance Consistency\n(Lower is Better)')
    ax5.grid(True, alpha=0.3)
    
    # 6. Search vs Non-search performance
    search_perf = []
    nonsearch_perf = []
    
    for cache in cache_types:
        cache_data = df[df['cache_type'] == cache]
        search_data = cache_data[cache_data['operation'].str.contains('search')]
        nonsearch_data = cache_data[~cache_data['operation'].str.contains('search')]
        
        search_perf.append(search_data['throughput_ops_sec'].mean())
        nonsearch_perf.append(nonsearch_data['throughput_ops_sec'].mean())
    
    x_pos = np.arange(len(cache_types))
    width = 0.35
    
    bars1 = ax6.bar(x_pos - width/2, search_perf, width, label='Search Ops', 
                    color='lightblue', alpha=0.8)
    bars2 = ax6.bar(x_pos + width/2, nonsearch_perf, width, label='Insert/Delete', 
                    color='lightcoral', alpha=0.8)
    
    ax6.set_xticks(x_pos)
    ax6.set_xticklabels(cache_types)
    ax6.set_ylabel('Average Throughput (ops/sec)')
    ax6.set_title('Search vs Insert/Delete Performance')
    ax6.legend()
    ax6.grid(True, alpha=0.3)
    
    plt.suptitle('Cache Performance Summary Dashboard', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(f'{output_dir}/6_summary_dashboard.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("✓ Generated: 6_summary_dashboard.png")

def generate_summary_report(df, output_dir):
    """Generate a comprehensive text summary report"""
    report_path = f'{output_dir}/analysis_summary.txt'
    
    with open(report_path, 'w') as f:
        f.write("CACHE BENCHMARK ANALYSIS SUMMARY REPORT\n")
        f.write("=" * 60 + "\n\n")
        
        f.write(f"Dataset Overview:\n")
        f.write(f"- Total records: {len(df)}\n")
        f.write(f"- Cache types tested: {', '.join(df['cache_type'].unique())}\n")
        f.write(f"- Operations tested: {', '.join(df['operation'].unique())}\n")
        f.write(f"- Runs per configuration: {df['run_id'].nunique()}\n")
        f.write(f"- Thread count: {df['thread_count'].iloc[0]}\n")
        f.write(f"- Record count: {df['record_count'].iloc[0]:,}\n")
        f.write(f"- Cache size: {df['cache_page_limit'].iloc[0]} pages ({df['cache_size'].iloc[0]:.1%})\n\n")
        
        f.write("PERFORMANCE SUMMARY BY CACHE TYPE:\n")
        f.write("=" * 40 + "\n")
        
        cache_summary = []
        for cache in df['cache_type'].unique():
            cache_data = df[df['cache_type'] == cache]
            summary = {
                'cache': cache,
                'avg_throughput': cache_data['throughput_ops_sec'].mean(),
                'max_throughput': cache_data['throughput_ops_sec'].max(),
                'avg_hit_ratio': cache_data['cache_hit_ratio'].mean(),
                'avg_ipc': cache_data['ipc'].mean(),
                'consistency': cache_data['throughput_ops_sec'].std() / cache_data['throughput_ops_sec'].mean(),
                'best_op': cache_data.loc[cache_data['throughput_ops_sec'].idxmax(), 'operation']
            }
            cache_summary.append(summary)
        
        # Sort by average throughput
        cache_summary.sort(key=lambda x: x['avg_throughput'], reverse=True)
        
        for i, summary in enumerate(cache_summary):
            f.write(f"\n{i+1}. {summary['cache']} Cache:\n")
            f.write(f"   Average Throughput: {summary['avg_throughput']:.2f} ops/sec\n")
            f.write(f"   Peak Throughput: {summary['max_throughput']:.2f} ops/sec\n")
            f.write(f"   Average Hit Ratio: {summary['avg_hit_ratio']:.4f} ({summary['avg_hit_ratio']:.1%})\n")
            f.write(f"   Average IPC: {summary['avg_ipc']:.4f}\n")
            f.write(f"   Performance Consistency: {summary['consistency']:.4f} (lower is better)\n")
            f.write(f"   Best Operation: {summary['best_op']}\n")
        
        f.write("\n\nOPERATION ANALYSIS:\n")
        f.write("=" * 20 + "\n")
        
        operations = df['operation'].unique()
        for op in operations:
            op_data = df[df['operation'] == op]
            best_cache = op_data.loc[op_data['throughput_ops_sec'].idxmax(), 'cache_type']
            best_throughput = op_data['throughput_ops_sec'].max()
            avg_hit_ratio = op_data['cache_hit_ratio'].mean()
            
            f.write(f"\n{op.replace('_', ' ').title()}:\n")
            f.write(f"   Best Cache: {best_cache}\n")
            f.write(f"   Best Throughput: {best_throughput:.2f} ops/sec\n")
            f.write(f"   Average Hit Ratio: {avg_hit_ratio:.4f}\n")
            
            # Performance ranking for this operation
            op_ranking = op_data.groupby('cache_type')['throughput_ops_sec'].mean().sort_values(ascending=False)
            f.write(f"   Performance Ranking: {' > '.join(op_ranking.index)}\n")
        
        f.write("\n\nKEY INSIGHTS:\n")
        f.write("=" * 15 + "\n")
        
        # Overall winner
        overall_winner = cache_summary[0]['cache']
        f.write(f"• Overall Best Cache: {overall_winner}\n")
        
        # Best for different access patterns
        seq_data = df[df['operation'] == 'search_sequential']
        seq_best = seq_data.loc[seq_data['throughput_ops_sec'].idxmax(), 'cache_type']
        f.write(f"• Best for Sequential Access: {seq_best}\n")
        
        rand_data = df[df['operation'] == 'search_random']
        rand_best = rand_data.loc[rand_data['throughput_ops_sec'].idxmax(), 'cache_type']
        f.write(f"• Best for Random Access: {rand_best}\n")
        
        zipf_data = df[df['operation'] == 'search_zipfian']
        zipf_best = zipf_data.loc[zipf_data['throughput_ops_sec'].idxmax(), 'cache_type']
        f.write(f"• Best for Zipfian Access: {zipf_best}\n")
        
        # Cache efficiency
        hit_ratio_winner = df.groupby('cache_type')['cache_hit_ratio'].mean().idxmax()
        f.write(f"• Highest Cache Hit Ratio: {hit_ratio_winner}\n")
        
        # CPU efficiency
        ipc_winner = df.groupby('cache_type')['ipc'].mean().idxmax()
        f.write(f"• Most CPU Efficient: {ipc_winner}\n")
        
        # Most consistent
        consistency_scores = {}
        for cache in df['cache_type'].unique():
            cache_data = df[df['cache_type'] == cache]['throughput_ops_sec']
            consistency_scores[cache] = cache_data.std() / cache_data.mean()
        most_consistent = min(consistency_scores, key=consistency_scores.get)
        f.write(f"• Most Consistent Performance: {most_consistent}\n")
        
        f.write("\n\nRECOMMendations:\n")
        f.write("=" * 17 + "\n")
        
        f.write(f"• For general-purpose workloads: Use {overall_winner}\n")
        f.write(f"• For sequential access patterns: Use {seq_best}\n")
        f.write(f"• For random access patterns: Use {rand_best}\n")
        f.write(f"• For skewed access patterns: Use {zipf_best}\n")
        f.write(f"• For predictable performance: Use {most_consistent}\n")
        
        # Performance differences
        best_perf = cache_summary[0]['avg_throughput']
        worst_perf = cache_summary[-1]['avg_throughput']
        improvement = ((best_perf - worst_perf) / worst_perf) * 100
        f.write(f"• Performance improvement from best to worst cache: {improvement:.1f}%\n")
    
    print(f"✓ Generated: analysis_summary.txt")

def main():
    """Main function to generate all plots"""
    # Configuration
    csv_file = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250922_123326/combined_benchmark_results_with_perf_20250922_132611.csv"
    output_dir = "/home/skarim/Code/haldendb_ex/haldendb/benchmark/plots"
    
    print("Cache Benchmark Analysis - Generating Basic Plots")
    print("=" * 55)
    
    # Load and prepare data
    df = load_and_prepare_data(csv_file)
    
    # Generate all plots
    plot_functions = [
        plot_1_throughput_comparison,
        plot_2_cache_efficiency,
        plot_3_hardware_performance,
        plot_4_operation_analysis,
        plot_5_correlation_and_pca,
        plot_6_summary_dashboard
    ]
    
    print(f"\nGenerating {len(plot_functions)} plots...")
    print("-" * 35)
    
    for plot_func in plot_functions:
        try:
            plot_func(df, output_dir)
        except Exception as e:
            print(f"✗ Error generating {plot_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    # Generate summary report
    generate_summary_report(df, output_dir)
    
    print("\n" + "=" * 55)
    print("All plots generated successfully!")
    print(f"Output directory: {output_dir}")
    print("=" * 55)

if __name__ == "__main__":
    main()