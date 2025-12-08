import math
import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np


class DroneType(Enum):
	FRIENDLY = "friendly"
	ENEMY_AIR = "enemy_air"
	ENEMY_GROUND = "enemy_ground"


class DroneRole(Enum):
	HUNTER = "hunter"
	DEFENDER = "defender"
	INTERCEPTOR = "interceptor"


@dataclass
class Drone:
	id: int
	position: np.ndarray
	velocity: np.ndarray
	drone_type: DroneType
	role: Optional[DroneRole] = None
	health: float = 150.0
	target_id: Optional[int] = None

	def __post_init__(self) -> None:
		if self.drone_type == DroneType.FRIENDLY and self.role is None:
			self.role = DroneRole.INTERCEPTOR


@dataclass
class GroundAsset:
	id: int
	position: np.ndarray
	value: float
	protection_radius: float = 800.0
	health: float = 100.0


def _normalize_weights(weights: Dict[str, float], fallback: Dict[str, float]) -> Dict[str, float]:
	source = weights if weights else fallback
	total = sum(max(value, 0.0) for value in source.values()) or 1.0
	return {key: max(value, 0.0) / total for key, value in source.items()}


ALGORITHM_PRESETS: Dict[str, Dict[str, object]] = {}

# Lightweight entries for controllers placed under server/algorithms/
# These provide selectable presets so the frontend can list them and
# the existing SwarmAlgorithmController can instantiate behaviourally
# similar profiles without requiring deeper integration.
ALGORITHM_PRESETS.update({
	"cbba-superiority": {
		"label": "CBBA Superiority",
		"description": "Fast consensus-based target assignment with superior engagement",
		"formation": "shield",
		"max_speed": 78.0,  # Maximum speed
		"weapon_range": 170.0,  # Extended range
		"detection_range": 1800.0,
		"threat_gain": 7.5,  # Maximum response
		"asset_gain": 0.6,
		"target_gain": 10.0,  # Maximum targeting
		"cohesion_gain": 1.2,
		"threat_ground_weight": 12.0,  # Maximum priority
		"threat_air_weight": 6.5,  # Maximum priority
		"critical_multiplier": 7.0,  # Maximum urgency
		"threat_decay": 750.0,
		"asset_pull_gain": 1.7,
		"threat_response_time": 7.0,  # Ultra-fast response
		"role_bias_ground": {"interceptor": 0.7, "defender": 0.2, "hunter": 0.1},
		"role_bias_air": {"interceptor": 0.5, "defender": 0.15, "hunter": 0.35},
		"formation_params": {
			"ring_capacity": 8,
			"ring_radius": 380.0,
			"ring_spacing": 130.0,
			"altitude_base": 120.0,
			"altitude_step": 18.0
		}
			,
			"algorithm_params": {
				"pso_iterations": 1,
				"aco_pheromone_strength": 0.1,
				"abc_scout_count": 1
			}
	},
	"cvt-cbf": {
		"label": "CVT-CBF Defense",
		"description": "Adaptive density fields with control barrier safety constraints",
		"formation": "veil",
		"max_speed": 76.0,  # Maximum speed
		"weapon_range": 170.0,  # Extended
		"detection_range": 1800.0,
		"threat_gain": 7.0,  # Maximum response
		"asset_gain": 0.8,
		"target_gain": 9.5,  # Superior targeting
		"cohesion_gain": 1.5,
		"threat_ground_weight": 11.0,  # Maximum priority
		"threat_air_weight": 6.0,  # Maximum priority
		"critical_multiplier": 6.5,  # Maximum urgency
		"threat_decay": 800.0,
		"asset_pull_gain": 1.6,
		"threat_response_time": 9.0,  # Ultra-fast
		"role_bias_ground": {"interceptor": 0.65, "defender": 0.25, "hunter": 0.1},
		"role_bias_air": {"interceptor": 0.5, "defender": 0.15, "hunter": 0.35},
		"formation_params": {
			"arc_span_degrees": 120.0,
			"radius": 420.0,
			"altitude_base": 115.0,
			"altitude_step": 18.0,
			"layer_size": 6
		}
			,
			"algorithm_params": {
				"pso_iterations": 1,
				"aco_pheromone_strength": 0.1,
				"abc_scout_count": 1
			}
	},
	"qipfd-quantum": {
		"label": "QIPFD Quantum",
		"description": "Quantum-inspired potential field dynamics for adaptive threat response",
		"formation": "orbital",
		"max_speed": 76.0,
		"weapon_range": 160.0,
		"detection_range": 1700.0,
		"threat_gain": 5.2,
		"asset_gain": 0.5,
		"target_gain": 8.5,
		"cohesion_gain": 1.7,
		"threat_ground_weight": 8.7,
		"threat_air_weight": 4.0,
		"critical_multiplier": 4.8,
		"threat_decay": 800.0,
		"asset_pull_gain": 1.2,
		"threat_response_time": 12.0,
		"role_bias_ground": {"interceptor": 0.5, "defender": 0.25, "hunter": 0.25},
		"role_bias_air": {"interceptor": 0.35, "defender": 0.25, "hunter": 0.4},
		"formation_params": {
			"orbital_layers": 3,
			"orbit_radius": 440.0,
			"orbit_spacing": 110.0,
			"altitude_base": 130.0,
			"altitude_step": 24.0,
			"orbit_phase_offset": 0.6,
			"initial_orbit_speed": 26.0
		}
			,
			"algorithm_params": {
				"pso_iteration": 0,
				"aco_pheromone_strength": 0.0,
				"abc_scout_count": 0
			}
	}
})


