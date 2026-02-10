from flask import Flask, request, jsonify
from flask_cors import CORS
from simulation import SuperSimulation
from drone_swarm import ALGORITHM_PRESETS
import uuid
from threading import Thread, Lock
import time
import os
from dotenv import load_dotenv
import traceback
from dynamic_simulation import start_dynamic_simulation, get_dynamic_status, get_dynamic_data
from surveillance_system import get_surveillance_system, init_surveillance
from drone_config import (
    EMPTY_WEIGHT, MAX_TAKEOFF_WEIGHT, MAX_PAYLOAD,
    ENDURANCE_MIN_EMPTY, ENDURANCE_MIN_FULL, BATTERY_INITIAL, MAX_SPEED,
    BULLET_WEIGHT, MAX_BULLETS, TOTAL_AMMO_WEIGHT, MAX_PAYLOAD_KG,
    update_battery
)

# Supabase client (optional)
try:
    from supabase import create_client
except Exception:
    create_client = None

app = Flask(__name__)
CORS(app)

import logging

# Load environment variables for runtime toggles
load_dotenv()

def _parse_bool_env(name, default=False):
    v = os.environ.get(name)
    if v is None:
        return default
    return str(v).lower() in ('1', 'true', 'yes', 'on')

# Configure logging and API log toggle (can be controlled via env vars)
app.config['API_LOGS'] = _parse_bool_env('API_LOGS', True)
app.config['SUPABASE_VERBOSE'] = _parse_bool_env('SUPABASE_VERBOSE', False)

# Configure basic logging to stdout
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
if app.config.get('API_LOGS'):
    logging.getLogger('werkzeug').setLevel(logging.INFO)
else:
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
app.logger.setLevel(logging.INFO if app.config.get('API_LOGS') else logging.ERROR)

# Track persisted simulation IDs for debugging
app.config.setdefault('PERSISTED_SIMULATIONS', set())

simulations = {}
simulations_lock = Lock()

# Initialize surveillance system on startup
surveillance = None

