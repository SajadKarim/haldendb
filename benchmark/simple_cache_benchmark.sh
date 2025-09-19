#!/bin/bash

# Simple BPlusStore Cache Benchmark Script (without perf profiling)
# This script runs basic cache benchmarks with different cache types and parameters

# Configuration
BENCHMARK_DIR="/home/skarim/workspace/code/haldendb_old/haldendb/benchmark/build"
BENCHMARK_EXEC="$BENCHMARK_DIR/benchmark"

# Create timestamped output directory
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_DIR="$BENCHMARK_DIR/simple_cache_results_${TIMESTAMP}"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "=========================================="
echo "Simple BPlusStore Cache Benchmark Results Directory: $OUTPUT_DIR"
echo "=========================================="

# Configuration arrays
CACHE_TYPES=("LRU" "SSARC")  # CLOCK disabled due to implementation issues
STORAGE_TYPES=("VolatileStorage")  # FileStorage disabled due to implementation issues
CACHE_SIZE_PERCENTAGES=("5%" "15%" "25%")
PAGE_SIZES=(4096)
MEMORY_SIZES=(1073741824)  # 1GB default

# Tree types to test
TREES=("BPlusStore")

# Degrees to test
DEGREES=(64 128)

# Operations to profile
OPERATIONS=("insert" "search" "delete")

# Key-Value type combinations
declare -A KEY_VALUE_COMBOS
KEY_VALUE_COMBOS["int_int"]="int int"

# Record count for profiling
RECORDS=(100000 500000)
RUNS=${RUNS:-3}  # Default to 3, but allow override via environment variable
THREADS=(1 2 4)

# Function to calculate actual cache size from percentage and record count
calculate_cache_size() {
    local percentage=$1
    local record_count=$2
    
    # Remove the % symbol and convert to decimal
    local percent_value=${percentage%\%}
    
    # Calculate cache size as percentage of record count
    local cache_size=$((record_count * percent_value / 100))
    
    # Ensure minimum cache size
    if [ $cache_size -lt 10 ]; then
        cache_size=10
    fi
    
    echo $cache_size
}

# Function to build with cache support
build_cache_configuration() {
    echo "========================================="
    echo "Building BPlusStore Cache Configuration"
    echo "========================================="
    
    cd "$BENCHMARK_DIR"
    
    # Clean previous build
    make clean > /dev/null 2>&1
    
    # Define optimization flags for Release builds
    local RELEASE_OPTS="-O3 -DNDEBUG -march=native"
    
    # Configure and build
    echo "Building with cache support..."
    cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ $RELEASE_OPTS"
    
    make -j$(nproc)
    
    if [ $? -eq 0 ]; then
        echo "Build completed successfully"
    else
        echo "Build failed"
        exit 1
    fi
    
    cd - > /dev/null
    echo ""
}

# Function to run single cache benchmark
run_cache_benchmark() {
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
    local thread_count=${12}
    
    local benchmark_name="${tree_type}_${cache_type}_${storage_type}_${cache_size}_${operation}_${degree}_${records}_threads${thread_count}"
    
    echo "=========================================="
    echo "BPlusStore Cache Benchmark: $tree_type - $operation - Degree $degree"
    echo "Cache: $cache_type (Size: $cache_size), Storage: $storage_type"
    echo "Key: $key_type, Value: $value_type, Records: $records"
    echo "Threads: $thread_count"
    echo "=========================================="
    
    # Run benchmark
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
        --output-dir "$OUTPUT_DIR" \
        --config-name "$benchmark_name"
    
    echo "Benchmark completed for $benchmark_name"
    echo ""
}

