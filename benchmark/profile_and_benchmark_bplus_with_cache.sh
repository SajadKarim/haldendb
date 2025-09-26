#!/bin/bash

# BPlusStore Cache Profiling Benchmark Script
# This script runs comprehensive cache benchmarks with different cache types, storage types, and parameters
# Adapted for BPlusStore with LRU, SSARC, and CLOCK cache implementations
#
# Environment Variables:
# - THREADS: Array of thread counts for concurrent operations (default: defined in script)

# Configuration
BENCHMARK_DIR="/home/skarim/workspace/code/haldendb_old/haldendb/benchmark/build"
BENCHMARK_EXEC="$BENCHMARK_DIR/benchmark"

# Create timestamped output directory
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PROFILE_OUTPUT_DIR="$BENCHMARK_DIR/cache_profiling_results_${TIMESTAMP}"

# Create output directory
mkdir -p "$PROFILE_OUTPUT_DIR"

echo "=========================================="
echo "BPlusStore Cache Profiling Results Directory: $PROFILE_OUTPUT_DIR"
echo "=========================================="

# Cache-specific configuration arrays
CACHE_TYPES=("LRU" "SSARC" "CLOCK")  # CLOCK cache now enabled and fixed
STORAGE_TYPES=("VolatileStorage")
CACHE_SIZE_PERCENTAGES=("5%")  # Cache sizes as percentages of estimated B+ tree pages
PAGE_SIZES=(4096)
MEMORY_SIZES=(4294967296)  # 1GB default

# Tree types to test (BPlusStore configurations)
TREES=("BPlusStore")

# Degrees to test
DEGREES=(64)

# Operations to profile
OPERATIONS=("insert" "search_random" "search_sequential" "search_uniform" "search_zipfian" "delete")

# Key-Value type combinations
declare -A KEY_VALUE_COMBOS
#KEY_VALUE_COMBOS["int_int"]="int int"
KEY_VALUE_COMBOS["uint64_t_uint64_t"]="uint64_t uint64_t"
#KEY_VALUE_COMBOS["char16_char16"]="char16 char16"
#KEY_VALUE_COMBOS["uint64_t_char16"]="uint64_t char16"

# Record count for profiling
RECORDS=(500000)
RUNS=${RUNS:-3}  # Default to 3, but allow override via environment variable
THREADS=(4)

# Perf events to collect (cache-focused)
PERF_EVENTS="cache-misses,cache-references,cycles,instructions,branch-misses,page-faults,L1-dcache-load-misses,L1-dcache-loads,LLC-load-misses,LLC-loads"

# Function to calculate actual cache size from percentage and estimated page count
calculate_cache_size() {
    local percentage=$1
    local record_count=$2
    local degree=${3:-64}  # Default degree if not provided
    
    # Remove the % symbol and convert to decimal
    local percent_value=${percentage%\%}
    
    # Estimate the number of pages in the B+ tree
    # For a B+ tree with degree d:
    # - Leaf pages: approximately record_count / (d-1) 
    # - Internal pages: approximately leaf_pages / d (for each level)
    # - Total pages is roughly 1.1 to 1.2 times the leaf pages (accounting for internal nodes)
    
    local leaf_pages=$((record_count / (degree - 1)))
    if [ $leaf_pages -lt 1 ]; then
        leaf_pages=1
    fi
    
    # Estimate total pages (leaf + internal nodes)
    # Using a conservative multiplier of 1.15 for internal nodes
    local estimated_total_pages=$((leaf_pages * 115 / 100))
    
    # Calculate cache size as percentage of estimated total pages
    local cache_size=$((estimated_total_pages * percent_value / 100))
    
    # Ensure minimum cache size for meaningful testing
    if [ $cache_size -lt 10 ]; then
        cache_size=10
    fi
    
    # Ensure cache size doesn't exceed total estimated pages (would give 100% hit ratio)
    if [ $cache_size -gt $estimated_total_pages ]; then
        cache_size=$estimated_total_pages
    fi
    
    echo $cache_size
}