def run_simulation_async(sim_id: str, config: dict):
    global surveillance
    
    # Pause surveillance when simulation starts
    if surveillance:
        surveillance.pause()
    
    try:
        sim = SuperSimulation(config)
        sim.initialize_scenario()
        if app.config.get('API_LOGS'):
            app.logger.info(f"Simulation {sim_id}: initialized engine (algorithm={config.get('swarm_algorithm')})")
        
        with simulations_lock:
            simulations[sim_id]['status'] = 'running'
            simulations[sim_id]['engine'] = sim
    except Exception as e:
        error_msg = f"Initialization failed: {str(e)}"
        app.logger.error(f"Simulation {sim_id}: {error_msg}")
        traceback.print_exc()
        with simulations_lock:
            simulations[sim_id]['status'] = 'error'
            simulations[sim_id]['statistics'] = {'error': error_msg}
        return
    
    # How often to persist progress to Supabase (seconds)
    persist_interval_s = float(config.get('persist_interval_s', 2.0))
    # How often to record history frames (every N steps)
    history_stride = 1  # Record EVERY frame for smooth playback

    max_steps = int(config.get('max_time', 120) / sim.dt)
    step_count = 0
    last_persist_time = time.time()
    last_persist_progress = 0.0
    
    try:
        while not sim.is_complete() and step_count < max_steps:
            # Only record full state every `history_stride` steps to reduce memory and IO
            record_frame = (step_count % max(1, history_stride) == 0)
            sim.step(record_frame)
            step_count += 1
            
            with simulations_lock:
                simulations[sim_id]['progress'] = (step_count / max_steps) * 100
            # Persist progress to Supabase (best-effort)
            # Persist progress to Supabase occasionally (best-effort) to avoid network per-step overhead
            try:
                now = time.time()
                progress = simulations[sim_id]['progress']
                # persist if enough time passed or progress jumped by >=1%
                if (now - last_persist_time) >= persist_interval_s or (progress - last_persist_progress) >= 1.0:
                    client = app.config.get('SUPABASE')
                    if client:
                        # Read current statistics, merge progress into JSONB `statistics` column
                        sel = client.table('simulations').select('statistics').eq('simulation_id', sim_id).execute()
                        cur_stats = None
                        try:
                            cur_stats = getattr(sel, 'data', sel)
                            if isinstance(cur_stats, list):
                                cur_stats = cur_stats[0].get('statistics') if cur_stats else {}
                            elif isinstance(cur_stats, dict):
                                cur_stats = cur_stats.get('statistics') or {}
                            else:
                                cur_stats = {}
                        except Exception:
                            cur_stats = {}

                        if cur_stats is None:
                            cur_stats = {}
                        cur_stats['progress'] = progress

                        res = client.table('simulations').update({
                            'statistics': cur_stats,
                            'updated_at': 'now()'
                        }).eq('simulation_id', sim_id).execute()
                        if app.config.get('SUPABASE_VERBOSE'):
                            print(f"[Supabase] progress->statistics update for {sim_id}: {getattr(res, 'data', res)}")
                        if app.config.get('API_LOGS'):
                            app.logger.info(f"Simulation {sim_id}: progress {progress:.2f}% (persisted)")

                    last_persist_time = now
                    last_persist_progress = progress
            except Exception as e:
                if app.config.get('SUPABASE_VERBOSE'):
                    print(f"[Supabase] progress update failed for {sim_id}: {e}")
                    traceback.print_exc()
                if app.config.get('API_LOGS'):
                    app.logger.error(f"Simulation {sim_id}: progress update failed: {e}")
        
        with simulations_lock:
            simulations[sim_id]['status'] = 'completed'
            simulations[sim_id]['statistics'] = sim.get_statistics()
        if app.config.get('API_LOGS'):
            app.logger.info(f"Simulation {sim_id}: completed; statistics set")
        
        # Resume surveillance after simulation completes
        if surveillance:
            surveillance.resume()
    
    except Exception as e:
        error_msg = f"Simulation loop failed: {str(e)}"
        app.logger.error(f"Simulation {sim_id}: {error_msg}")
        traceback.print_exc()
        with simulations_lock:
            simulations[sim_id]['status'] = 'error'
            simulations[sim_id]['statistics'] = {'error': error_msg}
        return

    # Persist final results (frames + statistics) to Supabase (best-effort)
    try:
        client = app.config.get('SUPABASE')
        if client:
            payload = {
                'status': 'completed',
                'statistics': simulations[sim_id]['statistics'],
                'frames': sim.history,
                'completed_at': 'now()',
                'updated_at': 'now()'
            }
            res = client.table('simulations').update(payload).eq('simulation_id', sim_id).execute()
            if app.config.get('SUPABASE_VERBOSE'):
                print(f"[Supabase] final results update for {sim_id}: {getattr(res, 'data', res)}")
            if app.config.get('API_LOGS'):
                app.logger.info(f"Simulation {sim_id}: final results update persisted to Supabase")
    except Exception as e:
        if app.config.get('SUPABASE_VERBOSE'):
            print(f"[Supabase] final results persist failed for {sim_id}: {e}")
            traceback.print_exc()
        if app.config.get('API_LOGS'):
            app.logger.error(f"Simulation {sim_id}: final results persist failed: {e}")

    # Also persist a derived algorithm_performance row now that simulation is complete
    try:
        client = app.config.get('SUPABASE')
        if client:
            stats = simulations[sim_id].get('statistics') or {}

            # derive simple metrics similar to analytics endpoint
            avg_response_time = None
            try:
                history = sim.history or []
                if len(history) > 1:
                    timestamps = [f.get('time', i) for i, f in enumerate(history)]
                    deltas = [j - i for i, j in zip(timestamps[:-1], timestamps[1:])]
                    if deltas:
                        avg_response_time = sum(deltas) / len(deltas)
            except Exception:
                avg_response_time = None

            target_accuracy = None
            try:
                kr = stats.get('kill_ratio', None)
                if kr is not None:
                    target_accuracy = min(1.0, kr / (kr + 1.0))
            except Exception:
                target_accuracy = None

            formation_efficiency = None
            try:
                assets_total = 0
                if sim.history:
                    first = sim.history[0] if sim.history else {}
                    assets_total = len(first.get('assets', [])) if isinstance(first, dict) else 0
                protected = stats.get('assets_protected', None)
                if assets_total and protected is not None:
                    formation_efficiency = protected / assets_total
            except Exception:
                formation_efficiency = None

            # Start with simulation-level values
            perf = {
                'simulation_id': sim_id,
                'algorithm_name': simulations[sim_id].get('config', {}).get('swarm_algorithm'),
                'avg_response_time': avg_response_time,
                'target_accuracy': target_accuracy,
                'formation_efficiency': formation_efficiency,
                'created_at': 'now()'
            }

            # Prefer runtime telemetry reported by the algorithm controller when available
            try:
                runtime_telemetry = {}
                engine = simulations[sim_id].get('engine')
                if engine and hasattr(engine, 'get_algorithm_telemetry'):
                    runtime_telemetry = engine.get_algorithm_telemetry() or {}

                # Values hierarchy: runtime telemetry -> simulation.config.algorithm_params -> simulation.config -> sensible defaults
                cfg = simulations[sim_id].get('config', {}) or {}
                algo_params = cfg.get('algorithm_params', {}) or {}

                def _pick_int(key, default):
                    return int(runtime_telemetry.get(key)
                               or algo_params.get(key)
                               or cfg.get(key)
                               or default)

                def _pick_float(key, default):
                    return float(runtime_telemetry.get(key)
                                 or algo_params.get(key)
                                 or cfg.get(key)
                                 or default)

                perf['pso_iterations'] = _pick_int('pso_iterations', 1)
                perf['aco_pheromone_strength'] = _pick_float('aco_pheromone_strength', 0.1)
                perf['abc_scout_count'] = _pick_int('abc_scout_count', 1)
            except Exception:
                # Fallback defaults if anything goes wrong
                perf.setdefault('pso_iterations', 1)
                perf.setdefault('aco_pheromone_strength', 0.1)
                perf.setdefault('abc_scout_count', 1)

            pres = client.table('algorithm_performance').insert(perf).execute()
            if app.config.get('SUPABASE_VERBOSE'):
                print(f"[Supabase] algorithm_performance insert for {sim_id}: {getattr(pres, 'data', pres)}")
            if app.config.get('API_LOGS'):
                app.logger.info(f"Simulation {sim_id}: algorithm_performance row inserted")
            try:
                app.config['PERSISTED_SIMULATIONS'].add(sim_id)
            except Exception:
                pass
            # Persist a derived swarm analytics row for easy reporting/BI
            try:
                stats = simulations[sim_id].get('statistics') or {}
                analytics_payload = {
                    'simulation_id': sim_id,
                    'algorithm_name': simulations[sim_id].get('config', {}).get('swarm_algorithm'),
                    'duration': float(stats.get('duration') or sim.time if 'sim' in locals() else stats.get('duration') or 0.0),
                    'friendly_losses': int(stats.get('friendly_losses') or 0),
                    'enemy_losses': int(stats.get('enemy_losses') or 0),
                    'survival_rate': float(stats.get('survival_rate') or 0.0),
                    'kill_ratio': float(stats.get('kill_ratio') or 0.0),
                    'assets_protected': int(stats.get('assets_protected') or 0),
                    'mission_success': bool(stats.get('mission_success') or False),
                    'telemetry': {
                        'pso_iterations': perf.get('pso_iterations'),
                        'aco_pheromone_strength': perf.get('aco_pheromone_strength'),
                        'abc_scout_count': perf.get('abc_scout_count')
                    },
                    'statistics': stats,
                    'created_at': 'now()'
                }
                anres = client.table('swarm_analytics').insert(analytics_payload).execute()
                if app.config.get('SUPABASE_VERBOSE'):
                    print(f"[Supabase] swarm_analytics insert for {sim_id}: {getattr(anres, 'data', anres)}")
                if app.config.get('API_LOGS'):
                    app.logger.info(f"Simulation {sim_id}: swarm_analytics row inserted")
            except Exception as e:
                if app.config.get('SUPABASE_VERBOSE'):
                    print(f"[Supabase] swarm_analytics insert failed for {sim_id}: {e}")
                    traceback.print_exc()
    except Exception as e:
        if app.config.get('SUPABASE_VERBOSE'):
            print(f"[Supabase] final performance persist failed for {sim_id}: {e}")
            traceback.print_exc()

