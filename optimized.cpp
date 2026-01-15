#include <iostream>
#include <vector>
#include <cstdint>
#include <climits>
#include <chrono>

const uint32_t LCG_A = 1664525;
const uint32_t LCG_C = 1013904223;

void lcg_next(uint32_t& seed) {
    seed = LCG_A * seed + LCG_C;
}

int64_t max_subarray_sum(int n, uint32_t seed, int min_val, int max_val) {
    std::vector<int64_t> random_numbers(n);
    int range = max_val - min_val + 1;
    uint32_t array_seed = seed;
    
    for (int i = 0; i < n; ++i) {
        lcg_next(array_seed);
        random_numbers[i] = (array_seed % range) + min_val;
    }
    
    int64_t max_sum = INT64_MIN;
    
    for (int i = 0; i < n; ++i) {
        int64_t current_sum = 0;
        for (int j = i; j < n; ++j) {
            current_sum += random_numbers[j];
            if (current_sum > max_sum) max_sum = current_sum;
        }
    }
    
    return max_sum;
}

int64_t total_max_subarray_sum(int n, uint32_t initial_seed, int min_val, int max_val) {
    int64_t total_sum = 0;
    uint32_t outer_seed = initial_seed;
    
    for (int iter = 0; iter < 20; ++iter) {
        lcg_next(outer_seed);
        uint32_t seed_for_run = outer_seed;
        total_sum += max_subarray_sum(n, seed_for_run, min_val, max_val);
    }
    
    return total_sum;
}

int main() {
    int n = 10000;
    uint32_t initial_seed = 42;
    int min_val = -10;
    int max_val = 10;

    auto start_time = std::chrono::high_resolution_clock::now();
    int64_t result = total_max_subarray_sum(n, initial_seed, min_val, max_val);
    auto end_time = std::chrono::high_resolution_clock::now();
    
    std::cout << "Total Maximum Subarray Sum (20 runs): " << result << std::endl;
    std::cout << "Execution Time: " 
              << std::chrono::duration_cast<std::chrono::duration<double>>(end_time - start_time).count()
              << " seconds" << std::endl;
    
    return 0;
}