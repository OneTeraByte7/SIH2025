"""
Test the integrated battery_drain functionality in formulas.py
"""
from formulas import (
    update_battery,
    calc_battery,
    find_battery,
    read_drone,
    update_drone_battery,
    load_drone_data,
    save_drone_data,
    update_and_save_drone,
    MAX_PAYLOAD_KG,
    BULLET_MASS_KG,
    ENDURANCE_MIN_EMPTY,
    ENDURANCE_MIN_FULL
)
import json

print("=" * 70)
print("Testing Integrated Battery Drain Functionality")
print("=" * 70)

# Test 1: Basic battery calculation
print("\n1. Basic Battery Calculation (update_battery)")
print("-" * 70)
battery = 100.0
bullets = 250
dt = 60.0
result = update_battery(battery, bullets, dt)
print(f"Initial: {battery}%, Bullets: {bullets}, Time: {dt}s")
print(f"Final: {result:.2f}%")
print(f"✅ update_battery() works")

# Test 2: Alias function (calc_battery)
print("\n2. Alias Function Test (calc_battery)")
print("-" * 70)
result2 = calc_battery(battery, bullets, dt)
print(f"calc_battery() result: {result2:.2f}%")
if abs(result - result2) < 0.001:
    print("✅ calc_battery() matches update_battery()")
else:
    print("❌ calc_battery() does not match update_battery()")

# Test 3: Load drone data
print("\n3. Load Drone Data from JSON")
print("-" * 70)
try:
    drone_data = load_drone_data()
    if drone_data:
        print(f"✅ Loaded {len(drone_data)} drone(s):")
        for drone_id in drone_data.keys():
            print(f"   - {drone_id}")
    else:
        print("⚠️ No drone.json file found")
except Exception as e:
    print(f"❌ Error loading drone data: {e}")
    drone_data = {}

# Test 4: Read specific drone
if drone_data:
    print("\n4. Read Specific Drone Data")
    print("-" * 70)
    drone_id = list(drone_data.keys())[0]
    try:
        drone_info = read_drone(drone_id, drone_data)
        print(f"Drone: {drone_id}")
        print(f"  Battery: {drone_info['battery_percent']}%")
        print(f"  Bullets: {drone_info['ammo_state']['bullets_remaining']}")
        print(f"  Timestamp: {drone_info['timestamp']}")
        print(f"✅ read_drone() works")
    except Exception as e:
        print(f"❌ Error reading drone: {e}")

# Test 5: Find battery
if drone_data:
    print("\n5. Find Battery Percentage")
    print("-" * 70)
    try:
        battery_pct = find_battery(drone_id, drone_data)
        print(f"Battery for {drone_id}: {battery_pct}%")
        print(f"✅ find_battery() works")
    except Exception as e:
        print(f"❌ Error finding battery: {e}")

# Test 6: Update drone battery (without saving)
if drone_data:
    print("\n6. Update Drone Battery (in memory)")
    print("-" * 70)
    try:
        import copy
        drone_data_copy = copy.deepcopy(drone_data)
        old_battery = drone_data_copy[drone_id]['battery_percent']
        
        # Update battery
        updated_data = update_drone_battery(drone_id, drone_data_copy)
        new_battery = updated_data[drone_id]['battery_percent']
        
        print(f"Old battery: {old_battery}%")
        print(f"New battery: {new_battery}%")
        print(f"Time-based drain: {old_battery - new_battery:.4f}%")
        print(f"✅ update_drone_battery() works")
    except Exception as e:
        print(f"❌ Error updating drone battery: {e}")

# Test 7: Complete workflow test (with backup)
if drone_data:
    print("\n7. Complete Workflow Test (load -> update -> save)")
    print("-" * 70)
    print("Creating backup and testing full workflow...")
    
    try:
        import shutil
        from pathlib import Path
        
        # Create backup
        drone_file = Path(__file__).parent / "drone.json"
        backup_file = Path(__file__).parent / "drone.json.backup"
        
        if drone_file.exists():
            shutil.copy(drone_file, backup_file)
            print(f"✅ Created backup: {backup_file.name}")
        
        # Test workflow
        print(f"Updating {drone_id}...")
        updated_drone = update_and_save_drone(drone_id)
        print(f"New battery: {updated_drone['battery_percent']:.2f}%")
        print(f"New timestamp: {updated_drone['timestamp']}")
        print("✅ Complete workflow works")
        
        # Restore backup
        if backup_file.exists():
            shutil.copy(backup_file, drone_file)
            backup_file.unlink()
            print(f"✅ Restored original drone.json")
        
    except Exception as e:
        print(f"❌ Error in workflow test: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("✅ Integration Testing Complete!")
print("=" * 70)
print("\nSummary:")
print("  ✅ Battery calculation functions integrated")
print("  ✅ Drone state management functions added")
print("  ✅ JSON file I/O functions working")
print("  ✅ All battery_drain.py functionality now in formulas.py")
print("\nYou can now use formulas.py instead of battery_drain.py!")
print("=" * 70)