@app.route('/api/scenarios/presets', methods=['GET'])
def get_presets():
    """GUARANTEED WIN presets"""
    presets = {
        'guaranteed_win': {
            'name': '⭐ GUARANTEED WIN (Start Here)',
            'friendly_count': 25,
            'enemy_count': 10,
            'ground_attack_ratio': 0.3,
            'max_time': 300,  # Increased for longer battles
            'max_speed': 70.0,
            'weapon_range': 150.0,
            'detection_range': 1500.0,
            'assets': [{'position': [0, 0, 0], 'value': 1.0}]
        },
        'easy': {
            'name': '⭐⭐ Easy Mode',
            'friendly_count': 20,
            'enemy_count': 12,
            'ground_attack_ratio': 0.35,
            'max_time': 300,  # Increased
            'max_speed': 70.0,
            'weapon_range': 150.0,
            'detection_range': 1500.0,
            'assets': [{'position': [0, 0, 0], 'value': 1.0}]
        },
        'balanced': {
            'name': '⭐⭐⭐ Balanced',
            'friendly_count': 18,
            'enemy_count': 15,
            'ground_attack_ratio': 0.4,
            'max_time': 300,  # Increased
            'max_speed': 70.0,
            'weapon_range': 150.0,
            'detection_range': 1500.0,
            'assets': [{'position': [0, 0, 0], 'value': 1.0}]
        },
        'challenging': {
            'name': '⭐⭐⭐⭐ Challenging',
            'friendly_count': 16,
            'enemy_count': 18,
            'ground_attack_ratio': 0.45,
            'max_time': 300,  # Increased
            'max_speed': 70.0,
            'weapon_range': 150.0,
            'detection_range': 1500.0,
            'assets': [{'position': [0, 0, 0], 'value': 1.0}]
        }
    }
    return jsonify(presets)


@app.route('/api/algorithms', methods=['GET'])
def get_algorithms():
    """Return available swarm algorithm presets and metadata."""
    try:
        items = []
        for key, meta in ALGORITHM_PRESETS.items():
            label = meta.get('label') if isinstance(meta.get('label'), str) else key.replace('-', ' ').title()
            description = meta.get('description') or (str(meta.get('formation', '')).capitalize() or '')
            items.append({
                'value': key,
                'label': label,
                'description': description
            })
        return jsonify(items)
    except Exception:
        return jsonify([])

@app.route('/api/simulation/start', methods=['POST'])
def start_simulation():
    config = request.json
    sim_id = str(uuid.uuid4())
    
    with simulations_lock:
        simulations[sim_id] = {
            'id': sim_id,
            'status': 'initializing',
            'progress': 0,
            'config': config,
            'engine': None,
            'statistics': None
        }
    # Persist initial simulation record to Supabase (best-effort)
    try:
        client = app.config.get('SUPABASE')
        if client:
            # store initial progress inside `statistics` JSONB so we don't require schema change
            res = client.table('simulations').insert({
                'simulation_id': sim_id,
                'config': config,
                'status': 'initializing',
                'statistics': {'progress': 0}
            }).execute()
            if app.config.get('SUPABASE_VERBOSE'):
                print(f"[Supabase] insert response for {sim_id}: {getattr(res, 'data', res)}")
            try:
                app.config['PERSISTED_SIMULATIONS'].add(sim_id)
            except Exception as e:
                if app.config.get('SUPABASE_VERBOSE'):
                    print(f"[Supabase] failed to record persisted id in memory: {e}")
                    traceback.print_exc()
    except Exception as e:
        if app.config.get('SUPABASE_VERBOSE'):
            print(f"[Supabase] initial insert failed for {sim_id}: {e}")
            traceback.print_exc()
    
    thread = Thread(target=run_simulation_async, args=(sim_id, config))
    thread.start()
    
    return jsonify({'simulation_id': sim_id})

