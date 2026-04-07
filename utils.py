"""
utils.py  —  Shared helpers
-----------------------------
Statistics, formatting, and probabilistic vehicle spawning.
"""

import random


def should_spawn_vehicle(arrival_rate: float, delta: float) -> bool:
    """
    Poisson-approximation spawn check.
    arrival_rate: expected vehicles per second per lane.
    delta       : seconds since last check.
    """
    probability = min(arrival_rate * delta, 1.0)
    return random.random() < probability


def compute_average_wait(departed_vehicles: list) -> float:
    """Mean waiting time (seconds) for all departed vehicles."""
    if not departed_vehicles:
        return 0.0
    total = sum(v.wait_time for v in departed_vehicles if v.wait_time is not None)
    return total / len(departed_vehicles)


def compute_throughput(departed_vehicles: list, elapsed_seconds: float) -> float:
    """Vehicles cleared per minute."""
    if elapsed_seconds <= 0:
        return 0.0
    return (len(departed_vehicles) / elapsed_seconds) * 60.0


def format_seconds(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 60}m {s % 60}s" if s >= 60 else f"{s}s"
