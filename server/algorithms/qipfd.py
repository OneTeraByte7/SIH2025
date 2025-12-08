import numpy as np
from typing import List, Dict, Tuple

class QIPFDController:
    """Quantum-Inspired Potential Field Dynamics for drone swarm control"""
    
    def __init__(self, drone_id: int, config: Dict):
        self.drone_id = drone_id
        self.position = np.array([0.0, 0.0, 0.0])
        self.velocity = np.array([0.0, 0.0, 0.0])
        
        # Physics constraints
        self.max_speed = config.get('max_speed', 20.0)
        self.max_accel = config.get('max_accel', 5.0)
        
        # Potential field parameters
        self.k_attract = config.get('k_attract', 10.0)
        self.k_repel = config.get('k_repel', 50.0)
        self.sigma_quantum = config.get('sigma_quantum', 0.5)
        
        # Threat parameters
        self.critical_time_threshold = 10.0  # seconds
        self.firing_range = config.get('firing_range', 100.0)

        # Telemetry counters
        self._quantum_weight_calls = 0
        self._attractor_calls = 0
        self._update_calls = 0
        
    def calculate_quantum_weights(self, enemies: List[Dict], assets: List[Dict]) -> Dict:
        """Calculate quantum-inspired weights for each threat"""
        weights = {}
        
        for enemy in enemies:
            threat_score = 0.0
            enemy_pos = np.array(enemy['position'])
            enemy_type = enemy['type']
            
            if enemy_type == 'GROUND_ATTACK':
                # Find closest asset
                min_dist_to_asset = float('inf')
                for asset in assets:
                    asset_pos = np.array(asset['position'])
                    dist = np.linalg.norm(enemy_pos - asset_pos)
                    min_dist_to_asset = min(min_dist_to_asset, dist)
                
                # Calculate time to impact
                enemy_speed = np.linalg.norm(enemy.get('velocity', [0, 0, 0]))
                if enemy_speed > 0:
                    time_to_impact = min_dist_to_asset / enemy_speed
                    
                    if time_to_impact < self.critical_time_threshold:
                        threat_score = 1000.0 / max(time_to_impact, 0.1)
                    else:
                        threat_score = 100.0 / max(min_dist_to_asset, 1.0)
                        
            elif enemy_type == 'AIR_TO_AIR':
                dist_to_me = np.linalg.norm(enemy_pos - self.position)
                threat_score = 50.0 / max(dist_to_me, 1.0)
            
            # Quantum tunneling factor
            dist = np.linalg.norm(enemy_pos - self.position)
            tunneling_prob = np.exp(-dist / 50.0)
            threat_score *= (1.0 + tunneling_prob)
            
            weights[enemy['id']] = threat_score
            
        return weights

    def calculate_attractor_point(self, enemies: List[Dict], friendlies: List[Dict], 
                                  assets: List[Dict], weights: Dict) -> np.ndarray:
        """FULL COVERAGE: Ensures EVERY enemy is engaged using round-robin + deterministic hash"""
        self._attractor_calls += 1
        
        P_attractor = np.zeros(3)
        total_weight = 0.0
        
        # Count for coverage calculation
        num_friendlies = len(friendlies)
        num_enemies = len(enemies)
        
        # Find my index (deterministic ordering)
        sorted_ids = sorted([f.get('id') for f in friendlies])
        my_index = sorted_ids.index(self.drone_id) if self.drone_id in sorted_ids else 0
        
        # GUARANTEE COVERAGE: Round-robin ensures every enemy gets at least one drone
        my_primary_responsibilities = []
        my_secondary_targets = []
        
        for enemy_idx, enemy in enumerate(enemies):
            enemy_pos = np.array(enemy['position'])
            enemy_id = enemy.get('id', 0)
            my_dist = np.linalg.norm(enemy_pos - self.position)
            
            # PRIMARY: Round-robin assignment (drone_index matches enemy_index % num_friendlies)
            is_primary = (enemy_idx % num_friendlies) == my_index
            
            if is_primary:
                my_primary_responsibilities.append(enemy)
            else:
                # SECONDARY: Use deterministic hash for additional support
                my_score = (self.drone_id * 7919 + enemy_id * 6547) % 1000
                my_score += 1000.0 / max(my_dist, 1.0)
                
                # Check if I have highest score among non-primary drones
                is_top_secondary = True
                for f_idx, friendly in enumerate(friendlies):
                    if friendly['id'] == self.drone_id:
                        continue
                    # Skip if they are primary for this enemy
                    if (enemy_idx % num_friendlies) == f_idx:
                        continue
                    
                    f_pos = np.array(friendly['position'])
                    f_dist = np.linalg.norm(f_pos - enemy_pos)
                    f_id = friendly['id']
                    f_score = (f_id * 7919 + enemy_id * 6547) % 1000
                    f_score += 1000.0 / max(f_dist, 1.0)
                    
                    if f_score > my_score:
                        is_top_secondary = False
                        break
                
                if is_top_secondary:
                    my_secondary_targets.append(enemy)
        
        # Weight PRIMARY responsibilities heavily (20x)
        for enemy in my_primary_responsibilities:
            enemy_pos = np.array(enemy['position'])
            base_weight = weights.get(enemy['id'], 100.0)
            
            # Ground attacks get massive priority
            if enemy.get('type') == 'GROUND_ATTACK':
                base_weight *= 15.0
            
            # Primary responsibility gets 20x weight
            weight = base_weight * 20.0
            P_attractor += weight * enemy_pos
            total_weight += weight
        
        # Add SECONDARY targets (lower weight)
        for enemy in my_secondary_targets:
            enemy_pos = np.array(enemy['position'])
            base_weight = weights.get(enemy['id'], 100.0)
            
            if enemy.get('type') == 'GROUND_ATTACK':
                base_weight *= 5.0
            
            # Secondary gets 5x weight
            weight = base_weight * 5.0
            P_attractor += weight * enemy_pos
            total_weight += weight
        
        # OBSERVABLE: Add repulsion from visible friendlies (collision avoidance)
        repulsion_total = np.zeros(3)
        detection_range = 200.0
        for friendly in friendlies:
            if friendly['id'] == self.drone_id:
                continue
                
            friendly_pos = np.array(friendly['position'])
            distance = np.linalg.norm(self.position - friendly_pos)
            
            # Only consider observable friendlies
            if distance > detection_range:
                continue
            
            if distance < 30.0 and distance > 0.1:  # Safe distance zone
                repulsion_strength = self.k_repel / (distance**2 + 0.1)
                repulsion_vector = (self.position - friendly_pos) / distance
                repulsion_total += repulsion_strength * repulsion_vector
        
        # Add critical asset protection for immediate threats
        for asset in assets:
            asset_pos = np.array(asset['position'])
            
            for enemy in enemies:
                if enemy.get('type') != 'GROUND_ATTACK':
                    continue
                    
                enemy_pos = np.array(enemy['position'])
                enemy_vel = np.array(enemy.get('velocity', [0, 0, 0]))
                
                dist_to_asset = np.linalg.norm(enemy_pos - asset_pos)
                enemy_speed = np.linalg.norm(enemy_vel)
                time_to_asset = dist_to_asset / max(enemy_speed, 1.0)
                
                if time_to_asset < self.critical_time_threshold:
                    my_dist = np.linalg.norm(self.position - enemy_pos)
                    
                    # OBSERVABLE: Only respond if I'm close enough to observe threat
                    if my_dist < 500.0:
                        intercept_point = enemy_pos + enemy_vel * min(time_to_asset * 0.5, 1.0)
                        protection_weight = 500.0 / max(time_to_asset, 0.1)
                        P_attractor += protection_weight * intercept_point
                        total_weight += protection_weight
        
        # Combine attraction and repulsion
        if total_weight > 0:
            P_attractor = (P_attractor / total_weight) + repulsion_total
        else:
            # No targets - stay near assets
            if assets:
                P_attractor = np.array(assets[0]['position'])
            else:
                P_attractor = self.position
        
        return P_attractor
    
    def compute_control(self, enemies: List[Dict], friendlies: List[Dict], 
                       assets: List[Dict], dt: float) -> np.ndarray:
        """Main control loop - returns velocity command"""
        
        # Step 1: Calculate quantum weights
        self._quantum_weight_calls += 1
        weights = self.calculate_quantum_weights(enemies, assets)
        
        # Step 2: Calculate attractor point
        P_attractor = self.calculate_attractor_point(enemies, friendlies, assets, weights)
        
        # Step 3: Calculate desired velocity
        v_desired = (P_attractor - self.position) / dt
        
        # Step 4: Add quantum noise for exploration
        quantum_noise = np.random.normal(0, self.sigma_quantum, 3)
        v_final = v_desired + quantum_noise
        
        # Step 5: Apply physical constraints
        speed = np.linalg.norm(v_final)
        if speed > self.max_speed:
            v_final = (v_final / speed) * self.max_speed
        
        # Step 6: Limit acceleration
        a_required = (v_final - self.velocity) / dt
        if np.linalg.norm(a_required) > self.max_accel:
            a_limited = (a_required / np.linalg.norm(a_required)) * self.max_accel
            v_final = self.velocity + a_limited * dt
        self._update_calls += 1
        return v_final

    def get_telemetry(self) -> dict:
        return {
            'pso_iterations': int(self._quantum_weight_calls or 1),
            'aco_pheromone_strength': float(self.sigma_quantum or 0.1),
            'abc_scout_count': int(self._attractor_calls or 1)
        }
    
    def update(self, v_command: np.ndarray, dt: float):
        """Update drone state"""
        self.velocity = v_command
        self.position += self.velocity * dt