@app.route('/api/simulation/<sim_id>/status', methods=['GET'])
def get_simulation_status(sim_id):
    with simulations_lock:
        if sim_id not in simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        sim = simulations[sim_id]
        if app.config.get('API_LOGS'):
            app.logger.info(f"API: status requested for {sim_id} -> {sim['status']} ({sim['progress']:.2f}%)")
        return jsonify({
            'id': sim_id,
            'status': sim['status'],
            'progress': sim['progress'],
            'statistics': sim['statistics']
        })


def init_supabase():
    """Initialize Supabase client from environment variables (optional)."""
    load_dotenv()
    supabase_url = os.environ.get('URL') or os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('ANON_KEY') or os.environ.get('SUPABASE_KEY')
    if create_client and supabase_url and supabase_key:
        try:
            client = create_client(supabase_url, supabase_key)
            app.config['SUPABASE'] = client
        except Exception:
            app.config['SUPABASE'] = None
    else:
        app.config['SUPABASE'] = None


# Flask 3 removed `before_first_request`; prefer `before_serving` when available.
if hasattr(app, 'before_serving'):
    @app.before_serving
    def _init_supabase_before_serving():
        init_supabase()
else:
    # Fallback: run at import time so config is available when app starts.
    init_supabase()

@app.route('/api/simulation/<sim_id>/data', methods=['GET'])
def get_simulation_data(sim_id):
    with simulations_lock:
        if sim_id not in simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        sim = simulations[sim_id]
        if sim['engine'] is None:
            return jsonify({'error': 'Simulation not started'}), 400
        
        start_frame = int(request.args.get('start', 0))
        end_frame = int(request.args.get('end', len(sim['engine'].history)))
        
        history_slice = sim['engine'].history[start_frame:end_frame]
        
        return jsonify({
            'frames': history_slice,
            'total_frames': len(sim['engine'].history),
            'config': sim['config']
        })

@app.route('/api/simulation/<sim_id>/analytics', methods=['GET'])
def get_analytics(sim_id):
    with simulations_lock:
        if sim_id not in simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        sim = simulations[sim_id]
        if sim['engine'] is None:
            return jsonify({'error': 'Simulation not started'}), 400
        
        engine = sim['engine']
        if app.config.get('API_LOGS'):
            app.logger.info(f"API: analytics requested for {sim_id}")
        history = engine.history
        
        friendly_count = []
        enemy_count = []
        timestamps = []
        
        for frame in history[::10]:
            timestamps.append(frame['time'])
            friendly_count.append(sum(1 for d in frame['friendlies'] if d['health'] > 0))
            enemy_count.append(sum(1 for d in frame['enemies'] if d['health'] > 0))
        
        role_distribution = {'hunter': [], 'defender': [], 'interceptor': []}
        for frame in history[::10]:
            roles = {'hunter': 0, 'defender': 0, 'interceptor': 0}
            for d in frame['friendlies']:
                if d['health'] > 0 and d['role']:
                    roles[d['role']] += 1
            for role in role_distribution:
                role_distribution[role].append(roles[role])
        
        response = {
            'timestamps': timestamps,
            'friendly_count': friendly_count,
            'enemy_count': enemy_count,
            'role_distribution': role_distribution,
            'statistics': sim['statistics']
        }

        # After computing analytics, persist a performance row to Supabase (best-effort)
        try:
            client = app.config.get('SUPABASE')
            if client:
                stats = sim.get('statistics') or {}
                # derive simple metrics
                avg_response_time = None
                if len(timestamps) > 1:
                    deltas = [j - i for i, j in zip(timestamps[:-1], timestamps[1:])]
                    avg_response_time = sum(deltas) / len(deltas)

                target_accuracy = None
                try:
                    kr = stats.get('kill_ratio', None)
                    if kr is not None:
                        target_accuracy = min(1.0, kr / (kr + 1.0))
                except Exception:
                    target_accuracy = None

                formation_efficiency = None
                try:
                    assets_total = len(engine.history[0].get('assets', [])) if engine.history else 0
                    protected = stats.get('assets_protected', None)
                    if assets_total and protected is not None:
                        formation_efficiency = protected / assets_total
                except Exception:
                    formation_efficiency = None

                perf = {
                    'simulation_id': sim_id,
                    'algorithm_name': sim['config'].get('swarm_algorithm') if sim.get('config') else None,
                    'avg_response_time': avg_response_time,
                    'target_accuracy': target_accuracy,
                    'formation_efficiency': formation_efficiency,
                    'created_at': 'now()'
                }
                client.table('algorithm_performance').insert(perf).execute()
        except Exception as e:
            if app.config.get('SUPABASE_VERBOSE'):
                print(f"[Supabase] analytics insert failed for {sim_id}: {e}")
                traceback.print_exc()

        return jsonify(response)


@app.route('/api/debug/supabase', methods=['GET'])
def debug_supabase():
    """Return whether Supabase client is configured and which simulation IDs were persisted."""
    client = app.config.get('SUPABASE')
    enabled = bool(client)
    persisted = list(app.config.get('PERSISTED_SIMULATIONS', set()))
    return jsonify({'enabled': enabled, 'persisted_simulations': persisted, 'url': os.environ.get('URL')})


@app.route('/api/debug/simulations', methods=['GET'])
def debug_simulations():
    """Return a lightweight summary of in-memory simulations for debugging."""
    with simulations_lock:
        out = []
        for sid, info in simulations.items():
            out.append({
                'simulation_id': sid,
                'status': info.get('status'),
                'progress': info.get('progress'),
                'has_engine': info.get('engine') is not None,
                'statistics': info.get('statistics')
            })
    return jsonify(out)


# ============================================================================
# SURVEILLANCE SYSTEM API - Continuous drone surveillance
# ============================================================================

