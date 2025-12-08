"""
formulas.py

Extracted mathematical constants and helper functions from `test.py`.

This module provides small, well-documented utilities that compute
distances, random points in a circle, travel times, coverage ratios,
and simple statistics used by the Monte Carlo simulation.
"""
from typing import Iterable, Tuple, Sequence
import math
import random

# --- Constants (kept here so other modules can import them) ---
DRONE_SPEED: float = 10.0          # m/s (max speed)
FIRING_RANGE: float = 250.0        # m (max firing range)
ARENA_RADIUS: float = 500.0        # m radius around the asset
THREAT_TIME_SECONDS: float = 10.0  # seconds used to compute threat range
THREAT_RANGE: float = THREAT_TIME_SECONDS * DRONE_SPEED


def random_point_in_circle(radius: float) -> Tuple[float, float]:
    """Return a uniform random point (x, y) inside a circle of `radius`.

    Uses the standard polar sampling method where r = R * sqrt(U).
    """
    r = radius * math.sqrt(random.random())
    theta = 2 * math.pi * random.random()
    x = r * math.cos(theta)
    y = r * math.sin(theta)
    return x, y


def distance(p1: Tuple[float, float], p2: Tuple[float, float] = (0.0, 0.0)) -> float:
    """Manhattan (L1) distance between points p1 and p2 (defaults to origin).

    Computed as: |x1-x2| + |y1-y2|
    p1 and p2 are 2-tuples (x, y).
    """
    return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])


def time_to_travel(distance_m: float, speed_m_s: float = DRONE_SPEED) -> float:
    """Return travel time in seconds for given distance and speed.

    If `speed_m_s` is zero or negative, returns float('inf').
    """
    if speed_m_s <= 0:
        return float('inf')
    return distance_m / speed_m_s


def within_firing_range(p1: Tuple[float, float], p2: Tuple[float, float], firing_range: float = FIRING_RANGE) -> bool:
    """Return True if p1 is within `firing_range` of p2."""
    return distance(p1, p2) <= firing_range


def coverage_ratio(attended_flags: Sequence[int]) -> float:
    """Compute coverage ratio C = sum(attended_flags) / n_threat.

    If `attended_flags` is empty (no threats), returns 1.0 by convention.
    """
    if not attended_flags:
        return 1.0
    return sum(attended_flags) / len(attended_flags)


def mean(values: Iterable[float]) -> float:
    """Return the arithmetic mean of `values`. Empty iterable -> 0.0."""
    vals = list(values)
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


def probability_all_true(bools: Sequence[int]) -> float:
    """Return fraction of True (1) values in `bools`. Empty -> 0.0."""
    if not bools:
        return 0.0
    return sum(bools) / len(bools)


__all__ = [
    "DRONE_SPEED",
    "FIRING_RANGE",
    "ARENA_RADIUS",
    "THREAT_RANGE",
    "random_point_in_circle",
    "distance",
    "time_to_travel",
    "within_firing_range",
    "coverage_ratio",
    "mean",
    "probability_all_true",
]


if __name__ == "__main__":
    # Simple demonstration when run directly
    print("Module formulas.py demo:")
    print(f"DRONE_SPEED = {DRONE_SPEED} m/s")
    print(f"THREAT_RANGE = {THREAT_RANGE} m")
    p = random_point_in_circle(ARENA_RADIUS)
    print(f"Random point in circle: {p}")
    print(f"Distance to origin: {distance(p):.2f} m")
