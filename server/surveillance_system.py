"""
Surveillance Drone System
Maintains 3 drones in constant surveillance mode until a swarm simulation is initiated
"""
import numpy as np
import time
from threading import Thread, Lock
from typing import List, Dict, Any
import random

class SurveillanceDrone:
    """A single surveillance drone patrolling an area"""
    def __init__(self, drone_id: int, center_position: np.ndarray, patrol_radius: float = 300.0):
        self.id = drone_id
        self.center_position = center_position.copy()
        self.patrol_radius = patrol_radius
        
        # Initial position - spread drones around the center
        angle = (drone_id * 120) * np.pi / 180  # 120 degrees apart
        self.position = center_position + np.array([
            patrol_radius * 0.8 * np.cos(angle),  # Start at 80% of radius
            100 + drone_id * 20,  # Different altitudes
            patrol_radius * 0.8 * np.sin(angle)
        ])
        
        self.velocity = np.zeros(3)
        self.health = 100.0
        self.battery = 100.0
        self.status = 'patrolling'
        
        # Patrol pattern - circular orbit
        self.orbit_speed = 20.0  # m/s
        self.orbit_angle = angle
        self.orbit_height = 100 + drone_id * 20
        
    def update(self, dt: float = 0.1):
        """Update drone position and state"""
        if self.status != 'patrolling':
            return
        
        # Update orbit angle
        angular_velocity = self.orbit_speed / self.patrol_radius
        self.orbit_angle += angular_velocity * dt
        
        # Calculate target position on circular orbit
        target_position = self.center_position + np.array([
            self.patrol_radius * np.cos(self.orbit_angle),
            self.orbit_height,
            self.patrol_radius * np.sin(self.orbit_angle)
        ])
        
        # Move towards target
        direction = target_position - self.position
        distance = np.linalg.norm(direction)
        
        if distance > 1.0:
            self.velocity = (direction / distance) * self.orbit_speed
            self.position += self.velocity * dt
        
        # Update battery (drains slowly)
        self.battery -= 0.01 * dt
        if self.battery < 20:
            self.battery = 100.0  # Auto-recharge when low
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'position': self.position.tolist(),
            'velocity': self.velocity.tolist(),
            'health': self.health,
            'battery': self.battery,
            'status': self.status,
            'type': 'surveillance'
        }


class SurveillanceSystem:
    """Manages surveillance drones"""
    def __init__(self, center_position: List[float] = [0, 0, 0], patrol_radius: float = 300.0):
        self.center_position = np.array(center_position, dtype=float)
        self.patrol_radius = patrol_radius
        self.drones: List[SurveillanceDrone] = []
        self.running = False
        self.paused = False
        self.thread = None
        self.lock = Lock()
        self.time = 0.0
        self.dt = 0.1
        
        # Initialize 3 surveillance drones
        for i in range(3):
            drone = SurveillanceDrone(i, self.center_position, patrol_radius)
            self.drones.append(drone)
        
        print(f"[Surveillance] Initialized 3 surveillance drones at {center_position} with {patrol_radius}m radius")
    
    def start(self):
        """Start surveillance operation"""
        if self.running:
            return
        
        self.running = True
        self.thread = Thread(target=self._run, daemon=True)
        self.thread.start()
        print("[Surveillance] Surveillance system started")
    
    def stop(self):
        """Stop surveillance operation"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        print("[Surveillance] Surveillance system stopped")
    
    def pause(self):
        """Pause surveillance (when swarm simulation starts)"""
        with self.lock:
            self.paused = True
        print("[Surveillance] Surveillance paused for swarm operation")
    
    def resume(self):
        """Resume surveillance (when swarm simulation ends)"""
        with self.lock:
            self.paused = False
        print("[Surveillance] Surveillance resumed")
    
    def _run(self):
        """Main surveillance loop"""
        while self.running:
            with self.lock:
                if not self.paused:
                    # Update all drones
                    for drone in self.drones:
                        drone.update(self.dt)
                    self.time += self.dt
            
            time.sleep(self.dt)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current surveillance state"""
        with self.lock:
            return {
                'time': self.time,
                'running': self.running,
                'paused': self.paused,
                'drones': [drone.to_dict() for drone in self.drones],
                'center_position': self.center_position.tolist(),
                'patrol_radius': self.patrol_radius
            }
    
    def set_patrol_area(self, center_position: List[float], radius: float = 300.0):
        """Update patrol area"""
        with self.lock:
            self.center_position = np.array(center_position, dtype=float)
            self.patrol_radius = radius
            
            # Update drone centers
            for drone in self.drones:
                drone.center_position = self.center_position
                drone.patrol_radius = radius
        
        print(f"[Surveillance] Patrol area updated to {center_position} with radius {radius}m")


# Global surveillance system instance
_surveillance_system = None
_surveillance_lock = Lock()

def get_surveillance_system() -> SurveillanceSystem:
    """Get or create the global surveillance system"""
    global _surveillance_system
    with _surveillance_lock:
        if _surveillance_system is None:
            _surveillance_system = SurveillanceSystem()
            _surveillance_system.start()
        return _surveillance_system

def init_surveillance(center_position: List[float] = [0, 0, 0], patrol_radius: float = 300.0):
    """Initialize surveillance system"""
    global _surveillance_system
    with _surveillance_lock:
        if _surveillance_system is not None:
            _surveillance_system.stop()
        
        _surveillance_system = SurveillanceSystem(center_position, patrol_radius)
        _surveillance_system.start()
        return _surveillance_system
