"""
formulas.py

Extracted mathematical constants and helper functions from `test.py`.

This module provides small, well-documented utilities that compute
distances, random points in a circle, travel times, coverage ratios,
and simple statistics used by the Monte Carlo simulation.

Integrated battery drain functionality from battery_drain.py for
drone state management and JSON-based battery tracking.
"""
from typing import Iterable, Tuple, Sequence, Dict, Any, Optional
import math
import random
import json
import time
from pathlib import Path

# --- Constants (kept here so other modules can import them) ---
DRONE_SPEED: float = 10.0          # m/s (max speed)
FIRING_RANGE: float = 250.0        # m (max firing range)
ARENA_RADIUS: float = 500.0        # m radius around the asset
THREAT_TIME_SECONDS: float = 10.0  # seconds used to compute threat range
THREAT_RANGE: float = THREAT_TIME_SECONDS * DRONE_SPEED

# Battery and payload constants
MAX_PAYLOAD_KG: float = 2.5
BULLET_MASS_KG: float = 0.01
ENDURANCE_MIN_EMPTY: float = 90.0
ENDURANCE_MIN_FULL: float = 60.0
EMPTY_WEIGHT_DEFAULT: float = 8.0


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


def update_battery(battery_percent: float, bullets: int, dt_seconds: float) -> float:
    """
    Update battery based on current bullet count and time elapsed.
    
    battery_percent: current battery level (0–100)
    bullets: current bullets carried
    dt_seconds: time elapsed since last update
    
    Returns: new battery percentage
    
    Empty payload (0 bullets) = 90 min flight time
    Full payload (250 bullets) = 60 min flight time
    """
    # 1. Current payload from bullets
    payload_kg = bullets * BULLET_MASS_KG
    payload_fraction = max(0.0, min(1.0, payload_kg / MAX_PAYLOAD_KG))

    # 2. Endurance based on current payload
    endurance_min = ENDURANCE_MIN_EMPTY - \
                    (ENDURANCE_MIN_EMPTY - ENDURANCE_MIN_FULL) * payload_fraction
    endurance_sec = endurance_min * 60.0

    # Safety: if endurance_sec somehow becomes 0, kill battery immediately
    if endurance_sec <= 0:
        return 0.0

    # 3. Battery drain for this time step
    battery_drop = (dt_seconds / endurance_sec) * 100.0
    new_battery = max(0.0, battery_percent - battery_drop)
    return new_battery


# ============================================================================
# DRONE STATE MANAGEMENT (Integrated from battery_drain.py)
# ============================================================================

def calc_battery(battery: float, bullets: int, dt: float) -> float:
    """
    Calculate battery level after time elapsed (alias for update_battery).
    
    battery: current battery level (0–100)
    bullets: current bullets carried
    dt: time elapsed since last update (seconds)
    
    Returns: new battery percentage
    
    Note: This is an alias for update_battery() for compatibility with battery_drain.py
    """
    return update_battery(battery, bullets, dt)


def find_battery(drone_id: str, drone_data: Dict[str, Any]) -> float:
    """
    Find battery percentage for a specific drone from drone data.
    
    drone_id: ID of the drone (e.g., "DRONE-001")
    drone_data: Dictionary containing drone state data
    
    Returns: battery percentage
    """
    if drone_id not in drone_data:
        raise KeyError(f"Drone ID {drone_id} not found in drone data")
    return float(drone_data[drone_id].get('battery_percent', 100.0))


