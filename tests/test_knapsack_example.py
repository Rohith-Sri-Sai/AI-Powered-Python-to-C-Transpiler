"""Correctness and offline compiler checks for the knapsack workload."""
import importlib.util
from pathlib import Path

import shutil

import pytest

from optimizer.compile import compile_and_test
from optimizer.validation import validate_candidate

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "knapsack.py"

# Offline fixture, not live LLM output. Uses the same item set and 0/1 DP.
KNAPSACK_CPP = r'''
#include <cstdint>
#include <iostream>
#include <vector>
std::int64_t knapsack(std::int64_t capacity) {
    if (capacity <= 0) return 0;
    std::vector<std::int64_t> best(static_cast<std::size_t>(capacity) + 1, 0);
    for (std::int64_t item = 1; item <= 600; ++item) {
        std::int64_t weight = (item * 37) % 997 + 1;
        std::int64_t value = (item * 101) % 1009 + 1;
        for (std::int64_t budget = capacity; budget >= weight; --budget) {
            std::int64_t candidate = best[budget - weight] + value;
            if (candidate > best[budget]) best[budget] = candidate;
        }
    }
    return best[capacity];
}
int main() { std::cout << knapsack(50000) << "\n"; }
'''


def load_example():
    spec = importlib.util.spec_from_file_location("knapsack_example", EXAMPLE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reference_knapsack(capacity):
    """Independent two-row DP oracle: an item never reads its updated row."""
    previous = [0] * (capacity + 1)
    for item in range(1, 601):
        weight = (item * 37) % 997 + 1
        value = (item * 101) % 1009 + 1
        current = previous.copy()
        for budget in range(weight, capacity + 1):
            current[budget] = max(previous[budget], previous[budget - weight] + value)
        previous = current
    return previous[capacity]


def test_knapsack_matches_independent_oracle():
    example = load_example()
    for capacity in (0, 1, 2, 3, 7, 31, 64, 127):
        assert example.knapsack(capacity) == reference_knapsack(capacity)


def test_nonpositive_capacity_and_import_are_safe(capsys):
    example = load_example()
    assert capsys.readouterr().out == ""
    assert example.knapsack(-5) == 0
    assert example.knapsack(0) == 0


@pytest.mark.skipif(shutil.which("g++") is None, reason="g++ is required")
def test_knapsack_matches_cpp_at_default_and_multiple_inputs(tmp_path):
    source = tmp_path / "knapsack.cpp"
    binary = tmp_path / "knapsack.exe"
    source.write_text(KNAPSACK_CPP, encoding="utf-8")
    success, message = compile_and_test(source, binary)
    assert success, message
    result = validate_candidate(EXAMPLE, source, binary)
    assert result.success, result.feedback
    assert result.coverage == "baseline+integer-functions"
    assert result.case_count >= 8
