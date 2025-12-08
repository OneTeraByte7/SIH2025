"""
Drone Configuration - Technical Specifications
Based on problem statement requirements for SIH25164
"""

# Physical Specifications
EMPTY_WEIGHT = 8.0  # kg (without battery & payload)
MAX_TAKEOFF_WEIGHT = 15.0  # kg
MAX_PAYLOAD = 2.5  # kg
MAX_PAYLOAD_KG = 2.5  # kg

# Performance Parameters
ENDURANCE_MIN_EMPTY = 90  # minutes (at empty payload / min weight)
ENDURANCE_MIN_FULL = 60   # minutes (at full payload / max weight)
ENDURANCE_MIN = 60  # minutes (at max weight)
ENDURANCE_MAX = 90  # minutes (at min weight)
MAX_SPEED = 10.0  # m/s

# Operational Parameters
ALTITUDE_MIN = 60  # meters
ALTITUDE_MAX = 120  # meters

# Range Parameters
RANGE_MIN = 20  # km
RANGE_MAX = 40  # km

# Weapon Systems
FIRING_RANGE_MIN = 30  # meters
FIRING_RANGE_MAX = 250  # meters

# Ammunition Specifications
BULLET_WEIGHT = 0.01  # kg (10 grams per bullet)
BULLET_MASS_KG = 0.01  # kg (10 grams per bullet)
MAX_BULLETS = 250  # Maximum bullets capacity
TOTAL_AMMO_WEIGHT = BULLET_WEIGHT * MAX_BULLETS  # 2.5 kg total

# Battery Simulation Parameters
BATTERY_INITIAL = 100.0  # Initial battery percentage


def update_battery(battery_percent: float,
                   bullets: int,
                   dt_seconds: float,
                   current_weight_kg: float = None) -> float:
    """
    Update battery based on current bullet count and time elapsed.
    
    battery_percent: current battery level (0–100)
    bullets: current bullets carried
    dt_seconds: time elapsed since last update
    current_weight_kg: optional explicit drone weight (overrides bullet-based payload)
    
    Returns: new battery percentage
    """
    # 1. Current payload from bullets
    if current_weight_kg is not None:
        payload_kg = max(0.0, min(MAX_PAYLOAD_KG, current_weight_kg - EMPTY_WEIGHT))
    else:
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


# Legacy functions for compatibility
def calculate_flight_time(current_weight):
    """
    Calculate flight time based on current weight.
    DEPRECATED: Use update_battery() instead for accurate calculations.
    """
    weight_ratio = (current_weight - EMPTY_WEIGHT) / (MAX_TAKEOFF_WEIGHT - EMPTY_WEIGHT)
    flight_time = ENDURANCE_MAX - (weight_ratio * (ENDURANCE_MAX - ENDURANCE_MIN))
    return max(ENDURANCE_MIN, min(ENDURANCE_MAX, flight_time))

def calculate_battery_drain_per_second(current_weight):
    """
    Calculate battery drain percentage per second based on current weight.
    DEPRECATED: Use update_battery() instead for accurate calculations.
    """
    flight_time_minutes = calculate_flight_time(current_weight)
    flight_time_seconds = flight_time_minutes * 60.0
    drain_per_second = 100.0 / flight_time_seconds
    return drain_per_second


# Weight Calculation
def get_max_payload_weight():
    """Calculate maximum payload weight based on specifications"""
    return MAX_PAYLOAD

def get_weight_limits():
    """Get weight limits for the drone"""
    return {
        'empty_weight': EMPTY_WEIGHT,
        'max_weight': MAX_TAKEOFF_WEIGHT,
        'max_payload': MAX_PAYLOAD
    }

def get_battery_config():
    """Get battery configuration"""
    return {
        'endurance_min_empty': ENDURANCE_MIN_EMPTY,
        'endurance_min_full': ENDURANCE_MIN_FULL,
        'initial_percentage': BATTERY_INITIAL
    }

def get_ammunition_config():
    """Get ammunition configuration"""
    return {
        'bullet_weight_kg': BULLET_WEIGHT,
        'max_bullets': MAX_BULLETS,
        'total_ammo_weight_kg': TOTAL_AMMO_WEIGHT
    }

def get_drone_specifications():
    """Get complete drone specifications"""
    return {
        'physical': {
            'empty_weight_kg': EMPTY_WEIGHT,
            'max_takeoff_weight_kg': MAX_TAKEOFF_WEIGHT,
            'max_payload_kg': MAX_PAYLOAD
        },
        'performance': {
            'endurance_min_empty': ENDURANCE_MIN_EMPTY,
            'endurance_min_full': ENDURANCE_MIN_FULL,
            'max_speed_mps': MAX_SPEED
        },
        'operational': {
            'altitude_min_m': ALTITUDE_MIN,
            'altitude_max_m': ALTITUDE_MAX,
            'range_min_km': RANGE_MIN,
            'range_max_km': RANGE_MAX
        },
        'weapons': {
            'firing_range_min_m': FIRING_RANGE_MIN,
            'firing_range_max_m': FIRING_RANGE_MAX,
            'bullet_weight_kg': BULLET_WEIGHT,
            'max_bullets': MAX_BULLETS
        }
    }
