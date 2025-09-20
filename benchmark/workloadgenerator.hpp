#pragma once

#include <iostream>
#include <vector>
#include <random>
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <string>
#include <numeric>
#include <cmath>
#include "common.h"

namespace workloadgenerator {

// Distribution types for data generation
enum class DistributionType {
    Random,
    Sequential,
    Zipfian,
    Uniform
};

// Generate data function similar to GENERATE_RANDOM_NUMBER_ARRAY and GENERATE_RANDOM_CHAR_ARRAY
template<typename T>
void generate_data(size_t count, DistributionType distribution, std::vector<T>& data) {
    data.resize(count);
    
    if constexpr (std::is_same_v<T, int>) {
        std::random_device rd;
        std::mt19937_64 gen(rd());
        
        switch (distribution) {
            case DistributionType::Sequential:
                for (size_t i = 0; i < count; ++i) {
                    data[i] = static_cast<int>(i + 1);
                }
                break;
            case DistributionType::Random: {
                // Generate unique random data using the pattern from GENERATE_RANDOM_NUMBER_ARRAY
                // This ensures no duplicates for insert/delete operations
                data.resize(count);
                std::iota(data.begin(), data.end(), 1); // Fill with 1, 2, 3, ..., count
                std::shuffle(data.begin(), data.end(), gen); // Shuffle to randomize order
                break;
            }
            case DistributionType::Uniform: {
                // Generate uniform distribution within the same range [1, count] as random data
                // This ensures all keys exist in the tree but may have duplicates
                std::uniform_int_distribution<int> dis(1, static_cast<int>(count));
                for (size_t i = 0; i < count; ++i) {
                    data[i] = dis(gen);
                }
                break;
            }
            case DistributionType::Zipfian: {
                // Zipfian-like distribution within the same range [1, count] as random data
                // This ensures all keys exist in the tree but with skewed access pattern
                std::uniform_real_distribution<double> uniform(0.0, 1.0);
                for (size_t i = 0; i < count; ++i) {
                    double u = uniform(gen);
                    int rank = static_cast<int>(1.0 / std::pow(u, 1.0 / 1.1));
                    data[i] = (rank - 1) % static_cast<int>(count) + 1; // Ensure range [1, count]
                }
                break;
            }
        }
    }
}

// Save data to file
template<typename T>
void save_data_to_file(const std::vector<T>& data, const std::string& filepath) {
    std::ofstream file(filepath, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Cannot create file: " + filepath);
    }
    
    size_t count = data.size();
    file.write(reinterpret_cast<const char*>(&count), sizeof(count));
    file.write(reinterpret_cast<const char*>(data.data()), count * sizeof(T));
    file.close();
}

// Load data from file
template<typename T>
std::vector<T> load_data_from_file(const std::string& filepath) {
    std::ifstream file(filepath, std::ios::binary);
    if (!file) {
        throw std::runtime_error("Cannot open file: " + filepath);
    }
    
    size_t count;
    file.read(reinterpret_cast<char*>(&count), sizeof(count));
    
    std::vector<T> data(count);
    file.read(reinterpret_cast<char*>(data.data()), count * sizeof(T));
    file.close();
    
    return data;
}

// Generate filename based on type, distribution and count
inline std::string generate_filename(const std::string& type, DistributionType distribution, size_t count) {
    std::string dist_name;
    switch (distribution) {
        case DistributionType::Random: dist_name = "random"; break;
        case DistributionType::Sequential: dist_name = "sequential"; break;
        case DistributionType::Zipfian: dist_name = "zipfian"; break;
        case DistributionType::Uniform: dist_name = "uniform"; break;
    }
    return "data/" + type + "_" + dist_name + "_" + std::to_string(count) + ".dat";
}

// Create workload for specific type and distribution
template<typename T>
void create_workload(DistributionType distribution, size_t count) {
    std::string type_name;
    if constexpr (std::is_same_v<T, int>) {
        type_name = "int";
    }
    
    std::string filename = generate_filename(type_name, distribution, count);
    
    // Check if file exists
    if (std::filesystem::exists(filename)) {
        std::cout << "File " << filename << " already exists, skipping generation." << std::endl;
        return;
    }
    
    // Create data directory if it doesn't exist
    std::filesystem::create_directories("data");
    
    // Generate data
    std::vector<T> data;
    generate_data<T>(count, distribution, data);
    
    // Save to file
    save_data_to_file(data, filename);
    std::cout << "Generated " << filename << " with " << count << " records." << std::endl;
}

// Generate all workloads for all combinations
inline void generate_all_workloads() {
    std::vector<size_t> record_counts = {100000, 500000, 1000000, 5000000, 10000000};
    std::vector<DistributionType> distributions = {
        DistributionType::Random,
        DistributionType::Sequential,
        DistributionType::Uniform,
        DistributionType::Zipfian
    };
    
    std::cout << "Generating workloads for all combinations..." << std::endl;
    
    // Generate int workloads
    for (size_t count : record_counts) {
        for (DistributionType dist : distributions) {
            create_workload<int>(dist, count);
        }
    }
    
    std::cout << "Workload generation completed." << std::endl;
}

// Load workload data for insert operations (unique random data)
template<typename T>
std::vector<T> load_insert_workload(size_t count) {
    std::string type_name;
    if constexpr (std::is_same_v<T, int>) {
        type_name = "int";
    }
    
    std::string filename = generate_filename(type_name, DistributionType::Random, count);
    
    // Check if file exists, if not generate it
    if (!std::filesystem::exists(filename)) {
        std::cout << "Workload file " << filename << " not found, generating..." << std::endl;
        create_workload<T>(DistributionType::Random, count);
    }
    
    return load_data_from_file<T>(filename);
}

// Load workload data for search operations based on distribution type
template<typename T>
std::vector<T> load_search_workload(size_t count, DistributionType distribution) {
    std::string type_name;
    if constexpr (std::is_same_v<T, int>) {
        type_name = "int";
    }
    
    std::string filename = generate_filename(type_name, distribution, count);
    
    // Check if file exists, if not generate it
    if (!std::filesystem::exists(filename)) {
        std::cout << "Workload file " << filename << " not found, generating..." << std::endl;
        create_workload<T>(distribution, count);
    }
    
    return load_data_from_file<T>(filename);
}

} // namespace workloadgenerator