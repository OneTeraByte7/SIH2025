import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Provide the import for type checkers/linters only (won't execute at runtime)
    import formulas as fm  # type: ignore
else:
    try:
        import formulas as fm
    except Exception:
        # Minimal fallback implementation if `formulas` module is not available.
        import math
        import random as _random

        class _FM:
            # Basic default constants (tune as needed)
            DRONE_SPEED = 10.0
            FIRING_RANGE = 50.0
            ARENA_RADIUS = 1000.0
            THREAT_RANGE = 300.0

            @staticmethod
            def distance(a, b):
                return math.hypot(a[0] - b[0], a[1] - b[1])

            @staticmethod
            def time_to_travel(distance, speed):
                if speed == 0:
                    return float('inf')
                return distance / speed

            @staticmethod
            def within_firing_range(a, b, firing_range):
                return _FM.distance(a, b) <= firing_range

            @staticmethod
            def random_point_in_circle(radius):
                # Uniform sampling in a circle
                r = radius * math.sqrt(_random.random())
                theta = _random.random() * 2 * math.pi
                return (r * math.cos(theta), r * math.sin(theta))

        fm = _FM

# ----------------------------
# Constants & helper functions are in `formulas.py` and imported as `fm`
# ----------------------------

def is_enemy_attended(enemy_pos, friendly_positions):
    """Check if an enemy drone is attended using helpers from `formulas`.

    Conditions:
    - some friendly within firing range, OR
    - some friendly can reach the asset at or before the enemy.
    """
    asset_pos = (0.0, 0.0)

    d_e = fm.distance(enemy_pos, asset_pos)
    t_enemy = fm.time_to_travel(d_e, fm.DRONE_SPEED)

    for f_pos in friendly_positions:
        d_fe = fm.distance(enemy_pos, f_pos)
        d_f = fm.distance(f_pos, asset_pos)
        t_friendly = fm.time_to_travel(d_f, fm.DRONE_SPEED)

        # Condition 1: within firing range
        if fm.within_firing_range(enemy_pos, f_pos, fm.FIRING_RANGE):
            return True

        # Condition 2: can reach asset earlier or at same time
        if t_friendly <= t_enemy:
            return True

    return False

# ----------------------------
# MONTE CARLO SIMULATION
# ----------------------------

def run_single_trial(trial_id,
                     n_friendly_min=5,
                     n_friendly_max=15,
                     n_enemy_ground_min=3,
                     n_enemy_ground_max=10):
    """
    Run a single random scenario (trial) and compute coverage ratio C.
    Returns: (coverage_ratio, all_attended_flag, debug_info_dict)
    """

    # Random number of drones in this scenario
    n_friendly = random.randint(n_friendly_min, n_friendly_max)
    n_enemy_ground = random.randint(n_enemy_ground_min, n_enemy_ground_max)

    asset_pos = (0.0, 0.0)

    # Sample positions
    friendly_positions = [fm.random_point_in_circle(fm.ARENA_RADIUS)
                          for _ in range(n_friendly)]
    enemy_positions = [fm.random_point_in_circle(fm.ARENA_RADIUS)
                       for _ in range(n_enemy_ground)]

    # Determine which enemies are within "threatening range"
    threat_indices = []
    for i, e_pos in enumerate(enemy_positions):
        d_e = fm.distance(e_pos, asset_pos)
        if d_e <= fm.THREAT_RANGE:
            threat_indices.append(i)

    n_threat = len(threat_indices)

    # If no threat enemies, coverage is 1 by definition
    if n_threat == 0:
        coverage_ratio = 1.0
        all_attended = True
        attended_flags = []
    else:
        attended_flags = []
        for idx in threat_indices:
            e_pos = enemy_positions[idx]
            attended = is_enemy_attended(e_pos, friendly_positions)
            attended_flags.append(1 if attended else 0)

        coverage_ratio = sum(attended_flags) / n_threat
        all_attended = (coverage_ratio == 1.0)

    # Build a debug info dict so we can print everything clearly
    debug_info = {
        "trial_id": trial_id,
        "n_friendly": n_friendly,
        "n_enemy_ground": n_enemy_ground,
        "n_threat": n_threat,
        "coverage_ratio": coverage_ratio,
        "all_attended": all_attended,
        "attended_flags": attended_flags,     # per threat enemy
        "threat_indices": threat_indices,     # indices in enemy_positions list
        # Optional: positions if you want to log / inspect them
        "friendly_positions": friendly_positions,
        "enemy_positions": enemy_positions,
    }

    return coverage_ratio, all_attended, debug_info


def monte_carlo_simulation(num_trials=50, seed=42):
    """
    Run many trials and print the result of every trial.
    Also compute and print the Monte Carlo estimates at the end.
    """

    random.seed(seed)  # reproducibility

    coverage_values = []
    all_attended_bools = []

    print("=== MONTE CARLO SIMULATION START ===")
    print(f"Number of trials: {num_trials}")
    print(f"Threatening range: {fm.THREAT_RANGE} m")
    print(f"Firing range: {fm.FIRING_RANGE} m")
    print(f"Arena radius: {fm.ARENA_RADIUS} m\n")

    for trial in range(1, num_trials + 1):
        C, all_att, info = run_single_trial(trial)

        coverage_values.append(C)
        all_attended_bools.append(1 if all_att else 0)

        # --------- PRINT EVERY TRIAL RESULT ----------
        print(f"--- Trial {trial} ---")
        print(f"Friendly drones        : {info['n_friendly']}")
        print(f"Enemy ground drones    : {info['n_enemy_ground']}")
        print(f"Threat enemies (<= {fm.THREAT_RANGE} m from asset): {info['n_threat']}")
        print(f"Coverage ratio C       : {C:.3f}")
        print(f"All threat drones attended? : {all_att}")
        print(f"Attended flags per threat drone: {info['attended_flags']}")
        print()

    # ---------------- SUMMARY STATISTICS ----------------
    avg_coverage = sum(coverage_values) / len(coverage_values) if coverage_values else 0.0
    prob_all_attended = sum(all_attended_bools) / len(all_attended_bools) if all_attended_bools else 0.0

    print("=== MONTE CARLO SUMMARY ===")
    print(f"Estimated E[C] (mean coverage ratio)        : {avg_coverage:.3f}")
    print(f"Estimated P(all threat drones attended)     : {prob_all_attended:.3f}")
    print("===========================================\n")


# Run the Monte Carlo simulation when this script is executed
if __name__ == "__main__":
    monte_carlo_simulation(num_trials=50)
