"""
Quick test to verify flocking algorithm integration
"""
from drone_swarm import ALGORITHM_PRESETS, build_swarm_controller
import numpy as np

def test_flocking_algorithm():
    print("Testing Flocking Algorithm Integration")
    print("=" * 60)
    
    # Check if flocking preset exists
    if 'flocking-boids' in ALGORITHM_PRESETS:
        print("✓ Flocking preset found in ALGORITHM_PRESETS")
        preset = ALGORITHM_PRESETS['flocking-boids']
        print(f"  Label: {preset['label']}")
        print(f"  Description: {preset['description']}")
        print(f"  Formation: {preset['formation']}")
    else:
        print("✗ Flocking preset NOT found")
        return False
    
    # Try to build controller
    try:
        controller = build_swarm_controller('flocking-boids')
        print("✓ Controller built successfully")
        print(f"  Type: {type(controller).__name__}")
    except Exception as e:
        print(f"✗ Failed to build controller: {e}")
        return False
    
    # Test spawning drones
    try:
        anchor = np.array([0, 0, 0], dtype=float)
        pos, vel = controller.spawn_friendly(0, 10, anchor)
        print("✓ Drone spawn successful")
        print(f"  Position: {pos}")
        print(f"  Velocity: {vel}")
    except Exception as e:
        print(f"✗ Failed to spawn drone: {e}")
        return False
    
    # Check role distributions (should have no hunters)
    print("\n" + "=" * 60)
    print("Checking Role Distributions (should have 0.0 hunters):")
    print(f"  Ground threats: {controller.role_bias_ground}")
    print(f"  Air threats: {controller.role_bias_air}")
    
    if controller.role_bias_ground.get('hunter', 1.0) == 0.0 and \
       controller.role_bias_air.get('hunter', 1.0) == 0.0:
        print("✓ No hunters in role distribution")
    else:
        print("✗ Hunters still present in role distribution")
        return False
    
    print("\n" + "=" * 60)
    print("All tests passed! Flocking algorithm ready.")
    print("\nAvailable algorithms:")
    for key, algo in ALGORITHM_PRESETS.items():
        hunter_g = algo.get('role_bias_ground', {}).get('hunter', 0)
        hunter_a = algo.get('role_bias_air', {}).get('hunter', 0)
        status = "✓ No hunters" if (hunter_g == 0 and hunter_a == 0) else "⚠ Has hunters"
        print(f"  - {key}: {algo['label']} [{status}]")
    
    return True

if __name__ == '__main__':
    success = test_flocking_algorithm()
    exit(0 if success else 1)
