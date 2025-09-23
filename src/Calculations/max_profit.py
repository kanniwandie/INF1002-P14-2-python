from typing import List

def max_profit(prices: List[float]) -> float:
    """
    LeetCode 122 (Best Time to Buy and Sell Stock II):
    Multiple transactions allowed; cannot hold more than one share at a time.
    Greedy: sum of all positive day-to-day increases.
    """
    if not prices:
        return 0.0
    profit = 0.0
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i-1]
        if diff > 0:
            profit += diff
    return profit