# Function to build with cache support
build_cache_configuration() {
    local config_type=$1  # "non_concurrent" or "concurrent"
    
    echo "========================================="
    echo "Building BPlusStore Cache Configuration: $config_type"
    echo "========================================="
    
    cd "$BENCHMARK_DIR"
    
    # Clean previous build
    make clean > /dev/null 2>&1
    
    # Define optimization flags for Release builds
    local RELEASE_OPTS="-O3 -DNDEBUG -march=native"

    # Configure and build based on type
    if [ "$config_type" = "non_concurrent_default" ]; then
        echo "Building with cache + non_concurrent_default + cache counters ..."
        cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -D__CACHE_COUNTERS__ $RELEASE_OPTS"
    elif [ "$config_type" = "concurrent_default" ]; then
        echo "Building with cache + concurrent_default + cache counters ..."
        cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -D__CONCURRENT__ -D__CACHE_COUNTERS__ $RELEASE_OPTS"
    else
        echo "Building with cache + default + cache counters ..."
        cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -D__CACHE_COUNTERS__ $RELEASE_OPTS"
    fi
    
    make -j$(nproc)
    
    if [ $? -eq 0 ]; then
        echo "Build completed successfully for $config_type cache configuration"
    else
        echo "Build failed for $config_type cache configuration"
        exit 1
    fi
    
    cd - > /dev/null
    echo ""
}