@app.route('/api/surveillance/status', methods=['GET'])
def get_surveillance_status():
    """Get current surveillance system status and drone positions"""
    global surveillance
    if surveillance is None:
        return jsonify({
            'active': False,
            'drones': [],
            'message': 'Surveillance system not active'
        })
    
    return jsonify(surveillance.get_state())


@app.route('/api/surveillance/start', methods=['POST'])
def start_surveillance():
    """Start or restart surveillance system"""
    global surveillance
    
    data = request.json or {}
    center_position = data.get('center_position', [0, 0, 0])
    patrol_radius = data.get('patrol_radius', 500.0)
    
    surveillance = init_surveillance(center_position, patrol_radius)
    
    return jsonify({
        'status': 'started',
        'center_position': center_position,
        'patrol_radius': patrol_radius,
        'drones': 3
    })


@app.route('/api/surveillance/stop', methods=['POST'])
def stop_surveillance():
    """Stop surveillance system"""
    global surveillance
    if surveillance:
        surveillance.stop()
        return jsonify({'status': 'stopped'})
    return jsonify({'status': 'not_running'})


@app.route('/api/surveillance/patrol-area', methods=['POST'])
def set_patrol_area():
    """Update surveillance patrol area"""
    global surveillance
    if surveillance is None:
        return jsonify({'error': 'Surveillance system not initialized'}), 404
    
    data = request.json or {}
    center_position = data.get('center_position', [0, 0, 0])
    patrol_radius = data.get('patrol_radius', 500.0)
    
    surveillance.set_patrol_area(center_position, patrol_radius)
    
    return jsonify({
        'status': 'updated',
        'center_position': center_position,
        'patrol_radius': patrol_radius
    })


@app.route('/api/simulation/<sim_id>/spawn-enemy', methods=['POST'])
def spawn_enemy(sim_id):
    """Spawn a new enemy drone at the specified position during ACTIVE simulation run"""
    with simulations_lock:
        if sim_id not in simulations:
            return jsonify({'error': 'Simulation not found'}), 404
        
        sim = simulations[sim_id]
        if sim['engine'] is None:
            return jsonify({'error': 'Simulation not started'}), 400
        
        # Only allow spawning during active simulation (not during playback)
        if sim['status'] != 'running':
            return jsonify({'error': f'Can only spawn during active simulation. Current status: {sim["status"]}'}), 400
        
        engine = sim['engine']
        data = request.json or {}
        
        # Get spawn position from request
        position = data.get('position', [0, 100, 0])
        enemy_type = data.get('type', 'air')  # 'air' or 'ground'
        
        # Import necessary classes
        from drone_swarm import Drone, DroneType
        import numpy as np
        
        # Create new enemy drone
        new_enemy_id = 2000 + len(engine.enemies)  # IDs starting from 2000
        
        drone_type = DroneType.ENEMY_GROUND if enemy_type == 'ground' else DroneType.ENEMY_AIR
        
        # Calculate velocity towards nearest asset or friendly
        target_pos = None
        if enemy_type == 'ground' and engine.assets:
            target_pos = engine.assets[0].position
        elif engine.friendlies:
            active_friendlies = [f for f in engine.friendlies if f.health > 0]
            if active_friendlies:
                target_pos = active_friendlies[0].position
        
        velocity = np.zeros(3)
        if target_pos is not None:
            direction = target_pos - np.array(position)
            distance = np.linalg.norm(direction)
            if distance > 0:
                velocity = (direction / distance) * 40.0
        
        new_enemy = Drone(
            id=new_enemy_id,
            position=np.array(position, dtype=float),
            velocity=velocity,
            drone_type=drone_type,
            health=80.0
        )
        
        engine.enemies.append(new_enemy)
        
        if app.config.get('API_LOGS'):
            app.logger.info(f"Spawned new {enemy_type} enemy {new_enemy_id} at {position}")
        
        return jsonify({
            'success': True,
            'enemy_id': new_enemy_id,
            'position': position,
            'type': enemy_type
        })


@app.route('/api/dynamic/start', methods=['POST'])
def start_dynamic():
    """Start a dynamic (moving-asset) simulation. Uses `server/dynamic_simulation.py` and
    keeps the dynamic sim separate from the existing `simulations` to avoid touching old code."""
    config = request.json or {}
    sim_id = start_dynamic_simulation(config)
    return jsonify({'simulation_id': sim_id})


@app.route('/api/dynamic/<sim_id>/status', methods=['GET'])
def dynamic_status(sim_id):
    res = get_dynamic_status(sim_id)
    if 'error' in res:
        return jsonify({'error': 'Simulation not found'}), 404
    return jsonify(res)


@app.route('/api/dynamic/<sim_id>/data', methods=['GET'])
def dynamic_data(sim_id):
    start = int(request.args.get('start', 0))
    end = request.args.get('end')
    endi = int(end) if end is not None else None
    res = get_dynamic_data(sim_id, start, endi)
    if 'error' in res:
        return jsonify({'error': 'Simulation not found'}), 404
    return jsonify(res)


# ============================================================================
# DRONE TELEMETRY API - Real-time Drone Monitoring
# ============================================================================

# Simulated drone telemetry data storage
drone_telemetry = {
    'battery_percentage': BATTERY_INITIAL,
    'current_weight': EMPTY_WEIGHT + TOTAL_AMMO_WEIGHT,  # Start with full ammo
    'bullets_remaining': MAX_BULLETS,
    'last_updated': time.time(),
    'flight_start_time': time.time(),
    'state': 'ready'
}
telemetry_lock = Lock()


