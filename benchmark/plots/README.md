# Performance Visualization Scripts

This directory contains scripts to generate comprehensive performance visualizations comparing Version 1 (vanilla) and Version 2 (optimized) of the HaldenDB benchmark results.

## Available Visualizations

### 1. Throughput Comparison (Option 1)
**Script:** `option1_overlay_comparison.py`
**Output:** Shows throughput improvements with speedup annotations
- Grouped bar charts for different storage types (NVDIMM, NVM, SSD NVMe)
- Compares Version 1 vs Version 2 across cache types (A2Q, ARC, CLOCK, LRU)
- Shows speedup multipliers (e.g., 2.1x, 3.5x) above optimized bars
- Focuses on operations per second performance

### 2. Detailed Metrics Analysis (Option 2)
**Script:** `option2_detailed_metrics.py`
**Output:** Comprehensive analysis of cache and system metrics
- **Cache Hit Ratio:** Shows cache efficiency improvements
- **Instructions per Operation:** CPU instruction count analysis
- **User CPU Time:** Time spent in user space
- **System CPU Time:** Time spent in kernel space
- All metrics show improvement ratios and differences

### 3. Comprehensive Dashboard
**Script:** `cache_and_performance_metrics.py --plot-type dashboard`
**Output:** Single-page overview of all key metrics
- Combines throughput, cache metrics, and system metrics
- Focused on SSD NVMe storage (most common use case)
- Shows improvement ratios for each metric
- Ideal for executive summaries

### 4. Separate Cache Metrics
**Script:** `cache_and_performance_metrics.py --plot-type cache`
**Output:** Detailed cache hits vs misses analysis
- Separate plots for cache hits and cache misses
- Across all storage types and cache policies
- Shows absolute numbers and trends

### 5. Separate Performance Metrics
**Script:** `cache_and_performance_metrics.py --plot-type performance`
**Output:** Detailed system performance analysis
- Instructions, user time, and system time
- Across all storage types and cache policies
- Shows resource utilization patterns

## Usage Examples

### Generate Individual Plots

```bash
# Throughput comparison (your current script)
python option1_overlay_comparison.py \
  --vanilla-csv /path/to/vanilla/results.csv \
  --optimized-csv /path/to/optimized/results.csv \
  --output throughput_comparison.pdf

# Detailed metrics analysis
python option2_detailed_metrics.py \
  --vanilla-csv /path/to/vanilla/results.csv \
  --optimized-csv /path/to/optimized/results.csv \
  --output detailed_metrics.pdf

# Comprehensive dashboard
python cache_and_performance_metrics.py \
  --vanilla-csv /path/to/vanilla/results.csv \
  --optimized-csv /path/to/optimized/results.csv \
  --plot-type dashboard \
  --output-dir ./plots/
```

### Generate All Plots at Once

```bash
python generate_all_plots.py \
  --vanilla-csv /path/to/vanilla/results.csv \
  --optimized-csv /path/to/optimized/results.csv \
  --output-dir ./all_plots/
```

### Your Current Command (Enhanced)

```bash
# Your existing throughput plot
cd /home/skarim/Code/haldendb_ex/haldendb/benchmark/plots && \
python option1_overlay_comparison.py \
  --vanilla-csv /home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250924_171318/combined_benchmark_results_with_perf_20250924_220907.csv \
  --optimized-csv /home/skarim/Code/haldendb_ex/haldendb_pvt/benchmark/build/cache_profiling_results_20250925_004057_default_configs_only/combined_benchmark_results_with_perf_20250925_151521.csv

# Add detailed metrics analysis
python option2_detailed_metrics.py \
  --vanilla-csv /home/skarim/Code/haldendb_ex/haldendb/benchmark/build/cache_profiling_results_20250924_171318/combined_benchmark_results_with_perf_20250924_220907.csv \
  --optimized-csv /home/skarim/Code/haldendb_ex/haldendb_pvt/benchmark/build/cache_profiling_results_20250925_004057_default_configs_only/combined_benchmark_results_with_perf_20250925_151521.csv
```

## Presentation Recommendations

### For Technical Audiences
1. **Start with Option 1** (throughput) to show the main performance gains
2. **Follow with Option 2** (detailed metrics) to explain WHY the improvements occurred
3. **Use separate cache/performance plots** for deep-dive discussions

### For Executive/Business Audiences
1. **Use the Dashboard** for a single-slide overview
2. **Highlight key speedup numbers** from the throughput plot
3. **Show cache efficiency improvements** to demonstrate optimization effectiveness

### For Academic/Research Presentations
1. **Present all visualizations** to show comprehensive analysis
2. **Use detailed metrics** to support claims about optimization effectiveness
3. **Include methodology discussion** about measurement techniques

## Key Metrics Explained

- **Cache Hit Ratio:** Higher is better (more data found in cache)
- **Cache Misses:** Lower is better (fewer expensive disk/memory accesses)
- **Instructions:** Lower is better (more efficient code execution)
- **User Time:** Lower is better (less CPU time in application code)
- **System Time:** Lower is better (less CPU time in kernel/OS code)
- **Throughput:** Higher is better (more operations per second)

## Output Files

All scripts generate PDF files optimized for:
- High-resolution printing (300 DPI)
- Professional presentations
- Academic publications
- Technical documentation

The plots use colorblind-friendly color schemes and clear typography for accessibility.