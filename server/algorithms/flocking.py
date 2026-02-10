"""
Flocking Algorithm Implementation
Based on Reynolds' Boids with separation, alignment, and cohesion rules

⚠️ CRITICAL LIMITATION: NO COMMUNICATION BETWEEN DRONES
- Each drone only observes local neighbors (no messaging)
- No target sharing or coordination
- No global awareness of threats
- Slower response time due to emergent behavior only
- Less effective than communication-based algorithms (QIPFD, CBBA, CVT-CBF)
"""
import numpy as np
from typing import Dict, List, Optional


class FlockingController:
    """
    Per-drone flocking controller implementing Reynolds' Boids algorithm
    
    ⚠️ NO COMMUNICATION: This algorithm operates on LOCAL OBSERVATION ONLY
    - Cannot share target information with teammates
    - Cannot coordinate attacks
    - Cannot communicate threats
    - Each drone makes independent decisions based only on what it sees
    - Results in emergent behavior but SLOWER and LESS EFFECTIVE response
    """
    
    def __init__(self, drone_id: int, config: Dict):
        self.drone_id = drone_id
        self.position = np.zeros(3)
        self.velocity = np.zeros(3)
        
        # Flocking parameters from config
        self.separation_dist = float(config.get('separation_dist', 50.0))
        self.alignment_dist = float(config.get('alignment_dist', 100.0))
        self.cohesion_dist = float(config.get('cohesion_dist', 100.0))
        
        self.separation_weight = float(config.get('separation_weight', 1.5))
        self.alignment_weight = float(config.get('alignment_weight', 1.0))
        self.cohesion_weight = float(config.get('cohesion_weight', 1.0))
        
        self.max_speed = float(config.get('max_speed', 70.0))
        self.max_force = float(config.get('max_force', 5.0))
        
        # Threat response parameters
        self.threat_weight = float(config.get('threat_weight', 2.0))
        self.detection_range = float(config.get('detection_range', 1500.0))
        self.weapon_range = float(config.get('weapon_range', 150.0))
        
        # Asset protection
        self.asset_weight = float(config.get('asset_weight', 1.2))
        
        self.assigned_target = None
        
    def compute_separation(self, friendlies: List) -> np.ndarray:
        """Avoid crowding neighbors"""
        separation = np.zeros(3)
        count = 0
        
        for other in friendlies:
            if other.get('id') == self.drone_id:
                continue
                
            other_pos = np.array(other.get('position', [0, 0, 0]), dtype=float)
            diff = self.position - other_pos
            dist = np.linalg.norm(diff)
            
            if 0 < dist < self.separation_dist:
                # Weight by inverse distance (closer = stronger repulsion)
                separation += diff / (dist + 1e-6)
                count += 1
        
        if count > 0:
            separation /= count
            # Normalize and scale to max_speed
            mag = np.linalg.norm(separation)
            if mag > 0:
                separation = (separation / mag) * self.max_speed
                # Steering = desired - current velocity
                separation = separation - self.velocity
        
        return separation
    
    def compute_alignment(self, friendlies: List) -> np.ndarray:
        """Align with average heading of neighbors"""
        alignment = np.zeros(3)
        count = 0
        
        for other in friendlies:
            if other.get('id') == self.drone_id:
                continue
                
            other_pos = np.array(other.get('position', [0, 0, 0]), dtype=float)
            dist = np.linalg.norm(self.position - other_pos)
            
            if dist < self.alignment_dist:
                other_vel = np.array(other.get('velocity', [0, 0, 0]), dtype=float)
                alignment += other_vel
                count += 1
        
        if count > 0:
            alignment /= count
            # Normalize and scale
            mag = np.linalg.norm(alignment)
            if mag > 0:
                alignment = (alignment / mag) * self.max_speed
                alignment = alignment - self.velocity
        
        return alignment
    
    def compute_cohesion(self, friendlies: List) -> np.ndarray:
        """Move toward average position of neighbors"""
        cohesion = np.zeros(3)
        count = 0
        
        for other in friendlies:
            if other.get('id') == self.drone_id:
                continue
                
            other_pos = np.array(other.get('position', [0, 0, 0]), dtype=float)
            dist = np.linalg.norm(self.position - other_pos)
            
            if dist < self.cohesion_dist:
                cohesion += other_pos
                count += 1
        
        if count > 0:
            cohesion /= count
            # Steer toward center
            desired = cohesion - self.position
            mag = np.linalg.norm(desired)
            if mag > 0:
                desired = (desired / mag) * self.max_speed
                cohesion = desired - self.velocity
        else:
            cohesion = np.zeros(3)
        
        return cohesion
    
    def compute_threat_pursuit(self, enemies: List, assets: List) -> np.ndarray:
        """
        Pursue nearest threat
        
        ⚠️ NO COMMUNICATION LIMITATION:
        - Can only see enemies within personal detection range
        - No target sharing with other drones
        - Multiple drones may target same enemy (inefficient)
        - Some enemies may go unnoticed
        - Slower response than coordinated algorithms
        """
        if not enemies:
            return np.zeros(3)
        
        # Find nearest enemy within detection range
        nearest_enemy = None
        nearest_dist = float('inf')
        
        for enemy in enemies:
            if isinstance(enemy, dict):
                enemy_pos = np.array(enemy.get('position', [0, 0, 0]), dtype=float)
                enemy_health = enemy.get('health', 0)
            else:
                enemy_pos = enemy.position
                enemy_health = enemy.health
                
            if enemy_health <= 0:
                continue
                
            dist = np.linalg.norm(self.position - enemy_pos)
            if dist < self.detection_range and dist < nearest_dist:
                nearest_dist = dist
                nearest_enemy = enemy
                if isinstance(enemy, dict):
                    self.assigned_target = enemy.get('id')
                else:
                    self.assigned_target = enemy.id
        
        if nearest_enemy is None:
            return np.zeros(3)
        
        # Pursue the target
        if isinstance(nearest_enemy, dict):
            target_pos = np.array(nearest_enemy.get('position', [0, 0, 0]), dtype=float)
        else:
            target_pos = nearest_enemy.position
            
        desired = target_pos - self.position
        mag = np.linalg.norm(desired)
        
        if mag > 0:
            desired = (desired / mag) * self.max_speed
            pursuit = desired - self.velocity
        else:
            pursuit = np.zeros(3)
        
        return pursuit
    
    def compute_asset_protection(self, assets: List) -> np.ndarray:
        """Stay near protected assets"""
        if not assets:
            return np.zeros(3)
        
        # Move toward nearest asset if too far
        nearest_asset = None
        nearest_dist = float('inf')
        
        for asset in assets:
            if isinstance(asset, dict):
                asset_pos = np.array(asset.get('position', [0, 0, 0]), dtype=float)
            else:
                asset_pos = asset.position
                
            dist = np.linalg.norm(self.position - asset_pos)
            if dist < nearest_dist:
                nearest_dist = dist
                nearest_asset = asset
        
        if nearest_asset is None:
            return np.zeros(3)
        
        # Only pull if outside protection radius
        protection_radius = 600.0
        if nearest_dist > protection_radius:
            if isinstance(nearest_asset, dict):
                asset_pos = np.array(nearest_asset.get('position', [0, 0, 0]), dtype=float)
            else:
                asset_pos = nearest_asset.position
                
            desired = asset_pos - self.position
            mag = np.linalg.norm(desired)
            if mag > 0:
                desired = (desired / mag) * self.max_speed
                return desired - self.velocity
        
        return np.zeros(3)
    
    def limit_force(self, force: np.ndarray) -> np.ndarray:
        """Limit force magnitude"""
        mag = np.linalg.norm(force)
        if mag > self.max_force:
            return (force / mag) * self.max_force
        return force
    
    def compute_control(self, enemies: List, friendlies: List, assets: List, **kwargs) -> np.ndarray:
        """Main control loop combining all behaviors"""
        
        # Convert friendlies to proper format if needed
        friendly_list = []
        for f in friendlies:
            if isinstance(f, dict):
                friendly_list.append(f)
            else:
                friendly_list.append({
                    'id': f.id,
                    'position': f.position.tolist() if hasattr(f.position, 'tolist') else f.position,
                    'velocity': f.velocity.tolist() if hasattr(f.velocity, 'tolist') else f.velocity
                })
        
        # Compute all behavioral forces
        separation = self.compute_separation(friendly_list)
        alignment = self.compute_alignment(friendly_list)
        cohesion = self.compute_cohesion(friendly_list)
        threat = self.compute_threat_pursuit(enemies, assets)
        asset_pull = self.compute_asset_protection(assets)
        
        # Apply weights and limits
        separation = self.limit_force(separation) * self.separation_weight
        alignment = self.limit_force(alignment) * self.alignment_weight
        cohesion = self.limit_force(cohesion) * self.cohesion_weight
        threat = self.limit_force(threat) * self.threat_weight
        asset_pull = self.limit_force(asset_pull) * self.asset_weight
        
        # Combine all forces
        total_force = separation + alignment + cohesion + threat + asset_pull
        
        # Update velocity
        new_velocity = self.velocity + total_force
        
        # Limit speed
        speed = np.linalg.norm(new_velocity)
        if speed > self.max_speed:
            new_velocity = (new_velocity / speed) * self.max_speed
        
        self.velocity = new_velocity
        
        return new_velocity
    
    def get_telemetry(self) -> Dict:
        """Return telemetry for analytics"""
        return {
            'separation_dist': self.separation_dist,
            'alignment_dist': self.alignment_dist,
            'cohesion_dist': self.cohesion_dist,
            'speed': float(np.linalg.norm(self.velocity))
        }