def _derive_drone_state(battery_pct: float, bullets_remaining: int, flight_elapsed: float) -> str:
    """Map telemetry readings to a coarse drone state for UI consumption."""
    if battery_pct <= 0:
        return 'powered_down'
    if battery_pct < 10:
        return 'emergency_rtb'
    if battery_pct < 30:
        return 'rtb_low_battery'
    if bullets_remaining <= 0:
        return 'needs_reload'
    if flight_elapsed < 10:
        return 'launch'
    return 'airborne'


@app.route('/api/drone/battery', methods=['GET'])
def get_drone_battery():
    """
    GET request to retrieve current battery percentage of the drone.
    Battery drains based on current bullet count and flight time.
    
    Empty payload (0 bullets) = 90 min flight time
    Full payload (250 bullets) = 60 min flight time
    
    Example:
    GET http://localhost:5000/api/drone/battery
    
    Response:
    {
        "battery_percentage": 95.5,
        "status": "healthy",
        "timestamp": 1733655468.123,
        "estimated_flight_time_minutes": 71.6,
        "current_weight_kg": 10.5,
        "bullets_remaining": 250,
        "flight_time_elapsed_seconds": 120.5
    }
    """
    with telemetry_lock:
        # Calculate time elapsed since last update
        current_time = time.time()
        dt_seconds = current_time - drone_telemetry['last_updated']
        
        # Update battery using the new formula
        bullets = drone_telemetry['bullets_remaining']
        current_battery = update_battery(
            drone_telemetry['battery_percentage'],
            bullets,
            dt_seconds
        )
        
        # Update stored values
        drone_telemetry['battery_percentage'] = current_battery
        drone_telemetry['last_updated'] = current_time
        
        # Calculate current weight
        current_weight = EMPTY_WEIGHT + (bullets * BULLET_WEIGHT)
        drone_telemetry['current_weight'] = current_weight
        
        # Calculate flight time elapsed
        flight_elapsed = current_time - drone_telemetry['flight_start_time']
        
        # Determine battery status
        if current_battery > 75:
            status = "healthy"
        elif current_battery > 30:
            status = "warning"
        elif current_battery > 10:
            status = "critical"
        else:
            status = "emergency"
        
        # Calculate endurance based on current payload
        payload_kg = bullets * BULLET_WEIGHT
        payload_fraction = max(0.0, min(1.0, payload_kg / MAX_PAYLOAD_KG))
        endurance_min = ENDURANCE_MIN_EMPTY - \
                        (ENDURANCE_MIN_EMPTY - ENDURANCE_MIN_FULL) * payload_fraction
        
        # Calculate estimated remaining flight time
        estimated_time = (current_battery / 100.0) * endurance_min
        drone_state = _derive_drone_state(current_battery, bullets, flight_elapsed)
        drone_telemetry['state'] = drone_state
        
        return jsonify({
            'battery_percentage': round(current_battery, 2),
            'status': status,
            'state': drone_state,
            'timestamp': current_time,
            'estimated_flight_time_minutes': round(estimated_time, 1),
            'total_flight_capacity_minutes': round(endurance_min, 1),
            'current_weight_kg': round(current_weight, 2),
            'bullets_remaining': bullets,
            'flight_time_elapsed_seconds': round(flight_elapsed, 2)
        })


@app.route('/api/drone/drain', methods=['POST'])
def drain_battery():
    """
    POST request to simulate battery drain and get current battery percentage.
    Battery drains based on:
    - Flight time (continuous drain based on bullet count)
    - Speed: 10 m/s
    - Bullet payload affects drain rate
    
    Empty payload (0 bullets) = 90 min flight time
    Full payload (250 bullets) = 60 min flight time
    
    Example:
    POST http://localhost:5000/api/drone/drain
    
    Optional Body:
    {
        "flight_duration_seconds": 10
    }
    
    Response:
    {
        "battery_percentage": 95.5,
        "status": "healthy",
        "current_weight_kg": 10.5,
        "bullets_remaining": 250,
        "estimated_flight_time_minutes": 71.6,
        "total_flight_capacity_minutes": 72.0,
        "distance_traveled_km": 0.1,
        "timestamp": 1733655478.456
    }
    """
    with telemetry_lock:
        # Get optional flight duration and weight from request
        flight_duration = 0
        weight_override = None
        if request.json:
            if 'flight_duration_seconds' in request.json:
                flight_duration = float(request.json['flight_duration_seconds'])
            if 'current_weight_kg' in request.json:
                try:
                    weight_override = float(request.json['current_weight_kg'])
                except (TypeError, ValueError):
                    weight_override = None
        
        # Calculate time elapsed since last update
        current_time = time.time()
        dt_seconds = current_time - drone_telemetry['last_updated']
        
        # Add manual flight duration if provided
        total_time = dt_seconds + flight_duration
        
        # Update battery using the new formula
        bullets = drone_telemetry['bullets_remaining']
        current_battery = update_battery(
            drone_telemetry['battery_percentage'],
            bullets,
            total_time,
            current_weight_kg=weight_override or drone_telemetry.get('current_weight')
        )
        
        # Update stored values
        drone_telemetry['battery_percentage'] = current_battery
        drone_telemetry['last_updated'] = current_time
        
        # Calculate current weight
        if weight_override is not None:
            current_weight = max(EMPTY_WEIGHT, min(MAX_TAKEOFF_WEIGHT, weight_override))
        else:
            current_weight = EMPTY_WEIGHT + (bullets * BULLET_WEIGHT)
        drone_telemetry['current_weight'] = current_weight
        
        # Calculate flight time elapsed
        flight_elapsed = current_time - drone_telemetry['flight_start_time']
        
        # Calculate distance traveled (speed = 10 m/s)
        distance_meters = total_time * MAX_SPEED
        distance_km = distance_meters / 1000.0
        
        # Determine battery status
        if current_battery > 75:
            status = "healthy"
        elif current_battery > 30:
            status = "warning"
        elif current_battery > 10:
            status = "critical"
        else:
            status = "emergency"
        
        # Calculate endurance based on current payload
        payload_kg = bullets * BULLET_WEIGHT
        payload_fraction = max(0.0, min(1.0, payload_kg / MAX_PAYLOAD_KG))
        endurance_min = ENDURANCE_MIN_EMPTY - \
                        (ENDURANCE_MIN_EMPTY - ENDURANCE_MIN_FULL) * payload_fraction
        
        # Calculate estimated remaining flight time
        estimated_time = (current_battery / 100.0) * endurance_min
        drone_state = _derive_drone_state(current_battery, bullets, flight_elapsed)
        drone_telemetry['state'] = drone_state
        
        return jsonify({
            'battery_percentage': round(current_battery, 2),
            'status': status,
            'state': drone_state,
            'current_weight_kg': round(current_weight, 2),
            'bullets_remaining': bullets,
            'estimated_flight_time_minutes': round(estimated_time, 1),
            'total_flight_capacity_minutes': round(endurance_min, 1),
            'flight_time_elapsed_seconds': round(flight_elapsed, 2),
            'distance_traveled_km': round(distance_km, 3),
            'timestamp': current_time
        })


