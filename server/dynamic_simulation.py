import time
import uuid
from threading import Thread, Lock
from typing import List, Dict, Any
import numpy as np
from simulation import SuperSimulation

# Lightweight dynamic simulation store (keeps separate from existing `simulations`)
dynamic_simulations: Dict[str, Dict[str, Any]] = {}
dynamic_lock = Lock()


def _interpolate_path(path: List[Dict[str, Any]], t: float):
    """Interpolate asset path waypoints by time.
    path: [{ 'time': float, 'pos': [x,y,z] }, ...]
    Accepts waypoints that may use the key 'pos' or 'position' (or nested x/y/z).
    Returns: [x,y,z] at time t or None if no path
    """
    if not path:
        return None
    # defensive access: assume each waypoint has normalized 'time' and 'pos' keys
    try:
        if t <= path[0].get('time', 0.0):
            return path[0].get('pos')
    except Exception:
        return None

    for a, b in zip(path, path[1:]):
        at = a.get('time')
        bt = b.get('time')
        if at is None or bt is None:
            continue
        if at <= t <= bt:
            dt = bt - at
            apos = a.get('pos')
            bpos = b.get('pos')
            if apos is None or bpos is None:
                return None
            if dt <= 0:
                return apos
            ratio = (t - at) / dt
            return [a_i + ratio * (b_i - a_i) for a_i, b_i in zip(apos, bpos)]
    # fallback to last known position
    return path[-1].get('pos')


def _run_dynamic(sim_id: str, config: Dict[str, Any]):
    with dynamic_lock:
        entry = dynamic_simulations.get(sim_id)
        if not entry:
            return
        sim: SuperSimulation = entry['sim']
        path = entry.get('asset_path', [])

    sim_dt = getattr(sim, 'dt', 0.1)
    max_time = float(config.get('max_time', 120.0))
    max_steps = int(max_time / sim_dt)

    for step in range(max_steps):
        # Update dynamic asset position based on configured path
        t = sim.time
        pos = _interpolate_path(path, t)
        if pos is not None and sim.assets:
            try:
                sim.assets[0].position = np.array(pos, dtype=float)
            except Exception:
                pass

        # Step simulation and record frame
        sim.step(record=True)

        with dynamic_lock:
            # copy last history frame into our lightweight history list
            if sim.history:
                entry['history'].append(sim.history[-1])
            entry['progress'] = min(100.0, (sim.time / max_time) * 100.0)
            entry['status'] = 'running' if not sim.is_complete() else 'completed'

        if sim.is_complete():
            break

    with dynamic_lock:
        entry['status'] = 'completed'
        entry['statistics'] = sim.get_statistics()


def start_dynamic_simulation(config: Dict[str, Any]) -> str:
    """Create and start a dynamic simulation. Returns simulation id."""
    sim_id = str(uuid.uuid4())
    sim = SuperSimulation(config)
    sim.initialize_scenario()

    raw_path = config.get('asset_path', [])

    # Normalize incoming waypoints: accept {'time':..., 'pos':[...]},
    # {'time':..., 'position':[...]}, or {'time':..., 'x':..,'y':..,'z':..}
    norm_path: List[Dict[str, Any]] = []
    for wp in raw_path or []:
        try:
            time_val = float(wp.get('time', wp.get('t', 0.0)))
        except Exception:
            continue

        pos = None
        if 'pos' in wp and wp['pos'] is not None:
            pos = wp['pos']
        elif 'position' in wp and wp['position'] is not None:
            pos = wp['position']
        else:
            # try x/y/z
            if all(k in wp for k in ('x', 'y', 'z')):
                pos = [wp.get('x'), wp.get('y'), wp.get('z')]

        if pos is None:
            continue

        # coerce to list of floats
        try:
            pos_list = [float(pos[i]) for i in range(3)] if (isinstance(pos, (list, tuple)) and len(pos) >= 3) else None
        except Exception:
            pos_list = None

        if pos_list is None:
            continue

        norm_path.append({'time': time_val, 'pos': pos_list})

    with dynamic_lock:
        dynamic_simulations[sim_id] = {
            'id': sim_id,
            'sim': sim,
            'status': 'initializing',
            'progress': 0.0,
            'history': [],
            'statistics': None,
            'asset_path': norm_path
        }

    thread = Thread(target=_run_dynamic, args=(sim_id, config), daemon=True)
    thread.start()
    return sim_id


def get_dynamic_status(sim_id: str) -> Dict[str, Any]:
    with dynamic_lock:
        info = dynamic_simulations.get(sim_id)
        if not info:
            return {'error': 'not found'}
        return {
            'id': sim_id,
            'status': info.get('status'),
            'progress': info.get('progress'),
            'statistics': info.get('statistics')
        }


def get_dynamic_data(sim_id: str, start: int = 0, end: int = None) -> Dict[str, Any]:
    with dynamic_lock:
        info = dynamic_simulations.get(sim_id)
        if not info:
            return {'error': 'not found'}
        h = info.get('history', [])
        slice_ = h[start:end]
        return {
            'frames': slice_,
            'total_frames': len(h),
            'statistics': info.get('statistics')
        }