def read_drone(drone_id: str, drone_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Read complete drone state data for a specific drone.
    
    drone_id: ID of the drone (e.g., "DRONE-001")
    drone_data: Dictionary containing drone state data
    
    Returns: dictionary with drone state
    """
    if drone_id not in drone_data:
        raise KeyError(f"Drone ID {drone_id} not found in drone data")
    return drone_data[drone_id]


def update_drone_battery(drone_id: str, drone_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update drone battery based on elapsed time since last update.
    
    drone_id: ID of the drone (e.g., "DRONE-001")
    drone_data: Dictionary containing drone state data
    
    Returns: updated drone data dictionary
    """
    if drone_id not in drone_data:
        raise KeyError(f"Drone ID {drone_id} not found in drone data")
    
    drone = drone_data[drone_id]
    
    # Calculate time elapsed since last update
    last_timestamp = float(drone.get('timestamp', time.time()))
    dt = time.time() - last_timestamp
    
    # Get current battery and bullets
    battery = float(drone.get('battery_percent', 100.0))
    bullets = int(drone.get('ammo_state', {}).get('bullets_remaining', 0))
    
    # Calculate new battery level
    new_battery = calc_battery(battery, bullets, dt)
    
    # Update drone data
    drone_data[drone_id]['battery_percent'] = new_battery
    drone_data[drone_id]['timestamp'] = time.time()
    
    return drone_data


def load_drone_data(file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load drone data from JSON file.
    
    file_path: Path to drone.json file (default: drone.json in same directory)
    
    Returns: dictionary containing drone state data
    """
    if file_path is None:
        file_path = Path(__file__).with_name("drone.json")
    else:
        file_path = Path(file_path)
    
    if not file_path.exists():
        return {}
    
    with file_path.open('r') as f:
        return json.load(f)


def save_drone_data(drone_data: Dict[str, Any], file_path: Optional[str] = None) -> None:
    """
    Save drone data to JSON file.
    
    drone_data: Dictionary containing drone state data
    file_path: Path to save file (default: drone.json in same directory)
    """
    if file_path is None:
        file_path = Path(__file__).with_name("drone.json")
    else:
        file_path = Path(file_path)
    
    with file_path.open('w') as f:
        json.dump(drone_data, f, indent=4)


def update_and_save_drone(drone_id: str, file_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Complete workflow: load drone data, update battery, and save.
    
    drone_id: ID of the drone to update
    file_path: Path to drone.json file (optional)
    
    Returns: updated drone data for the specific drone
    """
    # Load current data
    drone_data = load_drone_data(file_path)
    
    # Update battery
    drone_data = update_drone_battery(drone_id, drone_data)
    
    # Save updated data
    save_drone_data(drone_data, file_path)
    
    return drone_data[drone_id]


__all__ = [
    # Constants
    "DRONE_SPEED",
    "FIRING_RANGE",
    "ARENA_RADIUS",
    "THREAT_RANGE",
    "MAX_PAYLOAD_KG",
    "BULLET_MASS_KG",
    "ENDURANCE_MIN_EMPTY",
    "ENDURANCE_MIN_FULL",
    "EMPTY_WEIGHT_DEFAULT",
    
    # Utility functions
    "random_point_in_circle",
    "distance",
    "time_to_travel",
    "within_firing_range",
    "coverage_ratio",
    "mean",
    "probability_all_true",
    
    # Battery functions
    "update_battery",
    "calc_battery",
    
    # Drone state management (from battery_drain.py)
    "find_battery",
    "read_drone",
    "update_drone_battery",
    "load_drone_data",
    "save_drone_data",
    "update_and_save_drone",
]


if __name__ == "__main__":
    # Simple demonstration when run directly
    print("=" * 70)
    print("Module formulas.py demo")
    print("=" * 70)
    
    # Basic constants
    print(f"\n1. Basic Constants:")
    print(f"   DRONE_SPEED = {DRONE_SPEED} m/s")
    print(f"   THREAT_RANGE = {THREAT_RANGE} m")
    
    # Geometry functions
    print(f"\n2. Geometry Functions:")
    p = random_point_in_circle(ARENA_RADIUS)
    print(f"   Random point in circle: ({p[0]:.2f}, {p[1]:.2f})")
    print(f"   Distance to origin: {distance(p):.2f} m")
    
    # Battery calculation
    print(f"\n3. Battery Calculation:")
    battery = 100.0
    bullets = 250
    dt = 60.0
    new_battery = update_battery(battery, bullets, dt)
    print(f"   Initial: {battery}%, Bullets: {bullets}, Time: {dt}s")
    print(f"   Final battery: {new_battery:.2f}%")
    print(f"   Drained: {battery - new_battery:.2f}%")
    
    # Drone state management
    print(f"\n4. Drone State Management (from battery_drain.py):")
    try:
        drone_data = load_drone_data()
        if drone_data:
            drone_id = list(drone_data.keys())[0]
            print(f"   Loaded drone data for: {drone_id}")
            battery = find_battery(drone_id, drone_data)
            print(f"   Current battery: {battery}%")
            bullets = drone_data[drone_id].get('ammo_state', {}).get('bullets_remaining', 0)
            print(f"   Bullets remaining: {bullets}")
        else:
            print("   No drone.json found - skipping drone state demo")
    except Exception as e:
        print(f"   Could not load drone data: {e}")
    
    print("\n" + "=" * 70)
    print("Demo complete!")
    print("=" * 70)