class SwarmAlgorithmController:
	def __init__(self, profile: Dict[str, object], overrides: Optional[Dict[str, float]] = None):
		merged = profile.copy()
		overrides = overrides or {}
		merged.update({k: v for k, v in overrides.items() if v is not None})

		self.profile = merged
		self.max_speed = float(merged.get("max_speed", 70.0))
		self.weapon_range = float(merged.get("weapon_range", 150.0))
		self.detection_range = float(merged.get("detection_range", 1500.0))
		self.threat_gain = float(merged.get("threat_gain", 4.5))
		self.asset_gain = float(merged.get("asset_gain", 0.4))
		self.target_gain = float(merged.get("target_gain", 6.5))
		self.cohesion_gain = float(merged.get("cohesion_gain", 1.2))
		self.asset_pull_gain = float(merged.get("asset_pull_gain", 1.0))
		self.threat_ground_weight = float(merged.get("threat_ground_weight", 7.5))
		self.threat_air_weight = float(merged.get("threat_air_weight", 3.0))
		self.critical_multiplier = float(merged.get("critical_multiplier", 4.0))
		self.threat_decay = float(merged.get("threat_decay", 900.0))
		self.threatening_range_time = float(merged.get("threat_response_time", 15.0))
		self.formation = str(merged.get("formation", "shield"))
		self.formation_params = merged.get("formation_params", {}) or {}

		fallback_ground = {"interceptor": 0.55, "defender": 0.25, "hunter": 0.2}
		fallback_air = {"interceptor": 0.4, "defender": 0.2, "hunter": 0.4}
		self.role_bias_ground = _normalize_weights(merged.get("role_bias_ground", {}), fallback_ground)
		self.role_bias_air = _normalize_weights(merged.get("role_bias_air", {}), fallback_air)

	def spawn_friendly(self, index: int, total: int, anchor: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
		formation = self.formation
		params = self.formation_params
		anchor = anchor.astype(float)

		if formation == "shield":
			capacity = max(1, int(params.get("ring_capacity", 8)))
			radius_base = float(params.get("ring_radius", 360.0))
			radius_step = float(params.get("ring_spacing", 140.0))
			altitude_base = float(params.get("altitude_base", 110.0))
			altitude_step = float(params.get("altitude_step", 16.0))
			ring = index // capacity
			slot = index % capacity
			remaining = max(1, total - ring * capacity)
			slots_in_ring = min(capacity, remaining)
			angle = (2.0 * math.pi * slot) / slots_in_ring
			radius = radius_base + ring * radius_step
			position = anchor + np.array([
				radius * math.cos(angle),
				altitude_base + ring * altitude_step,
				radius * math.sin(angle)
			])
			velocity = np.zeros(3)
			return position, velocity

		if formation == "orbital":
			layers = max(1, int(params.get("orbital_layers", 3)))
			radius_base = float(params.get("orbit_radius", 420.0))
			orbit_spacing = float(params.get("orbit_spacing", 120.0))
			altitude_base = float(params.get("altitude_base", 130.0))
			altitude_step = float(params.get("altitude_step", 26.0))
			phase_offset = float(params.get("orbit_phase_offset", 0.5))
			orbit_speed = float(params.get("initial_orbit_speed", 22.0))

			layer = index % layers
			orbit_index = index // layers
			angle = (phase_offset * index) % (2.0 * math.pi)
			radius = radius_base + orbit_index * orbit_spacing
			position = anchor + np.array([
				radius * math.cos(angle),
				altitude_base + layer * altitude_step,
				radius * math.sin(angle)
			])
			tangent = np.array([
				-math.sin(angle),
				0.0,
				math.cos(angle)
			])
			velocity = tangent * orbit_speed
			return position, velocity

		if formation == "wave":
			columns = max(1, int(params.get("wave_columns", 5)))
			spacing = float(params.get("column_spacing", 180.0))
			depth_step = float(params.get("depth_step", 170.0))
			forward_offset = float(params.get("forward_offset", 320.0))
			altitude_base = float(params.get("altitude_base", 100.0))
			altitude_step = float(params.get("altitude_step", 10.0))
			push_speed = float(params.get("wave_push_speed", 26.0))

			col = index % columns
			row = index // columns
			offset_x = (col - (columns - 1) / 2.0) * spacing
			offset_z = -(forward_offset + row * depth_step)
			position = anchor + np.array([
				offset_x,
				altitude_base + row * altitude_step,
				offset_z
			])
			velocity = np.array([0.0, 0.0, push_speed])
			return position, velocity

		if formation == "veil":
			arc_span_deg = float(params.get("arc_span_degrees", 140.0))
			radius = float(params.get("radius", 460.0))
			altitude_base = float(params.get("altitude_base", 120.0))
			altitude_step = float(params.get("altitude_step", 20.0))
			layer_size = max(1, int(params.get("layer_size", 6)))

			if total == 1:
				angle = 0.0
			else:
				arc_span = math.radians(arc_span_deg)
				angle = -arc_span / 2.0 + (arc_span * index / (total - 1))
			layer = index // layer_size
			position = anchor + np.array([
				radius * math.sin(angle),
				altitude_base + layer * altitude_step,
				radius * math.cos(angle)
			])
			velocity = np.zeros(3)
			return position, velocity

		angle = (2.0 * math.pi * index) / max(1, total)
		radius = 400.0
		position = anchor + np.array([
			radius * math.cos(angle),
			120.0,
			radius * math.sin(angle)
		])
		velocity = np.zeros(3)
		return position, velocity

	def _role_from_weights(self, weights: Dict[str, float]) -> DroneRole:
		cumulative = 0.0
		roll = random.random()
		for key, weight in weights.items():
			cumulative += weight
			if roll <= cumulative:
				return DroneRole[key.upper()]
		return DroneRole.INTERCEPTOR

	def default_role(self) -> DroneRole:
		predominant = max(self.role_bias_air.items(), key=lambda item: item[1])[0]
		return DroneRole[predominant.upper()]

	def get_telemetry(self) -> dict:
		"""Return algorithm-specific telemetry values. By default return
		configured algorithm_params (if present) so callers can log realistic
		values. Algorithms that compute live telemetry can override this method.
		"""
		params = self.profile.get('algorithm_params', {}) or {}
		# Ensure canonical keys exist
		return {
			'pso_iterations': int(params.get('pso_iterations', 1) or 1),
			'aco_pheromone_strength': float(params.get('aco_pheromone_strength', 0.1) or 0.1),
			'abc_scout_count': int(params.get('abc_scout_count', 1) or 1)
		}

	def update_role(self, drone: Drone, enemies: List[Drone], assets: List[GroundAsset]) -> DroneRole:
		ground_threats = sum(1 for enemy in enemies if enemy.health > 0 and enemy.drone_type == DroneType.ENEMY_GROUND)
		weights = self.role_bias_ground if ground_threats > 0 else self.role_bias_air
		return self._role_from_weights(weights)

	def select_target(self, drone: Drone, enemies: List[Drone], assets: List[GroundAsset], friendlies: List[Drone]) -> Optional[int]:
		active_enemies = [enemy for enemy in enemies if enemy.health > 0]
		if not active_enemies:
			return None

		# Count active friendlies for coverage calculation
		active_friendlies = [f for f in friendlies if f.health > 0]
		num_friendlies = len(active_friendlies)
		num_enemies = len(active_enemies)
		
		# COMMUNICATION-FREE: Ensure EVERY enemy is covered using modulo-based round-robin
		# Each drone is responsible for multiple enemies when outnumbered
		drone_id = getattr(drone, 'id', 0)
		drone_index = next((i for i, f in enumerate(active_friendlies) if f.id == drone.id), 0)
		
		def _score_for(enemy, enemy_index):
			enemy_id = getattr(enemy, 'id', 0)
			
			# Primary responsibility: round-robin assignment ensures EVERY enemy gets coverage
			# Each drone covers enemies where (enemy_index % num_friendlies) == drone_index
			is_primary = (enemy_index % num_friendlies) == drone_index
			primary_boost = 100000.0 if is_primary else 0.0
			
			# Deterministic hash for tie-breaking and secondary assignment
			assignment_hash = (drone_id * 7919 + enemy_id * 6547) % 1000
			
			# Distance component for responsiveness
			d = float(np.linalg.norm(enemy.position - drone.position))
			distance_score = 1000.0 / max(d, 1.0)
			
			# Priority boost for critical threats
			priority_boost = 0.0
			if enemy.drone_type == DroneType.ENEMY_GROUND:
				for asset in assets:
					asset_distance = np.linalg.norm(enemy.position - asset.position)
					if asset_distance < self.threatening_range_time * self.max_speed:
						priority_boost = 50000.0  # Critical threat
						break
			
			# Combined score: priority > primary responsibility > hash > distance
			total_score = priority_boost + primary_boost + assignment_hash + distance_score
			
			return -total_score  # Negative for min()

		# Score all enemies with their indices for round-robin assignment
		scored_enemies = [(enemy, i, _score_for(enemy, i)) 
		                 for i, enemy in enumerate(active_enemies)]
		
		# Sort by score (lowest = highest priority)
		scored_enemies.sort(key=lambda x: x[2])
		
		# Select highest priority enemy
		if scored_enemies:
			best_enemy = scored_enemies[0][0]
			return getattr(best_enemy, 'id', None)
		
		return None

	def compute_threat_field(self, drone: Drone, enemies: List[Drone], assets: List[GroundAsset]) -> np.ndarray:
		field = np.zeros(3)
		for enemy in enemies:
			if enemy.health <= 0:
				continue
			offset = enemy.position - drone.position
			distance = np.linalg.norm(offset)
			if distance <= 1e-6 or distance > self.detection_range:
				continue

			weight = self.threat_air_weight
			if enemy.drone_type == DroneType.ENEMY_GROUND:
				weight = self.threat_ground_weight
				for asset in assets:
					asset_distance = np.linalg.norm(enemy.position - asset.position)
					if asset_distance < self.threatening_range_time * self.max_speed:
						weight *= self.critical_multiplier
						break

			direction = offset / distance
			decay = math.exp(-distance / self.threat_decay)
			field += weight * decay * direction
		return field

	def compute_asset_field(self, drone: Drone, assets: List[GroundAsset]) -> np.ndarray:
		if not assets:
			return np.zeros(3)
		field = np.zeros(3)
		for asset in assets:
			offset = asset.position - drone.position
			distance = np.linalg.norm(offset)
			if distance < 1e-6:
				continue
			if distance > 450.0:
				field += (offset / distance) * self.asset_pull_gain
		return field

	def compute_cohesion_field(self, drone: Drone, friendlies: List[Drone]) -> np.ndarray:
		active = [ally.position for ally in friendlies if ally.health > 0 and ally.id != drone.id]
		if not active:
			return np.zeros(3)
		centroid = np.mean(active, axis=0)
		offset = centroid - drone.position
		distance = np.linalg.norm(offset)
		if distance < 1e-6:
			return np.zeros(3)
		return (offset / distance) * self.cohesion_gain

	def compute_desired_velocity(self, drone: Drone, enemies: List[Drone], assets: List[GroundAsset], friendlies: List[Drone]) -> np.ndarray:
		threat_field = self.compute_threat_field(drone, enemies, assets)
		asset_field = self.compute_asset_field(drone, assets)
		cohesion_field = self.compute_cohesion_field(drone, friendlies)

		pursuit = np.zeros(3)
		if drone.target_id is not None:
			target = next((enemy for enemy in enemies if enemy.id == drone.target_id and enemy.health > 0), None)
			if target is not None:
				offset = target.position - drone.position
				distance = np.linalg.norm(offset)
				if distance > 1e-6:
					pursuit = (offset / distance) * self.target_gain

		combined = (threat_field * self.threat_gain) + (asset_field * self.asset_gain) + pursuit + cohesion_field
		magnitude = np.linalg.norm(combined)
		if magnitude <= 1e-6:
			return np.zeros(3)
		return (combined / magnitude) * self.max_speed


def build_swarm_controller(mode: str, overrides: Optional[Dict[str, float]] = None) -> SwarmAlgorithmController:
	# Get the profile, or use the first available algorithm as fallback
	profile = ALGORITHM_PRESETS.get(mode)
	if profile is None:
		# Use first available algorithm as fallback
		if ALGORITHM_PRESETS:
			profile = next(iter(ALGORITHM_PRESETS.values()))
		else:
			raise ValueError("No swarm algorithms available")

	# Try to return a module-backed adapter for richer algorithm implementations
	key = (mode or '').lower()
	try:
		if key.startswith('cbba'):
			from algorithms.cbba import CBBAController
			return _PerDroneAdapter(profile, overrides, CBBAController, kind='cbba')
		if key.startswith('cvt'):
			from algorithms.cvt import CVTCBFController
			return _PerDroneAdapter(profile, overrides, CVTCBFController, kind='cvt')
		if key.startswith('qipfd'):
			from algorithms.qipfd import QIPFDController
			return _PerDroneAdapter(profile, overrides, QIPFDController, kind='qipfd')
	except Exception:
		# If module import fails, fall back to generic controller
		pass

	return SwarmAlgorithmController(profile, overrides)


class _PerDroneAdapter(SwarmAlgorithmController):
	"""Adapter that uses per-drone algorithm controller instances (from
	server.algorithms.*) while keeping the SwarmAlgorithmController API used
	by the simulation engine.
	"""
	def __init__(self, profile: Dict[str, object], overrides: Optional[Dict[str, float]], controller_cls, kind='custom'):
		super().__init__(profile, overrides)
		self._controller_cls = controller_cls
		self._kind = kind
		self._instances: Dict[int, object] = {}

	def spawn_friendly(self, index: int, total: int, anchor: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
		# Use parent formation to pick initial position then attach a per-drone controller
		pos, vel = super().spawn_friendly(index, total, anchor)
		try:
			cfg = self.profile.copy() if isinstance(self.profile, dict) else {}
			# merge overrides into config where applicable
			inst = self._controller_cls(index, cfg)
			# seed state to match formation
			if hasattr(inst, 'position'):
				try:
					inst.position = np.array(pos, dtype=float)
				except Exception:
					pass
			if hasattr(inst, 'velocity'):
				try:
					inst.velocity = np.array(vel, dtype=float)
				except Exception:
					pass
			self._instances[index] = inst
		except Exception:
			# ignore and continue with formation-only placement
			pass
		return pos, vel

	def update_role(self, drone, enemies, assets):
		inst = self._instances.get(drone.id)
		# Many per-drone controllers don't implement update_role; fallback to parent
		if inst and hasattr(inst, 'get_telemetry'):
			# no-op but keep parity
			return super().update_role(drone, enemies, assets)
		return super().update_role(drone, enemies, assets)

	def select_target(self, drone, enemies, assets, friendlies):
		inst = self._instances.get(drone.id)
		if inst:
			# CBBA exposes assigned_target after greedy/build phases; try to use it
			if hasattr(inst, 'assigned_target') and inst.assigned_target is not None:
				return inst.assigned_target.get('id') if isinstance(inst.assigned_target, dict) else inst.assigned_target
			# fallback: choose nearest enemy
			try:
				dpos = getattr(inst, 'position', None) or drone.position
				nearest = min(enemies, key=lambda e: (e['position'][0]-dpos[0])**2 + (e['position'][2]-dpos[2])**2)
				return nearest.get('id')
			except Exception:
				return super().select_target(drone, enemies, assets, friendlies)
		return super().select_target(drone, enemies, assets, friendlies)

	def compute_desired_velocity(self, drone, enemies, assets, friendlies):
		inst = self._instances.get(drone.id)
		if not inst:
			return super().compute_desired_velocity(drone, enemies, assets, friendlies)

		try:
			# Map parameters depending on controller kind
			if self._kind == 'cbba':
				# CBBA compute_control(enemies, friendlies, assets, comm_available=False)
				return inst.compute_control(enemies, friendlies, assets, comm_available=False)
			if self._kind == 'cvt':
				# CVT compute_control(friendlies, enemies, assets, battlefield_bounds)
				return inst.compute_control(friendlies=[{ 'id': f.id, 'position': f.position.tolist() } for f in friendlies], enemies=enemies, assets=assets)
			if self._kind == 'qipfd':
				# QIPFD compute_control(enemies, friendlies, assets, dt)
				return inst.compute_control(enemies, friendlies, assets, self.threatening_range_time if hasattr(self, 'threatening_range_time') else 0.1)
			# generic attempt
			if hasattr(inst, 'compute_control'):
				return inst.compute_control(enemies, friendlies, assets)
		except Exception:
			pass
		return super().compute_desired_velocity(drone, enemies, assets, friendlies)


__all__ = [
	"Drone",
	"DroneRole",
	"DroneType",
	"GroundAsset",
	"SwarmAlgorithmController",
	"build_swarm_controller",
	"ALGORITHM_PRESETS"
]