@app.route('/api/drone/fire', methods=['POST'])
def fire_bullet():
    """
    POST request to fire a bullet and reduce drone weight.
    Each bullet weighs 10 grams (0.01 kg).
    Maximum 250 bullets capacity.
    Weight reduction affects battery drain rate.
    
    Example:
    POST http://localhost:5000/api/drone/fire
    
    Optional Body:
    {
        "bullets_fired": 1
    }
    
    Response:
    {
        "message": "Fired 1 bullet(s)",
        "bullets_remaining": 249,
        "current_weight_kg": 10.49,
        "weight_reduced_kg": 0.01,
        "battery_percentage": 95.5,
        "estimated_flight_time_minutes": 75.2,
        "timestamp": 1733655468.123
    }
    """
    with telemetry_lock:
        # Get number of bullets to fire (default = 1)
        bullets_fired = 1
        if request.json and 'bullets_fired' in request.json:
            bullets_fired = int(request.json['bullets_fired'])
        
        # Check if enough bullets remaining
        if drone_telemetry['bullets_remaining'] < bullets_fired:
            return jsonify({
                'error': 'Not enough bullets',
                'bullets_remaining': drone_telemetry['bullets_remaining'],
                'bullets_requested': bullets_fired
            }), 400
        
        # Reduce bullets
        drone_telemetry['bullets_remaining'] -= bullets_fired
        weight_reduced = BULLET_WEIGHT * bullets_fired
        
        # Recalculate weight
        bullets = drone_telemetry['bullets_remaining']
        current_weight = EMPTY_WEIGHT + (bullets * BULLET_WEIGHT)
        drone_telemetry['current_weight'] = current_weight
        
        current_time = time.time()
        current_battery = drone_telemetry['battery_percentage']
        flight_elapsed = current_time - drone_telemetry['flight_start_time']
        drone_state = _derive_drone_state(current_battery, bullets, flight_elapsed)
        drone_telemetry['state'] = drone_state
        
        # Calculate new endurance based on reduced payload
        payload_kg = bullets * BULLET_WEIGHT
        payload_fraction = max(0.0, min(1.0, payload_kg / MAX_PAYLOAD_KG))
        endurance_min = ENDURANCE_MIN_EMPTY - \
                        (ENDURANCE_MIN_EMPTY - ENDURANCE_MIN_FULL) * payload_fraction
        
        # Calculate estimated remaining flight time
        estimated_time = (current_battery / 100.0) * endurance_min
        
        return jsonify({
            'message': f'Fired {bullets_fired} bullet(s)',
            'bullets_remaining': bullets,
            'current_weight_kg': round(current_weight, 2),
            'weight_reduced_kg': round(weight_reduced, 3),
            'battery_percentage': round(current_battery, 2),
            'estimated_flight_time_minutes': round(estimated_time, 1),
            'total_flight_capacity_minutes': round(endurance_min, 1),
            'state': drone_state,
            'timestamp': current_time
        })


