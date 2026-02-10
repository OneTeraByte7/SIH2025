"""
Test script for surveillance system
"""
import requests
import time
import json

BASE_URL = "https://sih2025-f2bw.onrender.com/api"

def test_surveillance():
    print("=" * 60)
    print("Testing Surveillance System")
    print("=" * 60)
    
    # 1. Check surveillance status
    print("\n1. Checking surveillance status...")
    response = requests.get(f"{BASE_URL}/surveillance/status")
    if response.status_code == 200:
        data = response.json()
        print(f"   Status: {'Running' if data['running'] else 'Stopped'}")
        print(f"   Paused: {data['paused']}")
        print(f"   Time: {data['time']:.2f}s")
        print(f"   Drones: {len(data['drones'])}")
        for drone in data['drones']:
            print(f"      Drone {drone['id']}: pos={[f'{p:.1f}' for p in drone['position']]}, battery={drone['battery']:.1f}%")
    else:
        print(f"   Error: {response.status_code}")
    
    # 2. Watch drones patrol for a few seconds
    print("\n2. Watching drone patrol (5 seconds)...")
    for i in range(5):
        time.sleep(1)
        response = requests.get(f"{BASE_URL}/surveillance/status")
        if response.status_code == 200:
            data = response.json()
            drone0 = data['drones'][0]
            print(f"   [{i+1}s] Drone 0 at [{drone0['position'][0]:.1f}, {drone0['position'][1]:.1f}, {drone0['position'][2]:.1f}]")
    
    # 3. Update patrol area
    print("\n3. Updating patrol area...")
    new_area = {
        'center_position': [100, 0, 100],
        'patrol_radius': 300
    }
    response = requests.post(f"{BASE_URL}/surveillance/patrol-area", json=new_area)
    if response.status_code == 200:
        data = response.json()
        print(f"   New center: {data['center_position']}")
        print(f"   New radius: {data['patrol_radius']}m")
    
    # 4. Watch drones move to new area
    print("\n4. Watching drones adjust to new patrol area (3 seconds)...")
    for i in range(3):
        time.sleep(1)
        response = requests.get(f"{BASE_URL}/surveillance/status")
        if response.status_code == 200:
            data = response.json()
            drone0 = data['drones'][0]
            print(f"   [{i+1}s] Drone 0 at [{drone0['position'][0]:.1f}, {drone0['position'][1]:.1f}, {drone0['position'][2]:.1f}]")
    
    # 5. Test pause/resume by starting a simulation
    print("\n5. Starting a simulation (surveillance should pause)...")
    sim_config = {
        'swarm_algorithm': 'cbba-superiority',
        'friendly_count': 5,
        'enemy_count': 3,
        'max_time': 10.0,
        'assets': [{'position': [0, 0, 0], 'value': 1.0}]
    }
    response = requests.post(f"{BASE_URL}/simulation/start", json=sim_config)
    if response.status_code == 200:
        sim_id = response.json()['simulation_id']
        print(f"   Simulation started: {sim_id}")
        
        # Check surveillance status
        time.sleep(1)
        response = requests.get(f"{BASE_URL}/surveillance/status")
        if response.status_code == 200:
            data = response.json()
            print(f"   Surveillance paused: {data['paused']}")
        
        # Wait for simulation to complete
        print("   Waiting for simulation to complete...")
        for i in range(20):
            time.sleep(1)
            response = requests.get(f"{BASE_URL}/simulation/{sim_id}/status")
            if response.status_code == 200:
                status = response.json()['status']
                if status == 'completed':
                    print(f"   Simulation completed!")
                    break
        
        # Check if surveillance resumed
        time.sleep(1)
        response = requests.get(f"{BASE_URL}/surveillance/status")
        if response.status_code == 200:
            data = response.json()
            print(f"   Surveillance resumed: {not data['paused']}")
    
    print("\n" + "=" * 60)
    print("Surveillance System Test Complete!")
    print("=" * 60)

if __name__ == '__main__':
    try:
        test_surveillance()
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to server. Make sure Flask server is running on http://localhost:5000")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
