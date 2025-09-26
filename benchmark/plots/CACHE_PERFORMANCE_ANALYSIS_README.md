# Cache Performance Analysis: Version 1 vs Version 2

This directory contains comprehensive tools for analyzing cache performance differences between Version 1 and Version 2 variants of your database system. The analysis focuses on five key metrics:

- **Cache Hits**: Number of successful cache lookups
- **Cache Misses**: Number of failed cache lookups  
- **Instructions**: Total CPU instructions executed
- **User Time**: Time spent in user space
- **System Time**: Time spent in kernel space

## Available Visualization Types

### 1. Multi-Metric Dashboard (`cache_performance_comparison.py`)

**What it shows:**
- Side-by-side comparison of all 5 metrics across storage types
- Grouped bar charts with error bars and pattern-based styling
- Percentage improvement annotations
- Separate subplots for each metric and storage type
- **Layout**: 5×3 grid (metrics as rows, storage types as columns)

**Visual Style:**
- **Patterns**: Version 1 (1T: `///`, 4T: `\\\`), Version 2 (1T: `...`, 4T: `xxx`)
- **Fonts**: Large, professional sizing matching throughput comparison plots
- **Legend**: Top-left corner of first subplot in single-column format
- **Annotations**: Vertical percentage improvements for better readability
- **Units**: Full descriptive names (Millions, Billions, Seconds) instead of abbreviations

**Best for:**
- Detailed metric-by-metric analysis
- Identifying which specific metrics improved most
- Comparing performance across different storage types and thread counts

**Outputs:**
- Main dashboard: `*_comparison.pdf`
- Improvement heatmap: `*_comparison_heatmap.pdf`

### 2. Radar/Spider Charts (`cache_performance_radar.py`)

**What it shows:**
- Multi-dimensional comparison on radar charts
- All 5 metrics displayed simultaneously on each chart
- Normalized values (0-1 scale) for fair comparison
- Separate charts for each cache policy and storage combination

**Best for:**
- Holistic performance comparison
- Identifying overall performance patterns
- Spotting configurations with balanced improvements

**Outputs:**
- Detailed radar charts: `*_radar.pdf`
- Summary radar charts: `*_radar_summary.pdf`

### 3. Difference Analysis (`cache_performance_differences.py`)

**What it shows:**
- Absolute differences (raw metric changes)
- Relative differences (percentage changes)
- Improvement vs regression analysis
- Summary statistics and counts

**Best for:**
- Quantifying exact improvements/regressions
- Understanding the magnitude of changes
- Statistical analysis of optimization effectiveness

**Outputs:**
- Difference plots: `*_differences.pdf`
- Summary analysis: `*_differences_summary.pdf`
- Statistics table: `*_differences_summary.csv`

## Usage Examples

### Generate All Visualizations
```bash
cd /home/skarim/Code/haldendb_ex/haldendb/benchmark/plots

python generate_cache_performance_analysis.py \
    --vanilla-csv /path/to/vanilla/results.csv \
    --optimized-csv /path/to/optimized/results.csv \
    --output-prefix my_analysis
```

### Generate Specific Visualization Types
```bash
# Only dashboard
python generate_cache_performance_analysis.py \
    --vanilla-csv /path/to/vanilla/results.csv \
    --optimized-csv /path/to/optimized/results.csv \
    --plots dashboard

# Multiple specific types
python generate_cache_performance_analysis.py \
    --vanilla-csv /path/to/vanilla/results.csv \
    --optimized-csv /path/to/optimized/results.csv \
    --plots dashboard radar
```

### Run Individual Scripts
```bash
# Multi-metric dashboard
python cache_performance_comparison.py \
    --vanilla-csv /path/to/vanilla/results.csv \
    --optimized-csv /path/to/optimized/results.csv \
    --output dashboard_output.pdf

# Radar charts
python cache_performance_radar.py \
    --vanilla-csv /path/to/vanilla/results.csv \
    --optimized-csv /path/to/optimized/results.csv \
    --output radar_output.pdf \
    --plot-type both

# Difference analysis
python cache_performance_differences.py \
    --vanilla-csv /path/to/vanilla/results.csv \
    --optimized-csv /path/to/optimized/results.csv \
    --output differences_output.pdf
```

## Your Current Command Integration

You can easily integrate these new visualizations with your existing workflow:

```bash
# Your current command
cd /home/skarim/Code/haldendb_ex/haldendb/benchmark/plots && python option1_overlay_comparison.py \
    --vanilla-csv /home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250924_171318/combined_benchmark_results_with_perf_20250924_220907.csv \
    --optimized-csv /home/skarim/Code/haldendb_ex/haldendb_pvt/benchmark/build/cache_profiling_results_20250925_004057_default_configs_only/combined_benchmark_results_with_perf_20250925_151521.csv

# Add cache performance analysis
python generate_cache_performance_analysis.py \
    --vanilla-csv /home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250924_171318/combined_benchmark_results_with_perf_20250924_220907.csv \
    --optimized-csv /home/skarim/Code/haldendb_ex/haldendb_pvt/benchmark/build/cache_profiling_results_20250925_004057_default_configs_only/combined_benchmark_results_with_perf_20250925_151521.csv \
    --output-prefix cache_analysis_$(date +%Y%m%d)
```

## Interpretation Guide

### Dashboard Plots
- **Green annotations**: Improvements (positive for cache hits, negative for other metrics)
- **Red annotations**: Regressions
- **Error bars**: Standard deviation across multiple runs
- **Y-axis scaling**: Automatically scaled for readability (M = millions, B = billions)

### Radar Charts
- **Larger area**: Better overall performance
- **Balanced shape**: Consistent improvements across all metrics
- **Spiky shape**: Some metrics improved significantly, others didn't

### Difference Plots
- **Positive bars**: Optimized > Vanilla (good for cache hits, bad for others)
- **Negative bars**: Optimized < Vanilla (bad for cache hits, good for others)
- **Percentage values**: Relative improvement/regression magnitude

## Recommended Analysis Workflow

1. **Start with Dashboard**: Get detailed metric-by-metric view
2. **Use Radar Charts**: Identify best overall configurations
3. **Analyze Differences**: Quantify improvements and understand trade-offs
4. **Cross-reference**: Compare findings across all three visualization types

## Customization Options

Each script supports various customization options:

- `--plot-type`: Choose specific plot variants
- `--output`: Specify output file names
- Color schemes and styling can be modified in the script files
- Metric selection and scaling can be adjusted in the configuration sections

## Troubleshooting

**Common Issues:**
- **No data found**: Check that CSV files contain the required columns
- **Missing metrics**: Ensure both CSV files have the same column names
- **Memory issues**: For large datasets, consider filtering data first

**Required Columns:**
- Vanilla CSV: `cache_hits`, `cache_misses`, `perf_instructions`, `perf_user_time`, `perf_sys_time`
- Optimized CSV: Same columns (with potential name mapping handled automatically)

## Output Files Summary

When you run the complete analysis, you'll get:

1. **Dashboard Analysis**:
   - `*_comparison.pdf`: Main multi-metric dashboard
   - `*_comparison_heatmap.pdf`: Improvement heatmap

2. **Radar Analysis**:
   - `*_radar.pdf`: Detailed radar charts by configuration
   - `*_radar_summary.pdf`: Summary radar charts by storage type

3. **Difference Analysis**:
   - `*_differences.pdf`: Absolute and relative difference plots
   - `*_differences_summary.pdf`: Improvement/regression summary
   - `*_differences_summary.csv`: Statistical summary table

This comprehensive analysis will give you deep insights into how your optimizations affect cache performance and system resource usage across different configurations.