@app.route('/api/drone/weight', methods=['POST'])
def get_drone_weight():
    """
    POST request to retrieve current weight of the drone.
    Automatically updates simulation every 10 seconds.
    
    Example:
    POST http://localhost:5000/api/drone/weight
    
    Response:
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
    """
    with telemetry_lock:
        # Simulate weight fluctuation over time (simulate payload changes every 10s)
        time_elapsed = time.time() - drone_telemetry['last_updated']
        
        # If more than 10 seconds have passed, simulate minor weight change
        if time_elapsed >= 10.0:
            # Random payload fluctuation between -0.2 to +0.2 kg (simulates fuel consumption, minor adjustments)
            import random
            weight_change = random.uniform(-0.2, 0.2)
            new_weight = drone_telemetry['current_weight'] + weight_change
            drone_telemetry['current_weight'] = max(
                EMPTY_WEIGHT,
                min(MAX_TAKEOFF_WEIGHT, new_weight)
            )
            drone_telemetry['last_updated'] = time.time()
        
        # Calculate payload weight
        current_weight = drone_telemetry['current_weight']
        payload_weight = current_weight - EMPTY_WEIGHT
        weight_percentage = (current_weight / MAX_TAKEOFF_WEIGHT) * 100
        
        # Validate payload doesn't exceed limit
        if payload_weight > MAX_PAYLOAD:
            weight_status = "overload"
        elif weight_percentage < 70:
            weight_status = "optimal"
        elif weight_percentage < 90:
            weight_status = "acceptable"
        else:
            weight_status = "maximum"
        
        return jsonify({
            'current_weight': round(current_weight, 2),
            'empty_weight': EMPTY_WEIGHT,
            'max_weight': MAX_TAKEOFF_WEIGHT,
            'payload_weight': round(payload_weight, 2),
            'max_payload': MAX_PAYLOAD,
            'weight_percentage': round(weight_percentage, 1),
            'weight_status': weight_status,
            'timestamp': drone_telemetry['last_updated'],
            'remaining_capacity': round(MAX_TAKEOFF_WEIGHT - current_weight, 2),
            'time_since_last_update': round(time_elapsed, 2)
        })


@app.route('/api/formulas/battery', methods=['POST'])
def calculate_battery():
    """
    POST request to calculate battery drain using the battery formula.
    
    Example:
    POST http://localhost:5000/api/formulas/battery
    
    Body:
    {
        "battery_percent": 100.0,
        "bullets": 250,
        "dt_seconds": 60.0
    }
    
    Response:
    {
        "initial_battery": 100.0,
        "final_battery": 98.61,
        "battery_drained": 1.39,
        "bullets": 250,
        "time_elapsed_seconds": 60.0,
        "payload_kg": 2.5,
        "endurance_minutes": 60.0,
        "estimated_flight_time_minutes": 59.17
    }
    """
    data = request.json or {}
    
    # Get parameters from request
    battery_percent = float(data.get('battery_percent', 100.0))
    bullets = int(data.get('bullets', 0))
    dt_seconds = float(data.get('dt_seconds', 0.0))
    
    # Validate inputs
    if battery_percent < 0 or battery_percent > 100:
        return jsonify({'error': 'battery_percent must be between 0 and 100'}), 400
    if bullets < 0 or bullets > MAX_BULLETS:
        return jsonify({'error': f'bullets must be between 0 and {MAX_BULLETS}'}), 400
    if dt_seconds < 0:
        return jsonify({'error': 'dt_seconds must be non-negative'}), 400
    
    # Calculate payload and endurance
    payload_kg = bullets * BULLET_WEIGHT
    payload_fraction = max(0.0, min(1.0, payload_kg / MAX_PAYLOAD_KG))
    endurance_min = ENDURANCE_MIN_EMPTY - \
                    (ENDURANCE_MIN_EMPTY - ENDURANCE_MIN_FULL) * payload_fraction
    
    # Calculate new battery level
    new_battery = update_battery(battery_percent, bullets, dt_seconds)
    battery_drained = battery_percent - new_battery
    
    # Calculate estimated remaining flight time
    estimated_time = (new_battery / 100.0) * endurance_min
    
    return jsonify({
        'initial_battery': round(battery_percent, 2),
        'final_battery': round(new_battery, 2),
        'battery_drained': round(battery_drained, 2),
        'bullets': bullets,
        'time_elapsed_seconds': dt_seconds,
        'payload_kg': round(payload_kg, 2),
        'payload_fraction': round(payload_fraction, 3),
        'endurance_minutes': round(endurance_min, 2),
        'estimated_flight_time_minutes': round(estimated_time, 2)
    })


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'active_simulations': len(simulations),
        'version': 'EMERGENCY_FIX_v1'
    })


if __name__ == '__main__':
    # Initialize surveillance system
    surveillance = init_surveillance(center_position=[0, 0, 0], patrol_radius=300.0)
    print("\n" + "=" * 70)
    print("🛰️  SURVEILLANCE SYSTEM ACTIVE")
    print("=" * 70)
    print("  ✅ 3 surveillance drones deployed")
    print("  ✅ Patrolling 300m radius around [0, 0, 0]")
    print("  ✅ Inside asset protection boundary")
    print("  ✅ Will pause during swarm simulations")
    print("  ✅ API: /api/surveillance/status")
    print("=" * 70 + "\n")
    
    # When running with the Flask reloader (debug=True) the module may be
    # executed twice (parent + child). Use the WERKZEUG_RUN_MAIN env var to
    # ensure the startup banner prints only once (in the reloader child), or
    # print when not running in debug mode.
    if (not app.debug) or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        print("=" * 70)
        print("🚨 EMERGENCY FIX - GUARANTEED WIN VERSION 🚨")
        print("=" * 70)
        print("Changes:")
        print("  ✅ Friendly health: 150 (was 100)")
        print("  ✅ Enemy health: 80 (was 100)")
        print("  ✅ Friendly damage: 40-60 (was 30-50)")
        print("  ✅ Enemy damage: 15-25 (was 30-50)")
        print("  ✅ Weapon range: 150m (was 100m)")
        print("  ✅ Speed: 70m/s (was 50m/s)")
        print("  ✅ Detection: 1500m (was 1000m)")
        print("=" * 70)
        print("Server starting on http://localhost:5000")
        print("TRY: '⭐ GUARANTEED WIN' scenario first!")
        print("=" * 70)

    app.run(debug=True, host='0.0.0.0', port=5000)