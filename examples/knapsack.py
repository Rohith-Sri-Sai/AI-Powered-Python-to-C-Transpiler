"""CPU-heavy 0/1 knapsack: maximize value without exceeding a weight budget.

The default performs roughly 30 million integer DP updates. It deliberately uses
ordinary Python loops rather than NumPy, so native-code acceleration is visible.
Each of the 600 deterministic items may be selected at most once. No randomness,
external dependencies, sleeps, or timing output are included.

Run directly: python examples/knapsack.py
Transpile: run python main.py, then enter examples/knapsack.py at the file prompt.
"""


def knapsack(capacity):
    """Return the optimum value for the fixed item set; nonpositive budgets give 0.

    Descending budget order is essential: ascending order would permit reusing an
    item and solve a different (unbounded-knapsack) problem. Memory is O(capacity).
    """
    if capacity <= 0:
        return 0

    best = [0] * (capacity + 1)
    for item in range(1, 601):
        weight = (item * 37) % 997 + 1
        value = (item * 101) % 1009 + 1
        for budget in range(capacity, weight - 1, -1):
            candidate = best[budget - weight] + value
            if candidate > best[budget]:
                best[budget] = candidate

    return best[capacity]


if __name__ == "__main__":
    print(knapsack(50000))
