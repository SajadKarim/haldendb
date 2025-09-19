#!/bin/bash

# Build script for HaldenDB Benchmark
# This script sets up the build environment and compiles the benchmark executable

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
SOURCE_DIR="$SCRIPT_DIR"

echo "=========================================="
echo "HaldenDB Benchmark Build Script"
echo "=========================================="
echo "Source directory: $SOURCE_DIR"
echo "Build directory: $BUILD_DIR"
echo ""

# Create build directory
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Function to build with specific configuration
build_configuration() {
    local config_name=$1
    shift
    local cmake_flags=("$@")
    
    echo "Building configuration: $config_name"
    echo "CMake flags: ${cmake_flags[*]}"
    echo ""
    
    # Clean previous build
    rm -rf CMakeCache.txt CMakeFiles/
    
    # Configure with CMake
    cmake .. "${cmake_flags[@]}"
    
    # Build
    make -j$(nproc)
    
    if [ $? -eq 0 ]; then
        echo "✓ Build successful for $config_name"
        echo ""
    else
        echo "✗ Build failed for $config_name"
        exit 1
    fi
}

# Parse command line arguments
CONFIG_TYPE=${1:-"default"}

case "$CONFIG_TYPE" in
    "default"|"non_concurrent_default")
        build_configuration "non_concurrent_default" \
            -DCMAKE_BUILD_TYPE=Release \
            -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -O3 -DNDEBUG -march=native -mtune=native"
        ;;
    "non_concurrent_track_footprint")
        build_configuration "non_concurrent_track_footprint" \
            -DCMAKE_BUILD_TYPE=Release \
            -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -D__TRACK_CACHE_FOOTPRINT__ -O3 -DNDEBUG -march=native -mtune=native"
        ;;
    "concurrent_default")
        build_configuration "concurrent_default" \
            -DCMAKE_BUILD_TYPE=Release \
            -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -D__CONCURRENT__ -O3 -DNDEBUG -march=native -mtune=native"
        ;;
    "concurrent_track_footprint")
        build_configuration "concurrent_track_footprint" \
            -DCMAKE_BUILD_TYPE=Release \
            -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -D__CONCURRENT__ -D__TRACK_CACHE_FOOTPRINT__ -O3 -DNDEBUG -march=native -mtune=native"
        ;;
    "debug")
        build_configuration "debug" \
            -DCMAKE_BUILD_TYPE=Debug \
            -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -D__VALIDITY_CHECK__ -O0 -g3 -ggdb3"
        ;;
    "all")
        echo "Building all configurations..."
        echo ""
        
        build_configuration "non_concurrent_default" \
            -DCMAKE_BUILD_TYPE=Release \
            -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -O3 -DNDEBUG -march=native -mtune=native"
        
        build_configuration "non_concurrent_track_footprint" \
            -DCMAKE_BUILD_TYPE=Release \
            -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -D__TRACK_CACHE_FOOTPRINT__ -O3 -DNDEBUG -march=native -mtune=native"
        
        build_configuration "concurrent_default" \
            -DCMAKE_BUILD_TYPE=Release \
            -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -D__CONCURRENT__ -O3 -DNDEBUG -march=native -mtune=native"
        
        build_configuration "concurrent_track_footprint" \
            -DCMAKE_BUILD_TYPE=Release \
            -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -D__CONCURRENT__ -D__TRACK_CACHE_FOOTPRINT__ -O3 -DNDEBUG -march=native -mtune=native"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [CONFIGURATION]"
        echo ""
        echo "Available configurations:"
        echo "  default                           - Non-concurrent default (same as non_concurrent_default)"
        echo "  non_concurrent_default            - Non-concurrent with basic cache support"
        echo "  non_concurrent_track_footprint    - Non-concurrent with cache footprint tracking"
        echo "  concurrent_default                - Concurrent with basic cache support"
        echo "  concurrent_track_footprint        - Concurrent with cache footprint tracking"
        echo "  debug                             - Debug build with validation checks"
        echo "  all                               - Build all configurations"
        echo "  help                              - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0                                # Build default configuration"
        echo "  $0 concurrent_default             # Build concurrent configuration"
        echo "  $0 debug                          # Build debug configuration"
        echo "  $0 all                            # Build all configurations"
        exit 0
        ;;
    *)
        echo "Error: Unknown configuration '$CONFIG_TYPE'"
        echo "Run '$0 help' to see available configurations"
        exit 1
        ;;
esac

echo "=========================================="
echo "Build completed successfully!"
echo "=========================================="
echo "Executable location: $BUILD_DIR/benchmark"
echo ""
echo "To run benchmarks:"
echo "  cd $BUILD_DIR"
echo "  ./benchmark --help"
echo ""
echo "To run profiling script:"
echo "  $SOURCE_DIR/profile_and_benchmark_bplus_with_cache.sh help"
echo "=========================================="