# Complete API Documentation - All Endpoints

**Base URL**: `http://localhost:5000`

---

## 📋 Table of Contents
1. [Battery Formula API](#battery-formula-api)
2. [Drone Telemetry API](#drone-telemetry-api)
3. [Simulation API](#simulation-api)
4. [Surveillance API](#surveillance-api)
5. [Dynamic Simulation API](#dynamic-simulation-api)
6. [Utility APIs](#utility-apis)

---

## 1. Battery Formula API

### POST /api/formulas/battery
Calculate battery drain based on payload and time.

**Request:**
```json
{
  "battery_percent": 100.0,
  "bullets": 250,
  "dt_seconds": 60.0
}
```

**Response:**
```json
{
  "initial_battery": 100.0,
  "final_battery": 98.61,
  "battery_drained": 1.39,
  "bullets": 250,
  "time_elapsed_seconds": 60.0,
  "payload_kg": 2.5,
  "payload_fraction": 1.0,
  "endurance_minutes": 60.0,
  "estimated_flight_time_minutes": 59.17
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/api/formulas/battery \
  -H "Content-Type: application/json" \
  -d "{\"battery_percent\": 100.0, \"bullets\": 250, \"dt_seconds\": 60.0}"
```

---

## 2. Drone Telemetry API

### GET /api/drone/battery
Get current battery status with automatic time-based drain.

**Request:** None

**Response:**
```json
{
  "battery_percentage": 95.5,
  "status": "healthy",
  "state": "airborne",
  "timestamp": 1733655468.123,
  "estimated_flight_time_minutes": 71.6,
  "total_flight_capacity_minutes": 72.0,
  "current_weight_kg": 10.5,
  "bullets_remaining": 250,
  "flight_time_elapsed_seconds": 120.5
}
```

**cURL:**
```bash
curl http://localhost:5000/api/drone/battery
```

---

### POST /api/drone/drain
Simulate battery drain over a time period.

**Request:**
```json
{
  "flight_duration_seconds": 10,
  "current_weight_kg": 10.5
}
```
*Both parameters optional*

**Response:**
```json
{
  "battery_percentage": 95.5,
  "status": "healthy",
  "state": "airborne",
  "current_weight_kg": 10.5,
  "bullets_remaining": 250,
  "estimated_flight_time_minutes": 71.6,
  "total_flight_capacity_minutes": 72.0,
  "flight_time_elapsed_seconds": 130.5,
  "distance_traveled_km": 0.1,
  "timestamp": 1733655478.456
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/api/drone/drain \
  -H "Content-Type: application/json" \
  -d "{\"flight_duration_seconds\": 10}"
```

---

### POST /api/drone/fire
Fire bullets and reduce drone weight.

**Request:**
```json
{
  "bullets_fired": 1
}
```
*Optional, defaults to 1*

**Response:**
```json
{
  "message": "Fired 1 bullet(s)",
  "bullets_remaining": 249,
  "current_weight_kg": 10.49,
  "weight_reduced_kg": 0.01,
  "battery_percentage": 95.5,
  "estimated_flight_time_minutes": 75.2,
  "total_flight_capacity_minutes": 75.5,
  "state": "airborne",
  "timestamp": 1733655468.123
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/api/drone/fire \
  -H "Content-Type: application/json" \
  -d "{\"bullets_fired\": 5}"
```

---

### POST /api/drone/weight
Get current drone weight status.

**Request:** None (POST with empty body)

**Response:**
```json
{
  "current_weight": 10.5,
  "empty_weight": 8.0,
  "max_weight": 15.0,
  "payload_weight": 2.5,
  "max_payload": 2.5,
  "weight_percentage": 70.0,
  "weight_status": "optimal",
  "timestamp": 1733653468.123,
  "remaining_capacity": 4.5,
  "time_since_last_update": 12.5
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/api/drone/weight
```

---

## 3. Simulation API

### GET /api/scenarios/presets
Get available scenario presets.

**Request:** None

**Response:**
```json
{
  "guaranteed_win": {
    "name": "⭐ GUARANTEED WIN (Start Here)",
    "friendly_count": 25,
    "enemy_count": 10,
    "ground_attack_ratio": 0.3,
    "max_time": 300,
    "max_speed": 70.0,
    "weapon_range": 150.0,
    "detection_range": 1500.0,
    "assets": [{"position": [0, 0, 0], "value": 1.0}]
  },
  "easy": {...},
  "balanced": {...},
  "challenging": {...}
}
```

**cURL:**
```bash
curl http://localhost:5000/api/scenarios/presets
```

---

### GET /api/algorithms
Get available swarm algorithms.

**Request:** None

**Response:**
```json
[
  {
    "value": "pso",
    "label": "Particle Swarm Optimization",
    "description": "Circle formation"
  },
  {
    "value": "aco",
    "label": "Ant Colony Optimization",
    "description": "Grid formation"
  }
]
```

**cURL:**
```bash
curl http://localhost:5000/api/algorithms
```

---

### POST /api/simulation/start
Start a new simulation.

**Request:**
```json
{
  "friendly_count": 20,
  "enemy_count": 15,
  "ground_attack_ratio": 0.4,
  "max_time": 300,
  "swarm_algorithm": "pso",
  "max_speed": 70.0,
  "weapon_range": 150.0,
  "detection_range": 1500.0,
  "assets": [{"position": [0, 0, 0], "value": 1.0}]
}
```

**Response:**
```json
{
  "simulation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/api/simulation/start \
  -H "Content-Type: application/json" \
  -d "{\"friendly_count\": 20, \"enemy_count\": 15, \"swarm_algorithm\": \"pso\"}"
```

---

### GET /api/simulation/{sim_id}/status
Get simulation status and progress.

**Request:** None

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "running",
  "progress": 45.5,
  "statistics": null
}
```

**cURL:**
```bash
curl http://localhost:5000/api/simulation/YOUR_SIM_ID/status
```

---

### GET /api/simulation/{sim_id}/data
Get simulation frames/history data.

**Query Parameters:**
- `start` (optional): Start frame index
- `end` (optional): End frame index

**Request:** None

**Response:**
```json
{
  "frames": [
    {
      "time": 0.0,
      "friendlies": [...],
      "enemies": [...],
      "assets": [...]
    }
  ],
  "total_frames": 1000,
  "config": {...}
}
```

**cURL:**
```bash
curl "http://localhost:5000/api/simulation/YOUR_SIM_ID/data?start=0&end=100"
```

---

### GET /api/simulation/{sim_id}/analytics
Get simulation analytics and statistics.

**Request:** None

**Response:**
```json
{
  "timestamps": [0, 1, 2, ...],
  "friendly_count": [20, 19, 18, ...],
  "enemy_count": [15, 14, 12, ...],
  "role_distribution": {
    "hunter": [5, 6, 7, ...],
    "defender": [10, 9, 8, ...],
    "interceptor": [5, 4, 3, ...]
  },
  "statistics": {
    "duration": 120.5,
    "friendly_losses": 2,
    "enemy_losses": 15,
    "survival_rate": 0.9,
    "kill_ratio": 7.5,
    "mission_success": true
  }
}
```

**cURL:**
```bash
curl http://localhost:5000/api/simulation/YOUR_SIM_ID/analytics
```

---

### POST /api/simulation/{sim_id}/spawn-enemy
Spawn a new enemy during active simulation.

**Request:**
```json
{
  "position": [100, 200, 50],
  "type": "air"
}
```
*type can be "air" or "ground"*

**Response:**
```json
{
  "success": true,
  "enemy_id": 2001,
  "position": [100, 200, 50],
  "type": "air"
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/api/simulation/YOUR_SIM_ID/spawn-enemy \
  -H "Content-Type: application/json" \
  -d "{\"position\": [100, 200, 50], \"type\": \"air\"}"
```

---

## 4. Surveillance API

### GET /api/surveillance/status
Get current surveillance system status.

**Request:** None

**Response:**
```json
{
  "active": true,
  "paused": false,
  "drones": [
    {
      "id": "surveillance-1",
      "position": [100, 150, 80],
      "angle": 45.5,
      "health": 100
    }
  ],
  "center_position": [0, 0, 0],
  "patrol_radius": 500.0
}
```

**cURL:**
```bash
curl http://localhost:5000/api/surveillance/status
```

---

### POST /api/surveillance/start
Start or restart surveillance system.

**Request:**
```json
{
  "center_position": [0, 0, 0],
  "patrol_radius": 500.0
}
```

**Response:**
```json
{
  "status": "started",
  "center_position": [0, 0, 0],
  "patrol_radius": 500.0,
  "drones": 3
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/api/surveillance/start \
  -H "Content-Type: application/json" \
  -d "{\"center_position\": [0, 0, 0], \"patrol_radius\": 500.0}"
```

---

### POST /api/surveillance/stop
Stop surveillance system.

**Request:** None

**Response:**
```json
{
  "status": "stopped"
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/api/surveillance/stop
```

---

### POST /api/surveillance/patrol-area
Update surveillance patrol area.

**Request:**
```json
{
  "center_position": [0, 0, 0],
  "patrol_radius": 600.0
}
```

**Response:**
```json
{
  "status": "updated",
  "center_position": [0, 0, 0],
  "patrol_radius": 600.0
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/api/surveillance/patrol-area \
  -H "Content-Type: application/json" \
  -d "{\"center_position\": [0, 0, 0], \"patrol_radius\": 600.0}"
```

---

## 5. Dynamic Simulation API

### POST /api/dynamic/start
Start a dynamic simulation with moving assets.

**Request:**
```json
{
  "friendly_count": 20,
  "enemy_count": 15,
  "swarm_algorithm": "pso",
  "max_time": 300
}
```

**Response:**
```json
{
  "simulation_id": "dyn-a1b2c3d4"
}
```

**cURL:**
```bash
curl -X POST http://localhost:5000/api/dynamic/start \
  -H "Content-Type: application/json" \
  -d "{\"friendly_count\": 20, \"enemy_count\": 15}"
```

---

### GET /api/dynamic/{sim_id}/status
Get dynamic simulation status.

**Request:** None

**Response:**
```json
{
  "id": "dyn-a1b2c3d4",
  "status": "running",
  "progress": 60.0
}
```

**cURL:**
```bash
curl http://localhost:5000/api/dynamic/YOUR_SIM_ID/status
```

---

### GET /api/dynamic/{sim_id}/data
Get dynamic simulation data.

**Query Parameters:**
- `start` (optional): Start frame
- `end` (optional): End frame

**Request:** None

**Response:**
```json
{
  "frames": [...],
  "total_frames": 500
}
```

**cURL:**
```bash
curl "http://localhost:5000/api/dynamic/YOUR_SIM_ID/data?start=0&end=100"
```

---

## 6. Utility APIs

### GET /api/health
Health check endpoint.

**Request:** None

**Response:**
```json
{
  "status": "healthy",
  "active_simulations": 2,
  "version": "EMERGENCY_FIX_v1"
}
```

**cURL:**
```bash
curl http://localhost:5000/api/health
```

---

### GET /api/debug/supabase
Debug Supabase connection.

**Request:** None

**Response:**
```json
{
  "enabled": true,
  "persisted_simulations": ["sim-123", "sim-456"],
  "url": "https://your-project.supabase.co"
}
```

**cURL:**
```bash
curl http://localhost:5000/api/debug/supabase
```

---

### GET /api/debug/simulations
Debug in-memory simulations.

**Request:** None

**Response:**
```json
[
  {
    "simulation_id": "a1b2c3d4",
    "status": "completed",
    "progress": 100.0,
    "has_engine": true,
    "statistics": {...}
  }
]
```

**cURL:**
```bash
curl http://localhost:5000/api/debug/simulations
```

---

## 🧪 Complete Test Script

Save this as `test_all_apis.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:5000"

echo "========================================="
echo "Testing All API Endpoints"
echo "========================================="

# 1. Health Check
echo -e "\n1. Health Check"
curl -s $BASE_URL/api/health | json_pp

# 2. Battery Formula
echo -e "\n2. Battery Formula API"
curl -s -X POST $BASE_URL/api/formulas/battery \
  -H "Content-Type: application/json" \
  -d '{"battery_percent": 100.0, "bullets": 250, "dt_seconds": 60.0}' | json_pp

# 3. Drone Battery
echo -e "\n3. Get Drone Battery"
curl -s $BASE_URL/api/drone/battery | json_pp

# 4. Fire Bullets
echo -e "\n4. Fire Bullets"
curl -s -X POST $BASE_URL/api/drone/fire \
  -H "Content-Type: application/json" \
  -d '{"bullets_fired": 5}' | json_pp

# 5. Get Presets
echo -e "\n5. Get Scenario Presets"
curl -s $BASE_URL/api/scenarios/presets | json_pp

# 6. Get Algorithms
echo -e "\n6. Get Algorithms"
curl -s $BASE_URL/api/algorithms | json_pp

# 7. Surveillance Status
echo -e "\n7. Surveillance Status"
curl -s $BASE_URL/api/surveillance/status | json_pp

echo -e "\n========================================="
echo "All tests complete!"
echo "========================================="
```

---

## 📝 Python Test Script

Save this as `test_all_apis.py`:

```python
import requests
import json

BASE_URL = "http://localhost:5000"

def test_api(name, method, endpoint, data=None):
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data)
        
        print(f"Status: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return None

# Run tests
print("Starting API Tests...")

# 1. Health
test_api("Health Check", "GET", "/api/health")

# 2. Battery Formula
test_api("Battery Formula", "POST", "/api/formulas/battery", {
    "battery_percent": 100.0,
    "bullets": 250,
    "dt_seconds": 60.0
})

# 3. Drone Battery
test_api("Drone Battery", "GET", "/api/drone/battery")

# 4. Fire Bullets
test_api("Fire Bullets", "POST", "/api/drone/fire", {
    "bullets_fired": 5
})

# 5. Drain Battery
test_api("Drain Battery", "POST", "/api/drone/drain", {
    "flight_duration_seconds": 30
})

# 6. Get Weight
test_api("Get Weight", "POST", "/api/drone/weight")

# 7. Presets
test_api("Scenario Presets", "GET", "/api/scenarios/presets")

# 8. Algorithms
test_api("Algorithms", "GET", "/api/algorithms")

# 9. Surveillance Status
test_api("Surveillance Status", "GET", "/api/surveillance/status")

# 10. Start Simulation
result = test_api("Start Simulation", "POST", "/api/simulation/start", {
    "friendly_count": 10,
    "enemy_count": 5,
    "swarm_algorithm": "pso",
    "max_time": 60
})

if result and 'simulation_id' in result:
    sim_id = result['simulation_id']
    
    # 11. Check Status
    test_api("Simulation Status", "GET", f"/api/simulation/{sim_id}/status")

print("\n" + "="*60)
print("All API tests complete!")
print("="*60)
```

Run with:
```bash
cd server
python test_all_apis.py
```

---

## 🚀 Quick Start

1. **Start the server:**
```bash
cd server
python app.py
```

2. **Test health check:**
```bash
curl http://localhost:5000/api/health
```

3. **Test battery API:**
```bash
curl -X POST http://localhost:5000/api/formulas/battery \
  -H "Content-Type: application/json" \
  -d "{\"battery_percent\": 100, \"bullets\": 250, \"dt_seconds\": 60}"
```

**All APIs are ready to test!** 🎉
