"""Exercise the unchanged project examples with explicit offline C++ fixtures.

These fixtures test compiler/validator integration, not live model quality.
"""
from pathlib import Path
import shutil

import pytest

from optimizer.compile import compile_and_test
from optimizer.validation import validate_candidate

ROOT = Path(__file__).resolve().parents[1]
PRIMES_CPP = r'''
#include <iostream>
long long count_primes(long long limit) {
    long long count = 0;
    for (long long number = 2; number < limit; ++number) {
        bool prime = true;
        for (long long divisor = 2; divisor * divisor <= number; ++divisor) {
            if (number % divisor == 0) { prime = false; break; }
        }
        if (prime) ++count;
    }
    return count;
}
int main() { std::cout << count_primes(150000) << "\n"; }
'''
BFS_CPP = r'''
#include <iostream>
#include <queue>
#include <vector>
long long heavy_bfs(int target_depth) {
    long long count = 0;
    for (int repeat = 0; repeat < 2000; ++repeat) {
        std::queue<int> queue;
        queue.push(0);
        std::vector<bool> visited(target_depth, false);
        while (!queue.empty()) {
            int node = queue.front(); queue.pop();
            if (!visited[node]) {
                visited[node] = true;
                ++count;
                if (node + 1 < target_depth) queue.push(node + 1);
                if (node + 2 < target_depth) queue.push(node + 2);
            }
        }
    }
    return count;
}
int main() { std::cout << heavy_bfs(800) << "\n"; }
'''


@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ is required")
@pytest.mark.parametrize("filename,cpp", [("matrix_mult.py", PRIMES_CPP), ("bfs.py", BFS_CPP)])
def test_unchanged_examples_match_at_default_and_multiple_inputs(tmp_path, filename, cpp):
    source = tmp_path / "candidate.cpp"
    binary = tmp_path / "candidate.exe"
    source.write_text(cpp, encoding="utf-8")
    success, message = compile_and_test(source, binary)
    assert success, message
    result = validate_candidate(ROOT / "examples" / filename, source, binary)
    assert result.success, result.feedback
    assert result.coverage == "baseline+integer-functions"
    assert result.case_count >= 8
