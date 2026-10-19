#include <iostream>
#include <vector>
#include <numeric>
#include <algorithm>

std::vector<std::vector<int>> matrix_multiply(const std::vector<std::vector<int>>& a, const std::vector<std::vector<int>>& b) {
    int n = a.size();
    std::vector<std::vector<int>> result(n, std::vector<int>(n, 0));

    for (int i = 0; i < n; ++i) {
        for (int k = 0; k < n; ++k) {
            int aik = a[i][k];
            for (int j = 0; j < n; ++j) {
                result[i][j] += aik * b[k][j];
            }
        }
    }

    return result;
}

int main() {
    int n = 100;
    std::vector<std::vector<int>> a(n, std::vector<int>(n));
    std::vector<std::vector<int>> b(n, std::vector<int>(n));

    for (int i = 0; i < n; ++i) {
        for (int j = 0; j < n; ++j) {
            a[i][j] = i + j;
            b[i][j] = i - j;
        }
    }

    std::vector<std::vector<int>> result = matrix_multiply(a, b);
    int sum_result = std::accumulate(result.begin(), result.end(), 0, [](int a, const std::vector<int>& row) {
        return a + std::accumulate(row.begin(), row.end(), 0);
    });

    std::cout << sum_result << std::endl;

    return 0;
}