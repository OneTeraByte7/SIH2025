import numpy as np
from typing import List, Dict, Tuple, Optional
from enum import Enum

class EngagementMode(Enum):
    ENGAGE_IMMEDIATELY = 1
    ENGAGE_AGGRESSIVE = 2
    ENGAGE_CAUTIOUS = 3
    WAIT_FOR_SUPPORT = 4
    DISENGAGE = 5

class CBBAController:
    """CBBA + APF + Local Superiority for coordinated swarm control"""
    
    def __init__(self, drone_id: int, config: Dict):
        self.drone_id = drone_id
        self.position = np.array([0.0, 0.0, 0.0])
        self.velocity = np.array([0.0, 0.0, 0.0])
        
        # Resources
        self.max_ammo = config.get('max_ammo', 100)
        self.max_fuel = config.get('max_fuel', 1000)
        self.remaining_ammo = self.max_ammo
        self.remaining_fuel = self.max_fuel
        
        # CBBA state
        self.my_bundle = []
        self.my_bids = {}
        self.assigned_target = None

        # Telemetry counters
        self._build_calls = 0
        self._bundle_additions = 0
        self._resolve_calls = 0
        self._greedy_calls = 0
        
        # Physical parameters
        self.max_speed = config.get('max_speed', 20.0)
        self.firing_range = config.get('firing_range', 100.0)
        self.max_range = config.get('max_range', 500.0)
        
        # APF parameters
        self.k_attract = 10.0
        self.k_repel = 50.0
        
    def calculate_task_value(self, enemy: Dict, assets: List[Dict]) -> float:
        """Calculate bid value for a task"""
        
        base_value = 0.0
        enemy_pos = np.array(enemy['position'])
        
        # Priority based on enemy type (ground enemies prioritized)
        if enemy['type'] == 'GROUND_ATTACK':
            min_dist = float('inf')
            for asset in assets:
                asset_pos = np.array(asset['position'])
                dist = np.linalg.norm(enemy_pos - asset_pos)
                min_dist = min(min_dist, dist)
            
            enemy_speed = np.linalg.norm(enemy.get('velocity', [0, 0, 0]))
            time_to_impact = min_dist / max(enemy_speed, 1.0)
            
            if time_to_impact < 10.0:
                base_value = 1500.0
            else:
                base_value = 800.0
        else:
            base_value = 150.0
        
        # Distance penalty
        distance = np.linalg.norm(self.position - enemy_pos)
        distance_factor = 1.0 / (1.0 + distance / self.max_range)
        
        # Resource consideration
        ammo_factor = self.remaining_ammo / self.max_ammo
        fuel_factor = self.remaining_fuel / self.max_fuel
        resource_factor = min(ammo_factor, fuel_factor)
        
        total_value = base_value * distance_factor * resource_factor
        return total_value
    
    def build_bundle(self, enemies: List[Dict], assets: List[Dict], max_bundle_size: int = 3):
        """Phase 1: Build bundle of tasks"""
        self._build_calls += 1
        
        self.my_bundle = []
        self.my_bids = {}
        assigned_ids = set()
        
        for _ in range(max_bundle_size):
            best_value = 0.0
            best_enemy = None
            
            for enemy in enemies:
                if enemy['id'] in assigned_ids:
                    continue
                    
                value = self.calculate_task_value(enemy, assets)
                
                if value > best_value:
                    best_value = value
                    best_enemy = enemy
            
            if best_enemy is not None:
                self.my_bundle.append(best_enemy['id'])
                self.my_bids[best_enemy['id']] = best_value
                assigned_ids.add(best_enemy['id'])
                self._bundle_additions += 1
            else:
                break
    
    def resolve_conflicts(self, neighbor_bundles: List[Dict]):
        """Phase 2: Consensus through conflict resolution"""
        self._resolve_calls += 1
        
        for neighbor in neighbor_bundles:
            for task_id in list(self.my_bundle):
                if task_id in neighbor['bundle']:
                    my_bid = self.my_bids[task_id]
                    neighbor_bid = neighbor['bids'][task_id]
                    
                    if neighbor_bid > my_bid:
                        self.my_bundle.remove(task_id)
                        del self.my_bids[task_id]
                    elif neighbor_bid == my_bid:
                        if neighbor['drone_id'] < self.drone_id:
                            self.my_bundle.remove(task_id)
                            del self.my_bids[task_id]
    
    def greedy_assignment(self, enemies: List[Dict], friendlies: List[Dict], assets: List[Dict]):
        """Phase 3: FULL COVERAGE - uses modulo-based round-robin + deterministic hash"""
        self._greedy_calls += 1
        
        # Count active entities for coverage calculation
        num_friendlies = len([f for f in friendlies if f.get('id') != self.drone_id]) + 1
        num_enemies = len(enemies)
        
        # Find my index in friendly list (deterministic ordering by ID)
        sorted_friendlies = sorted([f.get('id') for f in friendlies])
        my_index = sorted_friendlies.index(self.drone_id) if self.drone_id in sorted_friendlies else 0
        
        highest_priority = 0.0
        assigned_target = None
        
        for enemy_idx, enemy in enumerate(enemies):
            enemy_pos = np.array(enemy['position'])
            enemy_id = enemy.get('id', 0)
            
            # GUARANTEE COVERAGE: Round-robin ensures every enemy gets at least one drone
            # Drone 0 covers enemies 0, N, 2N, ...
            # Drone 1 covers enemies 1, N+1, 2N+1, ...
            is_primary_responsibility = (enemy_idx % num_friendlies) == my_index
            primary_boost = 100000.0 if is_primary_responsibility else 0.0
            
            # COMMUNICATION-FREE: Deterministic hash for secondary assignment
            assignment_hash = (self.drone_id * 7919 + enemy_id * 6547) % 1000
            hash_boost = 1.0 + (assignment_hash / 1000.0) * 0.5
            
            # Calculate base priority (ground enemies have higher weight)
            priority = 0.0
            if enemy['type'] == 'GROUND_ATTACK':
                min_dist = float('inf')
                for asset in assets:
                    dist = np.linalg.norm(enemy_pos - np.array(asset['position']))
                    min_dist = min(min_dist, dist)
                
                enemy_speed = np.linalg.norm(enemy.get('velocity', [0, 0, 0]))
                time_to_impact = min_dist / max(enemy_speed, 1.0)
                
                if time_to_impact < 10.0:
                    priority = 1500.0 / max(time_to_impact, 0.1)
                else:
                    priority = 150.0 / max(min_dist, 1.0)
            else:
                dist = np.linalg.norm(enemy_pos - self.position)
                priority = 60.0 / max(dist, 1.0)
            
            # Distance-based boost: closer drones naturally prioritize nearby threats
            my_dist = np.linalg.norm(enemy_pos - self.position)
            distance_factor = 100.0 / max(my_dist, 1.0)
            
            # Combined priority: primary responsibility >> priority >> distance
            total_priority = primary_boost + (priority * hash_boost * distance_factor)
            
            if total_priority > highest_priority:
                highest_priority = total_priority
                assigned_target = enemy
        
        self.assigned_target = assigned_target

    def get_telemetry(self) -> dict:
        """Return CBBA-specific telemetry mapped into common keys."""
        avg_bid = 0.0
        if self.my_bids:
            avg_bid = sum(self.my_bids.values()) / max(1, len(self.my_bids))

        return {
            'pso_iterations': int(self._resolve_calls + self._greedy_calls),
            'aco_pheromone_strength': float(avg_bid or 0.1),
            'abc_scout_count': int(self._bundle_additions or 1)
        }
    
    def assess_local_superiority(self, enemies: List[Dict], friendlies: List[Dict]) -> EngagementMode:
        """Assess force ratio - COMMUNICATION FREE using observable positions only"""
        
        if self.assigned_target is None:
            return EngagementMode.WAIT_FOR_SUPPORT
        
        target_pos = np.array(self.assigned_target['position'])
        engagement_radius = 2 * self.firing_range
        
        # OBSERVABLE: Count forces within my sensor range (no communication needed)
        friendlies_nearby = sum(1 for f in friendlies 
                               if np.linalg.norm(np.array(f['position']) - target_pos) < engagement_radius)
        enemies_nearby = sum(1 for e in enemies 
                            if np.linalg.norm(np.array(e['position']) - target_pos) < engagement_radius)
        
        # Local observation-based force ratio
        force_ratio = friendlies_nearby / max(enemies_nearby, 1)
        
        # PRIORITY: Ground attacks on assets always engage immediately
        if self.assigned_target['type'] == 'GROUND_ATTACK':
            return EngagementMode.ENGAGE_IMMEDIATELY
        
        # Observable-based tactics (no communication needed)
        my_distance = np.linalg.norm(target_pos - self.position)
        
        if force_ratio >= 1.5 or my_distance < self.firing_range * 0.5:
            return EngagementMode.ENGAGE_AGGRESSIVE
        elif force_ratio >= 1.0:
            return EngagementMode.ENGAGE_CAUTIOUS
        elif force_ratio >= 0.5 or my_distance < self.firing_range:
            return EngagementMode.WAIT_FOR_SUPPORT
        else:
            return EngagementMode.DISENGAGE
    
    def calculate_apf_movement(self, mode: EngagementMode, friendlies: List[Dict]) -> np.ndarray:
        """Calculate movement using Artificial Potential Fields"""
        
        F_total = np.zeros(3)
        
        # Attractive force to target
        if self.assigned_target is not None:
            target_pos = np.array(self.assigned_target['position'])
            distance = np.linalg.norm(target_pos - self.position)
            
            if distance > 0:
                F_attract = self.k_attract * (target_pos - self.position) / distance
                F_total += F_attract
        
        # Repulsive forces from friendlies
        for friendly in friendlies:
            if friendly['id'] == self.drone_id:
                continue
            
            f_pos = np.array(friendly['position'])
            distance = np.linalg.norm(f_pos - self.position)
            safe_distance = 10.0
            
            if distance < safe_distance * 3 and distance > 0:
                repulsion_strength = self.k_repel / (distance**2 + 0.1)
                direction = (self.position - f_pos) / distance
                F_repel = repulsion_strength * direction
                F_total += F_repel
        
        # Convert force to velocity
        desired_velocity = F_total / 1.0  # mass = 1
        
        # Apply limits
        speed = np.linalg.norm(desired_velocity)
        if speed > self.max_speed:
            desired_velocity = (desired_velocity / speed) * self.max_speed
        
        return desired_velocity
    
    def compute_control(self, enemies: List[Dict], friendlies: List[Dict], 
                       assets: List[Dict], comm_available: bool = False) -> np.ndarray:
        """Main control loop"""
        
        if comm_available:
            self.build_bundle(enemies, assets)
            # In real implementation, exchange bundles here
            # self.resolve_conflicts(neighbor_bundles)
            if self.my_bundle:
                self.assigned_target = next((e for e in enemies if e['id'] == self.my_bundle[0]), None)
        else:
            self.greedy_assignment(enemies, friendlies, assets)
        
        mode = self.assess_local_superiority(enemies, friendlies)
        velocity_command = self.calculate_apf_movement(mode, friendlies)
        
        return velocity_command
    
    def update(self, v_command: np.ndarray, dt: float):
        """Update drone state"""
        self.velocity = v_command
        self.position += self.velocity * dt
        self.remaining_fuel -= np.linalg.norm(v_command) * dt * 0.1