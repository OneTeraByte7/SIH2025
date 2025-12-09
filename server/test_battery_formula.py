"""
Test script for battery formula
"""
from formulas import update_battery, MAX_PAYLOAD_KG, BULLET_MASS_KG, ENDURANCE_MIN_EMPTY, ENDURANCE_MIN_FULL

print("="*60)
print("Testing Battery Formula")
print("="*60)
print(f"Constants:")
print(f"  MAX_PAYLOAD_KG: {MAX_PAYLOAD_KG}")
print(f"  BULLET_MASS_KG: {BULLET_MASS_KG}")
print(f"  ENDURANCE_MIN_EMPTY: {ENDURANCE_MIN_EMPTY} minutes")
print(f"  ENDURANCE_MIN_FULL: {ENDURANCE_MIN_FULL} minutes")
print("="*60)

# Test 1: Full payload (250 bullets)
print("\nTest 1: Full payload (250 bullets)")
battery = 100.0
bullets = 250
time_seconds = 60.0
result = update_battery(battery, bullets, time_seconds)
print(f"  Initial: {battery}%, Bullets: {bullets}, Time: {time_seconds}s")
print(f"  Final Battery: {result:.2f}%")
print(f"  Drained: {battery - result:.2f}%")

# Test 2: Empty payload (0 bullets)
print("\nTest 2: Empty payload (0 bullets)")
battery = 100.0
bullets = 0
time_seconds = 60.0
result = update_battery(battery, bullets, time_seconds)
print(f"  Initial: {battery}%, Bullets: {bullets}, Time: {time_seconds}s")
print(f"  Final Battery: {result:.2f}%")
print(f"  Drained: {battery - result:.2f}%")

# Test 3: Medium payload (125 bullets)
print("\nTest 3: Medium payload (125 bullets)")
battery = 100.0
bullets = 125
time_seconds = 60.0
result = update_battery(battery, bullets, time_seconds)
print(f"  Initial: {battery}%, Bullets: {bullets}, Time: {time_seconds}s")
print(f"  Final Battery: {result:.2f}%")
print(f"  Drained: {battery - result:.2f}%")

# Test 4: 10 minutes with full payload
print("\nTest 4: 10 minutes with full payload")
battery = 100.0
bullets = 250
time_seconds = 600.0
result = update_battery(battery, bullets, time_seconds)
print(f"  Initial: {battery}%, Bullets: {bullets}, Time: {time_seconds}s (10 min)")
print(f"  Final Battery: {result:.2f}%")
print(f"  Drained: {battery - result:.2f}%")

print("\n" + "="*60)
print("✅ All tests completed successfully!")
print("="*60)
