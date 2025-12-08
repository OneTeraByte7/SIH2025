"""
Safe startup script with detailed error reporting
"""

import sys
import os

print("="*70)
print("DRONE SWARM BACKEND - SAFE STARTUP")
print("="*70)

# Step 1: Check Python version
print("\n[1/6] Checking Python version...")
if sys.version_info < (3, 9):
    print(f"❌ ERROR: Python {sys.version_info.major}.{sys.version_info.minor} is too old")
    print("   Required: Python 3.9 or newer")
    sys.exit(1)
print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# Step 2: Check dependencies
print("\n[2/6] Checking dependencies...")
required = ['numpy', 'flask', 'flask_cors']
missing = []

for module in required:
    try:
        __import__(module)
        print(f"  ✓ {module}")
    except ImportError:
        print(f"  ✗ {module} - MISSING")
        missing.append(module)

if missing:
    print(f"\n❌ ERROR: Missing dependencies: {', '.join(missing)}")
    print("   Run: pip install -r requirements.txt")
    sys.exit(1)

# Step 3: Import core modules
print("\n[3/6] Importing core modules...")
try:
    from drone_swarm import build_swarm_controller, ALGORITHM_PRESETS
    print("  ✓ drone_swarm")
except Exception as e:
    print(f"  ✗ drone_swarm - ERROR:")
    print(f"     {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    from simulation import SuperSimulation
    print("  ✓ simulation")
except Exception as e:
    print(f"  ✗ simulation - ERROR:")
    print(f"     {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Test simulation creation
print("\n[4/6] Testing simulation...")
try:
    test_config = {
        'swarm_algorithm': 'adaptive-shield',
        'friendly_count': 3,
        'enemy_count': 2,
        'max_time': 5.0,
        'assets': [{'position': [0, 0, 0], 'value': 1.0}]
    }
    test_sim = SuperSimulation(test_config)
    test_sim.initialize_scenario()
    test_sim.step(record=False)
    print("  ✓ Simulation works")
except Exception as e:
    print(f"  ✗ Simulation test failed:")
    print(f"     {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 5: Import Flask app
print("\n[5/6] Importing Flask app...")
try:
    from app import app
    print("  ✓ Flask app imported")
    
    # Count routes
    routes = list(app.url_map.iter_rules())
    print(f"  ✓ {len(routes)} routes registered")
    
except Exception as e:
    print(f"  ✗ Flask app import failed:")
    print(f"     {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 6: Start server
print("\n[6/6] Starting Flask server...")
print("="*70)
print("\n🚀 SERVER READY!")
print("\n   Backend URL: http://localhost:5000")
print("   Health check: http://localhost:5000/api/health")
print("\n   Available algorithms:")
for algo_key in ALGORITHM_PRESETS.keys():
    print(f"     - {algo_key}")
print("\n   Press Ctrl+C to stop")
print("\n" + "="*70 + "\n")

try:
    # Start Flask with detailed logging
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=False  # Disable reloader to avoid double startup
    )
except KeyboardInterrupt:
    print("\n\n✓ Server stopped by user")
except Exception as e:
    print(f"\n❌ Server error:")
    print(f"   {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
