cmake_minimum_required(VERSION 3.10)

project(haldendb_benchmark VERSION 1.0)

# Set C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(glog 0.7.0 REQUIRED)

# Set build type to Release by default
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Create compiler flags interface library
add_library(haldendb_compiler_flags INTERFACE)
target_compile_features(haldendb_compiler_flags INTERFACE cxx_std_20)

# Add compile definitions based on build configuration
# These can be overridden by command line -DCMAKE_CXX_FLAGS
add_compile_definitions(__TREE_WITH_CACHE__)

# Conditionally add other definitions
if(ENABLE_CONCURRENT)
    add_compile_definitions(__CONCURRENT__)
endif()

if(ENABLE_TRACK_FOOTPRINT)
    add_compile_definitions(__TRACK_CACHE_FOOTPRINT__)
endif()

if(ENABLE_VALIDITY_CHECK)
    add_compile_definitions(__VALIDITY_CHECK__)
endif()

# Add subdirectories for libraries
add_subdirectory(../libcache ${PROJECT_BINARY_DIR}/libcache)
add_subdirectory(../libbtree ${PROJECT_BINARY_DIR}/libbtree)

# Set compiler
set(CMAKE_CXX_COMPILER g++)

# Create benchmark executable
add_executable(benchmark benchmark.cpp)

# Set target properties
set_target_properties(benchmark PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
)

# Compiler-specific optimizations for Release builds
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    target_compile_options(benchmark PRIVATE
        -O3
        -DNDEBUG
        -march=native
        -mtune=native
        -Wall
        -Wextra
        -Wno-unused-parameter
        -Wno-switch
        -Wno-unused-variable
        -Wno-class-memaccess
        -Wno-sign-compare
    )
elseif(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_compile_options(benchmark PRIVATE
        -O0
        -g3
        -ggdb3
        -Wall
        -Wextra
        -DDEBUG
    )
endif()

# Link libraries
target_link_libraries(benchmark PUBLIC 
    libcache 
    libbtree 
    haldendb_compiler_flags
    glog::glog
)

# Include directories
target_include_directories(benchmark PUBLIC
    "${PROJECT_BINARY_DIR}"
    "${PROJECT_SOURCE_DIR}/../libcache"
    "${PROJECT_SOURCE_DIR}/../libbtree"
    "${PROJECT_SOURCE_DIR}"
)

# Add custom targets for different build configurations

# Non-concurrent default configuration
add_custom_target(build_non_concurrent_default
    COMMAND ${CMAKE_COMMAND} -DCMAKE_BUILD_TYPE=Release 
            -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -O3 -DNDEBUG -march=native -mtune=native" 
            ${CMAKE_SOURCE_DIR}
    COMMAND ${CMAKE_COMMAND} --build . --target benchmark
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
    COMMENT "Building non-concurrent default configuration"
)

# Non-concurrent with footprint tracking
add_custom_target(build_non_concurrent_track_footprint
    COMMAND ${CMAKE_COMMAND} -DCMAKE_BUILD_TYPE=Release 
            -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -D__TRACK_CACHE_FOOTPRINT__ -O3 -DNDEBUG -march=native -mtune=native" 
            ${CMAKE_SOURCE_DIR}
    COMMAND ${CMAKE_COMMAND} --build . --target benchmark
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
    COMMENT "Building non-concurrent with footprint tracking configuration"
)

# Concurrent default configuration
add_custom_target(build_concurrent_default
    COMMAND ${CMAKE_COMMAND} -DCMAKE_BUILD_TYPE=Release 
            -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -D__CONCURRENT__ -O3 -DNDEBUG -march=native -mtune=native" 
            ${CMAKE_SOURCE_DIR}
    COMMAND ${CMAKE_COMMAND} --build . --target benchmark
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
    COMMENT "Building concurrent default configuration"
)

# Concurrent with footprint tracking
add_custom_target(build_concurrent_track_footprint
    COMMAND ${CMAKE_COMMAND} -DCMAKE_BUILD_TYPE=Release 
            -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -D__CONCURRENT__ -D__TRACK_CACHE_FOOTPRINT__ -O3 -DNDEBUG -march=native -mtune=native" 
            ${CMAKE_SOURCE_DIR}
    COMMAND ${CMAKE_COMMAND} --build . --target benchmark
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
    COMMENT "Building concurrent with footprint tracking configuration"
)

# Debug configuration
add_custom_target(build_debug
    COMMAND ${CMAKE_COMMAND} -DCMAKE_BUILD_TYPE=Debug 
            -DCMAKE_CXX_FLAGS="-D__TREE_WITH_CACHE__ -D__VALIDITY_CHECK__ -O0 -g3 -ggdb3" 
            ${CMAKE_SOURCE_DIR}
    COMMAND ${CMAKE_COMMAND} --build . --target benchmark
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
    COMMENT "Building debug configuration"
)

# Print configuration information
message(STATUS "=== HaldenDB Benchmark Configuration ===")
message(STATUS "Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "C++ compiler: ${CMAKE_CXX_COMPILER}")
message(STATUS "C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "Source directory: ${CMAKE_SOURCE_DIR}")
message(STATUS "Binary directory: ${CMAKE_BINARY_DIR}")

# Print available custom targets
message(STATUS "")
message(STATUS "Available build targets:")
message(STATUS "  benchmark                          - Build with current configuration")
message(STATUS "  build_non_concurrent_default       - Build non-concurrent default")
message(STATUS "  build_non_concurrent_track_footprint - Build non-concurrent with footprint tracking")
message(STATUS "  build_concurrent_default           - Build concurrent default")
message(STATUS "  build_concurrent_track_footprint   - Build concurrent with footprint tracking")
message(STATUS "  build_debug                        - Build debug configuration")
message(STATUS "========================================")

# Installation rules (optional)
install(TARGETS benchmark
    RUNTIME DESTINATION bin
)

# Create build directory structure
file(MAKE_DIRECTORY ${CMAKE_BINARY_DIR}/results)
file(MAKE_DIRECTORY ${CMAKE_BINARY_DIR}/logs)