# Function to run single cache benchmark with perf profiling
run_cache_profiled_benchmark() {
    local tree_type=$1
    local cache_type=$2
    local storage_type=$3
    local cache_size=$4
    local page_size=$5
    local memory_size=$6
    local key_type=$7
    local value_type=$8
    local operation=$9
    local degree=${10}
    local records=${11}
    local config_name=${12}
    local thread_count=${13}
    
    local profile_name="${tree_type}_${cache_type}_${storage_type}_${cache_size}_${page_size}_${memory_size}_${key_type}_${value_type}_${operation}_${degree}_${records}_threads${thread_count}"
    
    # Create a separate folder for this individual run
    local run_folder="$PROFILE_OUTPUT_DIR/${config_name}_${profile_name}"
    mkdir -p "$run_folder"
    
    local perf_output="$run_folder/${config_name}_${profile_name}.prf"
    local perf_data="$run_folder/${config_name}_${profile_name}.data"
    
    echo "=========================================="
    echo "BPlusStore Cache Profiling: $tree_type - $operation - Degree $degree"
    echo "Cache: $cache_type (Size: $cache_size), Storage: $storage_type"
    echo "Page Size: $page_size, Memory Size: $memory_size"
    echo "Key: $key_type, Value: $value_type, Records: $records"
    echo "Threads: $thread_count"
    echo "Run Folder: $run_folder"
    echo "Output: $perf_output"
    echo "=========================================="
    
    # Run benchmark (simplified without perf for now)
    cd "$BENCHMARK_DIR"
    ./benchmark \
        --config "bm_cache" \
        --cache-type "$cache_type" \
        --storage-type "$storage_type" \
        --cache-size "$cache_size" \
        --page-size "$page_size" \
        --memory-size "$memory_size" \
        --tree-type "$tree_type" \
        --key-type "$key_type" \
        --value-type "$value_type" \
        --operation "$operation" \
        --degree "$degree" \
        --records "$records" \
        --runs "$RUNS" \
        --threads "$thread_count" \
        --output-dir "$run_folder" \
        --config-name "$config_name"
    
    # Save basic performance info to perf output file for compatibility
    echo "# Benchmark completed at $(date)" > "$perf_output"
    echo "# Command: ./benchmark --config bm_cache --cache-type $cache_type --storage-type $storage_type --cache-size $cache_size --operation $operation --degree $degree --records $records --runs $RUNS --threads $thread_count" >> "$perf_output"
    
    # Also run with perf record for detailed analysis (optional)
    if [ "$DETAILED_PROFILING" = "true" ]; then
        echo "Running detailed profiling with perf record..."
        echo "# Detailed profiling disabled for now due to perf issues" > "$perf_data"
        echo "# Enable by fixing perf command in script" >> "$perf_data"
    fi
    
    # Rename the CSV file to match the perf file naming convention
    local latest_csv=$(ls -t "$run_folder"/benchmark_*.csv 2>/dev/null | head -1)
    if [ -f "$latest_csv" ]; then
        local target_csv="$run_folder/${config_name}_${profile_name}.csv"
        mv "$latest_csv" "$target_csv"
        echo "CSV file renamed to: $(basename "$target_csv")"
    else
        echo "WARNING: No CSV file found in $run_folder with pattern benchmark_*.csv"
        echo "Checking for any CSV files in the directory:"
        ls -la "$run_folder"/*.csv 2>/dev/null || echo "No CSV files found at all"
    fi
    
    echo "BPlusStore cache profiling completed for $profile_name"
    
    # Brief sleep to let system settle between benchmarks
    sleep 2
    echo ""
}

# Function to run comprehensive cache profiling with custom parameters
run_full_cache_profiling_with_params() {
    local config_type=${1:-"non_concurrent_default"}
    local -n cache_types_ref=$2
    local -n storage_types_ref=$3
    local -n cache_size_percentages_ref=$4
    local -n page_sizes_ref=$5
    local -n memory_sizes_ref=$6
    local -n trees_ref=$7
    local -n degrees_ref=$8
    local -n operations_ref=$9
    local -n key_value_combos_ref=${10}
    local -n records_ref=${11}
    local config_suffix=${12:-""}
    local -n threads_ref=${13:-THREADS}
    
    echo "Starting comprehensive BPlusStore cache profiling for $config_type configuration${config_suffix:+ ($config_suffix)}..."
    echo "Cache Types: ${cache_types_ref[*]}"
    echo "Storage Types: ${storage_types_ref[*]}"
    echo "Cache Size Percentages: ${cache_size_percentages_ref[*]}"
    echo "Page Sizes: ${page_sizes_ref[*]}"
    echo "Memory Sizes: ${memory_sizes_ref[*]}"
    echo "Trees: ${trees_ref[*]}"
    echo "Degrees: ${degrees_ref[*]}"
    echo "Operations: ${operations_ref[*]}"
    echo "Records: ${records_ref[*]}"
    echo "Threads: ${threads_ref[*]}"
    echo ""
    
    # Build the appropriate configuration
    build_cache_configuration "$config_type"

    local total_combinations=0
    local current_combination=0
    
    # Calculate total combinations
    for combo_name in "${!key_value_combos_ref[@]}"; do
        IFS=' ' read -r key_type value_type <<< "${key_value_combos_ref[$combo_name]}"
        for tree in "${trees_ref[@]}"; do
            for cache_type in "${cache_types_ref[@]}"; do
                for storage_type in "${storage_types_ref[@]}"; do
                    for cache_size_percentage in "${cache_size_percentages_ref[@]}"; do
                        for page_size in "${page_sizes_ref[@]}"; do
                            for memory_size in "${memory_sizes_ref[@]}"; do
                                for degree in "${degrees_ref[@]}"; do
                                    for operation in "${operations_ref[@]}"; do
                                        for records in "${records_ref[@]}"; do
                                            for thread_count in "${threads_ref[@]}"; do
                                                ((total_combinations++))
                                            done
                                        done
                                    done
                                done
                            done
                        done
                    done
                done
            done
        done
    done
    
    echo "Total combinations to profile for $config_type${config_suffix:+ ($config_suffix)}: $total_combinations"
    echo ""
    
    # Create config-specific identifier for output files
    local config_id="${config_type}${config_suffix}"
    
    # Run profiling for each combination
    for combo_name in "${!key_value_combos_ref[@]}"; do
        IFS=' ' read -r key_type value_type <<< "${key_value_combos_ref[$combo_name]}"
        
        echo "Processing key-value combination: $key_type -> $value_type"
        
        for tree in "${trees_ref[@]}"; do
            for cache_type in "${cache_types_ref[@]}"; do
                for storage_type in "${storage_types_ref[@]}"; do
                    for cache_size_percentage in "${cache_size_percentages_ref[@]}"; do
                        for page_size in "${page_sizes_ref[@]}"; do
                            for degree in "${degrees_ref[@]}"; do
                                for records in "${records_ref[@]}"; do
                                    for memory_size in "${memory_sizes_ref[@]}"; do
                                        # Calculate actual cache size from percentage, record count, and degree
                                        local actual_cache_size=$(calculate_cache_size "$cache_size_percentage" "$records" "$degree")
                                        
                                        echo "Cache size calculation: $cache_size_percentage of estimated pages for $records records (degree $degree) = $actual_cache_size entries"                                
                                    
                                        for operation in "${operations_ref[@]}"; do
                                            for thread_count in "${threads_ref[@]}"; do
                                                ((current_combination++))
                                                echo "Progress: $current_combination/$total_combinations ($config_id)"
                                                
                                                run_cache_profiled_benchmark "$tree" "$cache_type" "$storage_type" "$actual_cache_size" "$page_size" "$memory_size" "$key_type" "$value_type" "$operation" "$degree" "$records" "$config_id" "$thread_count"
                                                
                                                # Small delay between runs to let system settle
                                                sleep 5
                                            done
                                        done
                                    done
                                done
                            done
                        done
                    done
                done
            done
        done
    done
    
    echo "=========================================="
    echo "BPlusStore cache profiling completed for $config_id!"
    echo "Results saved in: $PROFILE_OUTPUT_DIR"
    echo "Total profiles generated: $total_combinations"
    echo "=========================================="
}

# Function to run single-threaded cache profiling
run_full_cache_profiling_single_threaded() {
    # Create a local single-threaded array
    local SINGLE_THREADS=(1)
    local CACHE_TYPES_LOCAL=("LRU" "SSARC" "CLOCK")  # Test all cache types

    echo "Running single-threaded BPlusStore cache profiling..."
    echo "Using cache types: ${CACHE_TYPES_LOCAL[*]}"
    
    local config_type="non_concurrent_default"    
    run_full_cache_profiling_with_params "$config_type" CACHE_TYPES_LOCAL STORAGE_TYPES CACHE_SIZE_PERCENTAGES PAGE_SIZES MEMORY_SIZES TREES DEGREES OPERATIONS KEY_VALUE_COMBOS RECORDS "" SINGLE_THREADS
}

# Function to run multi-threaded cache profiling
run_full_cache_profiling_multi_threaded() {
    echo "Running multi-threaded BPlusStore cache profiling..."
    echo "Using threads: ${THREADS[*]}"
    
    local CACHE_TYPES_LOCAL=("LRU" "SSARC" "CLOCK")
    echo "Using cache types: ${CACHE_TYPES_LOCAL[*]}"
    
    local config_type="concurrent_default"    
    run_full_cache_profiling_with_params "$config_type" CACHE_TYPES_LOCAL STORAGE_TYPES CACHE_SIZE_PERCENTAGES PAGE_SIZES MEMORY_SIZES TREES DEGREES OPERATIONS KEY_VALUE_COMBOS RECORDS "" THREADS
}

# Function to run quick cache benchmark for all configurations
run_quick_cache_benchmark() {
    local config_type=${1:-"non_concurrent_default"}
    
    echo "=========================================="
    echo "Quick BPlusStore Cache Benchmark Run - $config_type Configuration"
    echo "=========================================="
    echo "Cache Types: ${CACHE_TYPES[*]}"
    echo "Storage Types: VolatileStorage"
    echo "Cache Sizes: 5%, 15%"
    echo "Trees: BPlusStore"
    echo "Degrees: 64, 128"
    echo "Operations: ${OPERATIONS[*]}"
    echo "Record Counts: 100000, 500000"
    echo "Key/Value Types: int/int"
    echo "Thread Counts: 1, 2, 4"
    echo "Runs per config: 1"
    
    # Build the appropriate configuration
    build_cache_configuration "$config_type"
    
    local quick_cache_percentages=("5%" "15%")
    local quick_storage_types=("VolatileStorage")
    local quick_trees=("BPlusStore")
    local quick_degrees=(64 128)
    local record_counts=(100000 500000)
    local quick_threads=(1 2 4)
    local total_combinations=$((${#CACHE_TYPES[@]} * ${#quick_storage_types[@]} * ${#quick_cache_percentages[@]} * ${#quick_trees[@]} * ${#quick_degrees[@]} * ${#OPERATIONS[@]} * ${#record_counts[@]} * ${#quick_threads[@]}))
    echo "Total combinations: $total_combinations"
    echo "=========================================="
    
    # Create consolidated CSV file
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local consolidated_csv="$PROFILE_OUTPUT_DIR/quick_cache_benchmark_${config_type}_${timestamp}.csv"
    echo "tree_type,cache_type,storage_type,cache_size,key_type,value_type,operation,record_count,degree,time_us,throughput_ops_sec,test_run_id,timestamp" > "$consolidated_csv"
    
    local current_combination=0
    local start_time=$(date +%s)
    
    for records in "${record_counts[@]}"; do
        echo ""
        echo "=== Processing Record Count: $records ==="
        
        for tree in "${quick_trees[@]}"; do
            for cache_type in "${CACHE_TYPES[@]}"; do
                for storage_type in "${quick_storage_types[@]}"; do
                    for cache_size_percentage in "${quick_cache_percentages[@]}"; do
                        local actual_cache_size=$(calculate_cache_size "$cache_size_percentage" "$records")
                        for degree in "${quick_degrees[@]}"; do
                            for operation in "${OPERATIONS[@]}"; do
                                for thread_count in "${quick_threads[@]}"; do
                                    ((current_combination++))
                                    
                                    echo "[$current_combination/$total_combinations] Testing: $tree - $cache_type/$storage_type (Cache:$actual_cache_size) - $operation - Degree $degree - Records $records - Threads $thread_count"
                                    
                                    cd "$BENCHMARK_DIR"
                                    
                                    # Run benchmark without perf profiling for speed
                                    ./benchmark \\
                                        --config "bm_cache" \\
                                        --cache-type "$cache_type" \\
                                        --storage-type "$storage_type" \\
                                        --cache-size "$actual_cache_size" \\
                                        --tree-type "$tree" \\
                                        --key-type "int" \\
                                        --value-type "int" \\
                                        --operation "$operation" \\
                                        --degree "$degree" \\
                                        --records "$records" \\
                                        --runs 1 \\
                                        --threads "$thread_count" > /dev/null 2>&1
                                
                                    # Find the most recent CSV file and append to consolidated results
                                    local latest_csv=$(ls -t benchmark_*.csv 2>/dev/null | head -1)
                                    if [ -f "$latest_csv" ]; then
                                        # Skip header and append data
                                        tail -n +2 "$latest_csv" >> "$consolidated_csv"
                                        rm "$latest_csv"  # Clean up individual file
                                    else
                                        echo "  WARNING: No CSV output found for this configuration"
                                    fi
                                    
                                    # Small delay to let system settle
                                    sleep 0.5
                                done
                            done
                        done
                    done
                done
            done
        done
    done
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))
    
    echo ""
    echo "=========================================="
    echo "Quick BPlusStore Cache Benchmark Run Completed!"
    echo "=========================================="
    echo "Total combinations tested: $total_combinations"
    echo "Total execution time: ${minutes}m ${seconds}s"
    echo "Results saved to: $consolidated_csv"
    echo ""
}

# Function to analyze cache perf results
analyze_cache_results() {
    echo "Analyzing BPlusStore cache perf results..."
    
    # Create summary CSV
    local summary_file="$PROFILE_OUTPUT_DIR/cache_perf_summary.csv"
    echo "tree_type,cache_type,storage_type,cache_size,key_type,value_type,operation,degree,records,cache_misses,cache_references,cache_miss_rate,cycles,instructions,ipc,branch_misses,page_faults" > "$summary_file"
    
    for perf_file in "$PROFILE_OUTPUT_DIR"/*/*.prf; do
        if [ -f "$perf_file" ]; then
            # Extract configuration from filename
            local basename=$(basename "$perf_file" .prf)
            
            # Parse perf output and extract metrics
            local cache_misses=$(grep "cache-misses" "$perf_file" | awk '{print $1}' | tr -d ',')
            local cache_references=$(grep "cache-references" "$perf_file" | awk '{print $1}' | tr -d ',')
            local cycles=$(grep "cycles" "$perf_file" | awk '{print $1}' | tr -d ',')
            local instructions=$(grep "instructions" "$perf_file" | awk '{print $1}' | tr -d ',')
            local branch_misses=$(grep "branch-misses" "$perf_file" | awk '{print $1}' | tr -d ',')
            local page_faults=$(grep "page-faults" "$perf_file" | awk '{print $1}' | tr -d ',')
            
            # Calculate derived metrics
            local cache_miss_rate=0
            local ipc=0
            
            if [ -n "$cache_references" ] && [ "$cache_references" -gt 0 ]; then
                cache_miss_rate=$(echo "scale=4; $cache_misses / $cache_references * 100" | bc -l 2>/dev/null || echo "0")
            fi
            
            if [ -n "$cycles" ] && [ "$cycles" -gt 0 ]; then
                ipc=$(echo "scale=4; $instructions / $cycles" | bc -l 2>/dev/null || echo "0")
            fi
            
            # Extract configuration details from filename
            echo "$basename,$cache_misses,$cache_references,$cache_miss_rate,$cycles,$instructions,$ipc,$branch_misses,$page_faults" >> "$summary_file"
        fi
    done
    
    echo "BPlusStore cache performance analysis completed. Summary saved to: $summary_file"
}