# Function to run comprehensive cache benchmarking
run_full_cache_benchmarking() {
    echo "Starting comprehensive BPlusStore cache benchmarking..."
    echo "Cache Types: ${CACHE_TYPES[*]}"
    echo "Storage Types: ${STORAGE_TYPES[*]}"
    echo "Cache Size Percentages: ${CACHE_SIZE_PERCENTAGES[*]}"
    echo "Trees: ${TREES[*]}"
    echo "Degrees: ${DEGREES[*]}"
    echo "Operations: ${OPERATIONS[*]}"
    echo "Records: ${RECORDS[*]}"
    echo "Threads: ${THREADS[*]}"
    echo ""
    
    # Build the configuration
    build_cache_configuration

    local total_combinations=0
    local current_combination=0
    
    # Calculate total combinations
    for combo_name in "${!KEY_VALUE_COMBOS[@]}"; do
        for tree in "${TREES[@]}"; do
            for cache_type in "${CACHE_TYPES[@]}"; do
                for storage_type in "${STORAGE_TYPES[@]}"; do
                    for cache_size_percentage in "${CACHE_SIZE_PERCENTAGES[@]}"; do
                        for page_size in "${PAGE_SIZES[@]}"; do
                            for memory_size in "${MEMORY_SIZES[@]}"; do
                                for degree in "${DEGREES[@]}"; do
                                    for operation in "${OPERATIONS[@]}"; do
                                        for records in "${RECORDS[@]}"; do
                                            for thread_count in "${THREADS[@]}"; do
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
    
    echo "Total combinations to benchmark: $total_combinations"
    echo ""
    
    # Run benchmarking for each combination
    for combo_name in "${!KEY_VALUE_COMBOS[@]}"; do
        IFS=' ' read -r key_type value_type <<< "${KEY_VALUE_COMBOS[$combo_name]}"
        
        echo "Processing key-value combination: $key_type -> $value_type"
        
        for tree in "${TREES[@]}"; do
            for cache_type in "${CACHE_TYPES[@]}"; do
                for storage_type in "${STORAGE_TYPES[@]}"; do
                    for cache_size_percentage in "${CACHE_SIZE_PERCENTAGES[@]}"; do
                        for page_size in "${PAGE_SIZES[@]}"; do
                            for degree in "${DEGREES[@]}"; do
                                for records in "${RECORDS[@]}"; do
                                    for memory_size in "${MEMORY_SIZES[@]}"; do
                                        # Calculate actual cache size from percentage and record count
                                        local actual_cache_size=$(calculate_cache_size "$cache_size_percentage" "$records")
                                        
                                        echo "Cache size calculation: $cache_size_percentage of $records records = $actual_cache_size entries"                                
                                    
                                        for operation in "${OPERATIONS[@]}"; do
                                            for thread_count in "${THREADS[@]}"; do
                                                ((current_combination++))
                                                echo "Progress: $current_combination/$total_combinations"
                                                
                                                run_cache_benchmark "$tree" "$cache_type" "$storage_type" "$actual_cache_size" "$page_size" "$memory_size" "$key_type" "$value_type" "$operation" "$degree" "$records" "$thread_count"
                                                
                                                # Small delay between runs to let system settle
                                                sleep 2
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
    echo "All benchmarks completed!"
    echo "Results saved in: $OUTPUT_DIR"
    echo "=========================================="
}

# Function to run quick benchmark
run_quick_benchmark() {
    echo "=========================================="
    echo "Quick BPlusStore Cache Benchmark Run"
    echo "=========================================="
    
    # Reduced configuration for quick testing
    local quick_cache_types=("LRU" "SSARC")
    local quick_storage_types=("VolatileStorage")
    local quick_cache_sizes=("5%" "15%")
    local quick_trees=("BPlusStore")
    local quick_degrees=(64)
    local quick_operations=("insert" "search")
    local quick_records=(100000)
    local quick_threads=(1)
    
    echo "Cache Types: ${quick_cache_types[*]}"
    echo "Storage Types: ${quick_storage_types[*]}"
    echo "Cache Sizes: ${quick_cache_sizes[*]}"
    echo "Trees: ${quick_trees[*]}"
    echo "Degrees: ${quick_degrees[*]}"
    echo "Operations: ${quick_operations[*]}"
    echo "Record Counts: ${quick_records[*]}"
    echo "Thread Counts: ${quick_threads[*]}"
    echo "Runs per config: $RUNS"
    echo ""
    
    # Build the configuration
    build_cache_configuration
    
    # Run quick benchmarks
    for combo_name in "${!KEY_VALUE_COMBOS[@]}"; do
        IFS=' ' read -r key_type value_type <<< "${KEY_VALUE_COMBOS[$combo_name]}"
        
        for tree in "${quick_trees[@]}"; do
            for cache_type in "${quick_cache_types[@]}"; do
                for storage_type in "${quick_storage_types[@]}"; do
                    for cache_size_percentage in "${quick_cache_sizes[@]}"; do
                        for page_size in "${PAGE_SIZES[@]}"; do
                            for degree in "${quick_degrees[@]}"; do
                                for records in "${quick_records[@]}"; do
                                    for memory_size in "${MEMORY_SIZES[@]}"; do
                                        local actual_cache_size=$(calculate_cache_size "$cache_size_percentage" "$records")
                                        
                                        for operation in "${quick_operations[@]}"; do
                                            for thread_count in "${quick_threads[@]}"; do
                                                run_cache_benchmark "$tree" "$cache_type" "$storage_type" "$actual_cache_size" "$page_size" "$memory_size" "$key_type" "$value_type" "$operation" "$degree" "$records" "$thread_count"
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
    echo "Quick benchmark completed!"
    echo "Results saved in: $OUTPUT_DIR"
    echo "=========================================="
}

# Main script logic
case "${1:-full}" in
    "quick")
        run_quick_benchmark
        ;;
    "full")
        run_full_cache_benchmarking
        ;;
    *)
        echo "Usage: $0 [quick|full]"
        echo "  quick - Run a quick benchmark with reduced parameters"
        echo "  full  - Run comprehensive benchmarking (default)"
        exit 1
        ;;
esac