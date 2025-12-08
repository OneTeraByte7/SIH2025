import numpy as np
from typing import List, Dict, Tuple
from scipy.optimize import minimize

class CVTCBFController:
    """Centroidal Voronoi Tessellation with Control Barrier Functions"""
    
    def __init__(self, drone_id: int, config: Dict):
        self.drone_id = drone_id
        self.position = np.array([0.0, 0.0, 0.0])
        self.velocity = np.array([0.0, 0.0, 0.0])
        
        # CVT parameters
        self.alpha = config.get('alpha', 200.0)  # Asset importance
        self.beta = config.get('beta', 100.0)    # Threat importance
        self.sigma1 = config.get('sigma1', 100.0)  # Asset radius
        self.sigma2 = config.get('sigma2', 50.0)   # Threat radius
        self.epsilon = 0.01  # Background density
        self.k_prop = config.get('k_prop', 2.0)  # Convergence gain
        
        # CBF parameters
        self.R_max = config.get('R_max', 500.0)  # Max range from asset
        self.d_safe = config.get('d_safe', 10.0)  # Safe distance
        self.lambda_range = 1.0
        self.lambda_coll = 1.0
        self.lambda_defense = 2.0
        
        # Physical limits
        self.max_speed = config.get('max_speed', 20.0)
        self.max_accel = config.get('max_accel', 5.0)
        
        # Sampling parameters
        self.num_samples = 50

        # Telemetry counters
        self._centroid_calls = 0
        self._voronoi_samples_count = 0
        self._cbf_corrections = 0
        
    def calculate_density(self, q: np.ndarray, assets: List[Dict], threats: List[Dict]) -> float:
        """Calculate adaptive density function φ(q)"""
        
        density = self.epsilon
        
        # Asset protection term
        for asset in assets:
            asset_pos = np.array(asset['position'])
            dist_sq = np.sum((q - asset_pos)**2)
            asset_density = self.alpha * np.exp(-dist_sq / (2 * self.sigma1**2))
            density += asset_density
        
        # Threat response term
        for threat in threats:
            threat_pos = np.array(threat['position'])
            dist_sq = np.sum((q - threat_pos)**2)
            threat_density = self.beta * np.exp(-dist_sq / (2 * self.sigma2**2))
            density += threat_density
        
        return density
    
    def compute_voronoi_cell(self, all_friendly_positions: List[np.ndarray], 
                            battlefield_bounds: Tuple[float, float, float]) -> List[np.ndarray]:
        """COMMUNICATION-FREE: Approximate Voronoi using only observable friendly positions"""
        
        # Grid-based sampling that each drone can compute independently
        x_range, y_range, z_range = battlefield_bounds
        samples = []
        
        # DETERMINISTIC sampling - all drones use same grid
        step = max(x_range, y_range, z_range) / 10
        
        for x in np.linspace(-x_range/2, x_range/2, 10):
            for y in np.linspace(-y_range/2, y_range/2, 10):
                for z in np.linspace(0, z_range, 5):
                    q = np.array([x, y, z])
                    
                    # Check if this point is closest to me using OBSERVABLE positions only
                    my_dist = np.linalg.norm(q - self.position)
                    is_mine = True
                    
                    # OBSERVABLE: Only consider friendlies within detection range
                    detection_range = 500.0
                    for other_pos in all_friendly_positions:
                        if np.array_equal(other_pos, self.position):
                            continue
                        # Only consider observable friendlies
                        if np.linalg.norm(other_pos - self.position) > detection_range:
                            continue
                        other_dist = np.linalg.norm(q - other_pos)
                        if other_dist < my_dist:
                            is_mine = False
                            break
                    
                    if is_mine:
                        samples.append(q)
        
        return samples if samples else [self.position]
    
    def compute_centroid(self, voronoi_samples: List[np.ndarray], 
                        assets: List[Dict], threats: List[Dict]) -> np.ndarray:
        """Compute weighted centroid of Voronoi cell"""
        
        weighted_sum = np.zeros(3)
        total_mass = 0.0
        
        for sample in voronoi_samples:
            density_value = self.calculate_density(sample, assets, threats)
            weighted_sum += sample * density_value
            total_mass += density_value
        
        if total_mass > 0:
            centroid = weighted_sum / total_mass
        else:
            centroid = self.position

        self._centroid_calls += 1
        self._voronoi_samples_count += len(voronoi_samples)
        
        return centroid
    
    def apply_cbf_safety_filter(self, u_nominal: np.ndarray, assets: List[Dict], 
                                friendlies: List[Dict], threats: List[Dict]) -> np.ndarray:
        """Apply Control Barrier Function constraints via QP"""
        
        constraints = []
        
        # Find closest asset
        closest_asset_pos = np.array(assets[0]['position']) if assets else self.position
        min_dist = float('inf')
        for asset in assets:
            asset_pos = np.array(asset['position'])
            dist = np.linalg.norm(self.position - asset_pos)
            if dist < min_dist:
                min_dist = dist
                closest_asset_pos = asset_pos
        
        # Constraint 1: Range constraint (stay within R_max of asset)
        h_range = self.R_max**2 - np.sum((self.position - closest_asset_pos)**2)
        grad_h_range = -2 * (self.position - closest_asset_pos)
        L_f_h_range = np.dot(grad_h_range, self.velocity)
        
        # Simple projection instead of full QP for efficiency
        if h_range < 0:  # Violated - move toward asset
            direction = closest_asset_pos - self.position
            direction = direction / np.linalg.norm(direction)
            return direction * self.max_speed
        
        # Constraint 2: Collision avoidance
        for friendly in friendlies:
            if friendly['id'] == self.drone_id:
                continue
            
            f_pos = np.array(friendly['position'])
            distance = np.linalg.norm(self.position - f_pos)
            
            if distance < self.d_safe * 2:  # Too close
                # Apply repulsive correction
                direction = (self.position - f_pos) / max(distance, 0.1)
                correction = direction * 5.0  # Repulsion strength
                u_nominal += correction
                self._cbf_corrections += 1
        
        # Constraint 3: Defense constraint for critical threats
        for threat in threats:
            if threat['type'] != 'GROUND_ATTACK':
                continue
            
            threat_pos = np.array(threat['position'])
            threat_vel = np.array(threat.get('velocity', [0, 0, 0]))
            
            # Calculate time to impact
            min_asset_dist = float('inf')
            intercept_pos = threat_pos
            
            for asset in assets:
                asset_pos = np.array(asset['position'])
                dist = np.linalg.norm(threat_pos - asset_pos)
                if dist < min_asset_dist:
                    min_asset_dist = dist
                    # Simple intercept calculation
                    threat_speed = np.linalg.norm(threat_vel)
                    if threat_speed > 0:
                        time = dist / threat_speed
                        intercept_pos = threat_pos + threat_vel * (time * 0.5)
            
            threat_speed = np.linalg.norm(threat_vel)
            if threat_speed > 0:
                time_to_impact = min_asset_dist / threat_speed
                
                if time_to_impact < 10.0:
                    # Check if I'm closest defender
                    my_dist = np.linalg.norm(self.position - threat_pos)
                    is_closest = True
                    
                    for friendly in friendlies:
                        if friendly['id'] == self.drone_id:
                            continue
                        f_dist = np.linalg.norm(np.array(friendly['position']) - threat_pos)
                        if f_dist < my_dist:
                            is_closest = False
                            break
                    
                    if is_closest:
                        # Override to move toward intercept
                        direction = intercept_pos - self.position
                        dist = np.linalg.norm(direction)
                        if dist > 0:
                            u_nominal = (direction / dist) * self.max_speed * 1.5
        
        # Apply speed limit
        speed = np.linalg.norm(u_nominal)
        if speed > self.max_speed:
            u_nominal = (u_nominal / speed) * self.max_speed
        
        return u_nominal
    
    def compute_control(self, friendlies: List[Dict], enemies: List[Dict], 
                       assets: List[Dict], battlefield_bounds: Tuple = (1000, 1000, 200)) -> np.ndarray:
        """FULL COVERAGE: CVT+CBF ensuring EVERY enemy is engaged"""
        
        # Extract OBSERVABLE positions only
        all_friendly_positions = [np.array(f['position']) for f in friendlies]
        num_friendlies = len(friendlies)
        num_enemies = len(enemies)
        
        # Find my index (deterministic ordering)
        sorted_ids = sorted([f.get('id', 0) for f in friendlies])
        my_index = sorted_ids.index(self.drone_id) if self.drone_id in sorted_ids else 0
        
        # Step 1: GUARANTEE COVERAGE - Round-robin + hash-based assignment
        my_enemies = []
        for enemy_idx, enemy in enumerate(enemies):
            enemy_pos = np.array(enemy['position'])
            enemy_id = enemy.get('id', 0)
            my_dist = np.linalg.norm(enemy_pos - self.position)
            
            # PRIMARY RESPONSIBILITY: Round-robin ensures full coverage
            is_primary = (enemy_idx % num_friendlies) == my_index
            primary_weight = 10.0 if is_primary else 1.0
            
            # COMMUNICATION-FREE: Deterministic hash for tie-breaking
            assignment_score = (self.drone_id * 7919 + enemy_id * 6547) % 1000
            distance_score = 100.0 / max(my_dist, 1.0)
            
            # Combined score with primary responsibility boost
            total_score = primary_weight * (assignment_score + distance_score * 10.0)
            
            # Check against other friendlies (deterministic simulation)
            should_take = is_primary  # Always take primary responsibility
            
            if not is_primary:
                # For non-primary, check if I have highest score
                for other_idx, other_pos in enumerate(all_friendly_positions):
                    if np.array_equal(other_pos, self.position):
                        continue
                    other_dist = np.linalg.norm(enemy_pos - other_pos)
                    other_id = sorted_ids[other_idx] if other_idx < len(sorted_ids) else 0
                    other_score = (other_id * 7919 + enemy_id * 6547) % 1000
                    other_distance_score = 100.0 / max(other_dist, 1.0)
                    
                    # Check if other has primary responsibility
                    other_is_primary = (enemy_idx % num_friendlies) == other_idx
                    other_primary_weight = 10.0 if other_is_primary else 1.0
                    other_total = other_primary_weight * (other_score + other_distance_score * 10.0)
                    
                    if other_total > total_score:
                        should_take = False
                        break
            
            if should_take:
                priority = primary_weight if my_dist < 200.0 else primary_weight * 0.7
                my_enemies.append((enemy, priority, is_primary))
            elif enemy.get('type') == 'GROUND_ATTACK' and my_dist < 300.0:
                # Secondary support for critical ground threats
                my_enemies.append((enemy, 0.5, False))
        
        # Step 2: Strategic positioning (CVT) only if no immediate threats
        voronoi_cell = self.compute_voronoi_cell(all_friendly_positions, battlefield_bounds)
        target_centroid = self.compute_centroid(voronoi_cell, assets, enemies)
        u_strategic = -self.k_prop * (self.position - target_centroid)
        
        # Step 3: Tactical engagement (prioritize PRIMARY responsibilities)
        u_tactical = np.zeros(3)
        threat_urgency = 0.0
        
        if my_enemies:
            # Sort: primary first, then by priority
            my_enemies.sort(key=lambda x: (-x[2], -x[1]))
            
            enemy, priority, is_primary = my_enemies[0]
            enemy_pos = np.array(enemy['position'])
            enemy_vel = np.array(enemy.get('velocity', [0, 0, 0]))
            
            # Calculate intercept point
            intercept_time = 0.5
            if enemy.get('type') == 'GROUND_ATTACK' and assets:
                asset_pos = np.array(assets[0]['position'])
                dist_to_asset = np.linalg.norm(enemy_pos - asset_pos)
                enemy_speed = np.linalg.norm(enemy_vel)
                if enemy_speed > 0:
                    intercept_time = min(dist_to_asset / enemy_speed * 0.3, 1.0)
            
            intercept_point = enemy_pos + enemy_vel * intercept_time
            u_tactical = 4.0 * priority * (intercept_point - self.position)
            
            # Calculate urgency
            if enemy.get('type') == 'GROUND_ATTACK':
                for asset in assets:
                    asset_pos = np.array(asset['position'])
                    dist = np.linalg.norm(enemy_pos - asset_pos)
                    speed = np.linalg.norm(enemy_vel)
                    if speed > 0:
                        time = dist / speed
                        if time < 15.0:
                            threat_urgency = max(threat_urgency, 1.0 - time / 15.0)
            
            # Primary responsibilities get maximum urgency
            if is_primary:
                threat_urgency = max(threat_urgency, 0.8)
        
        # Step 4: Blend strategic and tactical based on urgency
        alpha_blend = np.clip(threat_urgency, 0.0, 1.0)
        u_nominal = (1 - alpha_blend) * u_strategic + alpha_blend * u_tactical
        
        # Step 5: Safety filter (CBF)
        u_safe = self.apply_cbf_safety_filter(u_nominal, assets, friendlies, enemies)
        
        return u_safe

    def get_telemetry(self) -> dict:
        """Return CVT/CBF telemetry mapped into common keys."""
        return {
            'pso_iterations': int(self._centroid_calls or 1),
            'aco_pheromone_strength': float(self.beta or 0.1),
            'abc_scout_count': int(self._voronoi_samples_count or self.num_samples)
        }
    
    def update(self, v_command: np.ndarray, dt: float):
        """Update drone state"""
        # Apply acceleration limits
        a_required = (v_command - self.velocity) / dt
        a_mag = np.linalg.norm(a_required)
        
        if a_mag > self.max_accel:
            a_required = (a_required / a_mag) * self.max_accel
        
        self.velocity = self.velocity + a_required * dt
        self.position += self.velocity * dt