# Function to merge all CSV files from benchmark runs into a single combined CSV file
merge_csv_files() {
    echo "=========================================="
    echo "Merging all CSV files from benchmark runs"
    echo "=========================================="
    
    # Create combined CSV file with timestamp
    local merge_timestamp=$(date +"%Y%m%d_%H%M%S")
    local combined_csv="$PROFILE_OUTPUT_DIR/combined_benchmark_results_${merge_timestamp}.csv"
    
    # Initialize header written flag
    local header_written=false
    local total_files=0
    local processed_files=0
    
    # Count total CSV files first
    echo "Scanning for CSV files in: $PROFILE_OUTPUT_DIR"
    for csv_file in "$PROFILE_OUTPUT_DIR"/*/*.csv; do
        if [ -f "$csv_file" ]; then
            ((total_files++))
        fi
    done
    
    if [ $total_files -eq 0 ]; then
        echo "No CSV files found in $PROFILE_OUTPUT_DIR"
        echo "Make sure benchmark runs have completed successfully."
        return 1
    fi
    
    echo "Found $total_files CSV files to merge"
    echo "Combined file will be saved as: $combined_csv"
    echo ""
    
    # Process each CSV file
    for csv_file in "$PROFILE_OUTPUT_DIR"/*/*.csv; do
        if [ -f "$csv_file" ]; then
            ((processed_files++))
            local folder_name=$(basename "$(dirname "$csv_file")")
            echo "Processing [$processed_files/$total_files]: $folder_name"
            
            if [ "$header_written" = false ]; then
                # Write header from first file
                head -n 1 "$csv_file" > "$combined_csv"
                header_written=true
                echo "  Header written from first file"
            fi
            
            # Append data lines (skip header)
            tail -n +2 "$csv_file" >> "$combined_csv"
            echo "  Data appended"
        fi
    done
    
    # Count total lines in combined file
    local total_lines=$(wc -l < "$combined_csv")
    local data_lines=$((total_lines - 1))  # Subtract header line
    
    echo ""
    echo "=========================================="
    echo "CSV Merge Completed Successfully!"
    echo "=========================================="
    echo "Files processed: $processed_files"
    echo "Combined file: $combined_csv"
    echo "Total lines: $total_lines (1 header + $data_lines data lines)"
    echo "=========================================="
    
    return 0
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  full                        Run comprehensive cache profiling (both single and multi-threaded)"
    echo "  single_threaded             Run single-threaded cache profiling"
    echo "  multi_threaded              Run multi-threaded cache profiling"
    echo "  quick [config_type]         Run quick cache benchmark (default: non_concurrent_default)"
    echo "  analyze                     Analyze existing perf results"
    echo "  merge                       Merge all CSV files from existing benchmark runs"
    echo "  help                        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 full                     # Full profiling with both single and multi-threaded configurations"
    echo "  $0 single_threaded          # Single-threaded profiling only"
    echo "  $0 multi_threaded           # Multi-threaded profiling only"
    echo "  $0 quick                    # Quick benchmark with default configuration"
    echo "  $0 analyze                  # Analyze existing results"
    echo "  $0 merge                    # Merge all CSV files from existing benchmark runs"
    echo ""
    echo "Environment Variables:"
    echo "  RUNS=N                      Set number of runs per configuration (default: 3)"
    echo "  DETAILED_PROFILING=true     Enable detailed perf record profiling"
    echo ""
    echo "Cache Types: ${CACHE_TYPES[*]}"
    echo "Storage Types: ${STORAGE_TYPES[*]}"
    echo "Cache Size Percentages: ${CACHE_SIZE_PERCENTAGES[*]}"
}

# Main script logic
case "${1:-full}" in
    "full")
        run_full_cache_profiling_single_threaded
        run_full_cache_profiling_multi_threaded
        echo ""
        echo "Both single-threaded and multi-threaded profiling completed. Merging all CSV files..."
        merge_csv_files
        ;;
    "single_threaded")
        run_full_cache_profiling_single_threaded
        echo ""
        echo "Single-threaded profiling completed. Merging CSV files..."
        merge_csv_files
        analyze_cache_results
        ;;
    "multi_threaded")
        run_full_cache_profiling_multi_threaded
        echo ""
        echo "Multi-threaded profiling completed. Merging CSV files..."
        merge_csv_files
        analyze_cache_results
        ;;
    "quick")
        run_quick_cache_benchmark "${2:-non_concurrent_default}"
        ;;
    "analyze")
        analyze_cache_results
        ;;
    "merge")
        merge_csv_files
        ;;
    "help"|"-h"|"--help")
        show_usage
        ;;
    *)
        echo "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac

echo ""
echo "BPlusStore cache benchmark script completed!"
echo "Results directory: $PROFILE_OUTPUT_DIR"