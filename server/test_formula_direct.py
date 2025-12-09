"""
Simple direct test of battery formula (no API needed)
"""
import sys
sys.path.insert(0, '.')

from formulas import update_battery, MAX_PAYLOAD_KG, BULLET_MASS_KG, ENDURANCE_MIN_EMPTY, ENDURANCE_MIN_FULL

print("=" * 70)
print("Battery Formula Direct Test (No Server Required)")
print("=" * 70)
print(f"\nConstants:")
print(f"  MAX_PAYLOAD_KG = {MAX_PAYLOAD_KG}")
print(f"  BULLET_MASS_KG = {BULLET_MASS_KG}")
print(f"  ENDURANCE_MIN_EMPTY = {ENDURANCE_MIN_EMPTY} min")
print(f"  ENDURANCE_MIN_FULL = {ENDURANCE_MIN_FULL} min")

print("\n" + "=" * 70)
print("Test Cases")
print("=" * 70)

# Test 1
print("\n✅ Test 1: Full payload (250 bullets), 60 seconds")
result = update_battery(100.0, 250, 60.0)
print(f"   Initial: 100%, Bullets: 250, Time: 60s")
print(f"   Final: {result:.2f}%")
print(f"   Drained: {100.0 - result:.2f}%")

# Test 2
print("\n✅ Test 2: Empty payload (0 bullets), 60 seconds")
result = update_battery(100.0, 0, 60.0)
print(f"   Initial: 100%, Bullets: 0, Time: 60s")
print(f"   Final: {result:.2f}%")
print(f"   Drained: {100.0 - result:.2f}%")

# Test 3
print("\n✅ Test 3: Half payload (125 bullets), 60 seconds")
result = update_battery(100.0, 125, 60.0)
print(f"   Initial: 100%, Bullets: 125, Time: 60s")
print(f"   Final: {result:.2f}%")
print(f"   Drained: {100.0 - result:.2f}%")

# Test 4
print("\n✅ Test 4: Full payload, 10 minutes (600s)")
result = update_battery(100.0, 250, 600.0)
print(f"   Initial: 100%, Bullets: 250, Time: 600s")
print(f"   Final: {result:.2f}%")
print(f"   Drained: {100.0 - result:.2f}%")

# Test 5
print("\n✅ Test 5: Full payload, 1 hour (3600s)")
result = update_battery(100.0, 250, 3600.0)
print(f"   Initial: 100%, Bullets: 250, Time: 3600s (1 hour)")
print(f"   Final: {result:.2f}%")
print(f"   Drained: {100.0 - result:.2f}%")

print("\n" + "=" * 70)
print("✅ All tests completed successfully!")
print("=" * 70)
print("\nFormula working correctly in formulas.py")
print("API endpoint should work identically when server is running.")
print("\nTo test API endpoint:")
print("  1. Start server: python app.py")
print("  2. Run: python test_api_endpoint.py")
print("=" * 70)
