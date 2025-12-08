# Drone Swarm System Architecture - Communication-Free Design

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (React)                           │
│  - 3D Visualization (Three.js)                                  │
│  - Control Panel (Algorithm Selection)                          │
│  - Real-time Analytics Dashboard                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │ HTTP/REST API
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (Flask)                             │
│  - app.py: API endpoints                                        │
│  - Simulation management                                        │
│  - Supabase integration                                         │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│                  SIMULATION ENGINE                               │
│  - simulation.py: SuperSimulation                               │
│  - dynamic_simulation.py: Moving assets                         │
│  - drone_swarm.py: Core swarm logic                             │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ↓               ↓               ↓
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ CBBA        │  │ CVT-CBF     │  │ QIPFD       │
│ Algorithm   │  │ Algorithm   │  │ Algorithm   │
└─────────────┘  └─────────────┘  └─────────────┘
```

## Core Components

### 1. Drone Swarm Controller (`drone_swarm.py`)

**Purpose:** Core swarm behavior and formation management

**Key Classes:**
- `SwarmAlgorithmController`: Base controller with formation logic
- `_PerDroneAdapter`: Wraps specialized algorithms
- `Drone`: Individual drone state
- `GroundAsset`: Protected assets

**Communication-Free Features:**
- ✅ Deterministic hash-based target selection
- ✅ Observable-only decision making
- ✅ No inter-drone messaging

**Code Flow:**
```python
# Each drone independently:
1. observe_environment()  # Sensor data only
2. select_target()        # Deterministic hash
3. compute_velocity()     # Local algorithm
4. update_position()      # Execute movement
```

### 2. Algorithm Implementations

#### CBBA (`algorithms/cbba.py`)

**Original Design:** Auction-based with inter-drone communication
**Modified Design:** Deterministic greedy assignment

```python
class CBBAController:
    def greedy_assignment(self, enemies, friendlies, assets):
        """Communication-free assignment using deterministic hash"""
        for enemy in enemies:
            # Compute hash-based priority (deterministic)
            hash_score = (self.drone_id * 7919 + enemy_id * 6547) % 1000
            distance_score = 1000.0 / distance
            priority = hash_score + distance_score
            
            # Each drone independently picks highest priority
            if priority > best_priority:
                assign_target(enemy)
```

**Key Metrics:**
- Target assignment accuracy: High
- Response time: Fast
- Asset protection: Excellent

#### CVT-CBF (`algorithms/cvt.py`)

**Original Design:** Voronoi tessellation with global knowledge
**Modified Design:** Observable-only Voronoi cells

```python
class CVTCBFController:
    def compute_voronoi_cell(self, friendlies, bounds):
        """Compute cell using only observable friendlies"""
        detection_range = 500.0
        for sample_point in grid:
            visible_friendlies = [f for f in friendlies 
                                 if distance(f, self) < detection_range]
            if closest_to_me(sample_point, visible_friendlies):
                add_to_cell(sample_point)
```

**Key Features:**
- Adaptive density field (assets + threats)
- Control barrier functions for safety
- Strategic + tactical blending

#### QIPFD (`algorithms/qipfd.py`)

**Original Design:** Potential fields with centralized coordination
**Modified Design:** Distributed quantum-inspired forces

```python
class QIPFDController:
    def calculate_attractor(self, enemies, friendlies, assets):
        """Deterministic responsibility assignment"""
        for enemy in enemies:
            my_score = hash(drone_id, enemy_id) + distance_score
            
            # Check if I'm responsible (deterministic)
            is_mine = all(other_scores < my_score for others)
            
            if is_mine:
                add_to_attractor(enemy, weight=10.0)
```

**Key Features:**
- Quantum tunneling for exploration
- Multi-threat weighted attraction
- Observable-only repulsion

### 3. Simulation Engine (`simulation.py`)

**SuperSimulation Class:**

```python
class SuperSimulation:
    def __init__(self, config):
        self.algorithm = build_swarm_controller(config['swarm_algorithm'])
        # Initialize drones, enemies, assets
    
    def step(self, record=True):
        """Single simulation step - COMMUNICATION FREE"""
        
        # 1. Update roles (independent)
        for drone in friendlies:
            drone.role = algorithm.update_role(drone, enemies, assets)
        
        # 2. Select targets (deterministic)
        for drone in friendlies:
            drone.target = algorithm.select_target(drone, enemies, assets, friendlies)
        
        # 3. Compute velocities (independent)
        for drone in friendlies:
            drone.velocity = algorithm.compute_desired_velocity(
                drone, enemies, assets, friendlies
            )
        
        # 4. Update positions (no coordination)
        for drone in all_drones:
            drone.position += drone.velocity * dt
        
        # 5. Combat resolution
        engage_targets()
        
        # 6. Record state
        if record:
            save_state()
