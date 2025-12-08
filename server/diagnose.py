"""
Quick diagnostic to identify simulation loading issues
"""

import sys
import traceback

print("="*70)
print("SIMULATION DIAGNOSTIC")
print("="*70)

# Test 1: Import basic modules
print("\n1. Testing basic imports...")
try:
    import numpy as np
    print("   ✓ numpy imported")
except Exception as e:
    print(f"   ✗ numpy failed: {e}")
    sys.exit(1)

try:
    from flask import Flask
    print("   ✓ flask imported")
except Exception as e:
    print(f"   ✗ flask failed: {e}")

# Test 2: Import drone_swarm
print("\n2. Testing drone_swarm import...")
try:
    from drone_swarm import build_swarm_controller, Drone, DroneType, GroundAsset, ALGORITHM_PRESETS
    print("   ✓ drone_swarm imported successfully")
    print(f"   ✓ Available algorithms: {list(ALGORITHM_PRESETS.keys())}")
except Exception as e:
    print(f"   ✗ drone_swarm import failed:")
    print(f"      {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: Import simulation
print("\n3. Testing simulation import...")
try:
    from simulation import SuperSimulation
    print("   ✓ simulation imported successfully")
except Exception as e:
    print(f"   ✗ simulation import failed:")
    print(f"      {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 4: Create a simple simulation
print("\n4. Testing simulation creation...")
try:
    config = {
        'swarm_algorithm': 'adaptive-shield',
        'friendly_count': 5,
        'enemy_count': 3,
        'ground_attack_ratio': 0.5,
        'max_time': 10.0,
        'assets': [{'position': [0, 0, 0], 'value': 1.0}]
    }
    
    sim = SuperSimulation(config)
    print("   ✓ SuperSimulation created")
    
    sim.initialize_scenario()
    print("   ✓ Scenario initialized")
    print(f"      - Friendlies: {len(sim.friendlies)}")
    print(f"      - Enemies: {len(sim.enemies)}")
    print(f"      - Assets: {len(sim.assets)}")
    
except Exception as e:
    print(f"   ✗ Simulation creation failed:")
    print(f"      {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 5: Run one step
print("\n5. Testing simulation step...")
try:
    sim.step(record=False)
    print("   ✓ Simulation step completed")
    print(f"      - Time: {sim.time:.2f}s")
except Exception as e:
    print(f"   ✗ Simulation step failed:")
    print(f"      {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 6: Test Flask app
print("\n6. Testing Flask app...")
try:
    from app import app
    print("   ✓ Flask app imported")
    
    # Test if routes exist
    routes = [rule.rule for rule in app.url_map.iter_rules()]
    print(f"   ✓ Found {len(routes)} routes")
    
    key_routes = ['/api/simulation/start', '/api/scenarios/presets', '/api/health']
    for route in key_routes:
        if route in routes:
            print(f"      ✓ {route}")
        else:
            print(f"      ✗ {route} MISSING!")
            
except Exception as e:
    print(f"   ✗ Flask app import failed:")
    print(f"      {e}")
    traceback.print_exc()

# Test 7: Check Python version
print("\n7. System info...")
print(f"   Python version: {sys.version}")
print(f"   Platform: {sys.platform}")

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
print("\nIf all tests passed, the backend should work.")
print("Try running: python app.py")
print("="*70)