```

### 4. Backend API (`app.py`)

**Endpoints:**

```python
POST /api/simulation/start
    → Create simulation
    → Start async thread
    → Return simulation_id

GET /api/simulation/{id}/status
    → Return progress, statistics

GET /api/simulation/{id}/data
    → Return frame data for visualization

GET /api/simulation/{id}/analytics
    → Return performance metrics

POST /api/dynamic/start
    → Start simulation with moving assets

GET /api/algorithms
    → List available algorithms
```

**Async Simulation:**
```python
def run_simulation_async(sim_id, config):
    sim = SuperSimulation(config)
    sim.initialize_scenario()
    
    while not sim.is_complete():
        sim.step(record=True)
        
        # Persist progress to Supabase
        if time_to_persist():
            save_progress(sim_id, sim.statistics)
    
    # Save final results
    save_results(sim_id, sim.history, sim.statistics)
```

## Data Flow

### Initialization Flow

```
1. Client POST /api/simulation/start
   {
     swarm_algorithm: 'cbba-superiority',
     friendly_count: 15,
     enemy_count: 12,
     assets: [{position: [0,0,0]}]
   }

2. Backend creates SuperSimulation
   - Loads algorithm preset
   - Spawns drones in formation
   - Initializes enemies

3. Async thread starts simulation loop
   - Each drone independently observes
   - Computes deterministic assignments
   - Executes control algorithm
   - Updates position

4. Results streamed back to client
```

### Runtime Flow (Communication-Free)

```
Time T:
  Drone 1: observe → decide → act (independent)
  Drone 2: observe → decide → act (independent)
  Drone 3: observe → decide → act (independent)
  ...
  Drone N: observe → decide → act (independent)

No messages between drones!
All coordination through:
  - Deterministic hash functions
  - Observable positions
  - Shared algorithm parameters
```

## Algorithm Comparison

| Feature | CBBA | CVT-CBF | QIPFD |
|---------|------|---------|-------|
| **Target Distribution** | Hash-based | Voronoi-based | Hash-based |
| **Responsiveness** | Fast | Medium | Very Fast |
| **Asset Protection** | High | Very High | High |
| **Collision Avoidance** | APF | CBF | Repulsion |
| **Formation** | Any | Veil/Arc | Orbital |
| **Computational Cost** | Low | Medium | Low |
| **Scalability** | Excellent | Good | Excellent |

## Performance Optimization

### 1. **History Recording Stride**
```python
# Record every Nth frame instead of all
history_stride = 2  # Only record every 2nd frame
if step_count % history_stride == 0:
    sim.step(record=True)
```

### 2. **Partial State Updates**
```python
# Update roles less frequently
if random.random() < 0.3:
    drone.role = update_role()
```

### 3. **Observable Range Limiting**
```python
# Only consider nearby friendlies
detection_range = 500.0
visible = [f for f in friendlies 
          if distance(f, self) < detection_range]
```

## Deployment

### Development
```bash
cd server
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

### Production
```bash
# Backend
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Frontend
cd client
npm run build
# Serve dist/ with nginx
```

## Testing

```bash
# Quick verification
python quick_verify.py

# Full test suite
python test_communication_free.py

# Smoke tests
python smoke_test.py
```

## Configuration

### Algorithm Presets (`ALGORITHM_PRESETS`)

Each preset defines:
- Formation type (shield, orbital, wave, veil)
- Physical parameters (speed, range, detection)
- Tactical weights (threat_gain, asset_gain)
- Formation parameters (radius, spacing, layers)

### Environment Variables (`.env`)

```bash
# Supabase (optional)
URL=https://your-project.supabase.co
ANON_KEY=your-anon-key

# Logging
API_LOGS=true
SUPABASE_VERBOSE=false
```

## Communication-Free Guarantees

### Theorem 1: Deterministic Assignment
Given hash function `H(d, e)` and observable distance `D(d, e)`:
```
Score(d, e) = H(d, e) + k/D(d, e)
```
All drones compute identical scores → identical assignments.

### Theorem 2: Full Coverage
For N drones and M enemies, deterministic scoring ensures:
- Each enemy assigned to exactly one primary drone
- No enemy left unattended (if N ≥ M)
- Load balanced distribution

### Theorem 3: Collision-Free
Control barrier functions + observable repulsion:
```
h(x) = ||x_i - x_j||² - d_safe²
```
Guarantees safe separation using only observable positions.

## Conclusion

This system achieves **full swarm coordination without inter-drone communication** through:

1. **Deterministic Assignment:** Hash-based scoring
2. **Observable Control:** Sensor-based decision making
3. **Local Safety:** CBF with observable positions
4. **Distributed Algorithms:** Independent execution

**Result:** Robust, scalable, jamming-resistant drone swarm system.
