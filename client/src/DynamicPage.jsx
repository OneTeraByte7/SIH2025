import React, { useEffect, useRef, useState, useCallback } from 'react';
import * as THREE from 'three';
import { X, Play, StopCircle } from 'lucide-react';

const API_BASE = 'http://localhost:5000/api';

function createDroneMesh(color = 0x00ff00, size = 6) {
  // use a cone to better represent orientation and tactical look
  const geom = new THREE.ConeGeometry(size, size * 2, 8);
  const mat = new THREE.MeshStandardMaterial({ color, flatShading: true });
  const m = new THREE.Mesh(geom, mat);
  m.castShadow = false;
  m.receiveShadow = false;
  m.rotation.x = Math.PI / 2; // cone points forward
  return m;
}

export default function DynamicPage({ onClose }) {
  const mountRef = useRef(null);
  const rendererRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const assetMeshRef = useRef(null);
  const friendlyPoolRef = useRef([]);
  const enemyPoolRef = useRef([]);
  const rafRef = useRef(null);

  const [simId, setSimId] = useState(null);
  const [status, setStatus] = useState('idle');
  const [frames, setFrames] = useState([]);
  const [playing, setPlaying] = useState(false);
  const [params, setParams] = useState({ 
    max_time: 30, 
    friendly_count: 12, 
    enemy_count: 8,
    swarm_algorithm: 'cbba-superiority'
  });
  const currentFrameIndex = useRef(0);
  const [liveStats, setLiveStats] = useState({ friendlies: 0, enemies: 0, enemiesKilled: 0, assetHealth: 100 });
  const [algorithms, setAlgorithms] = useState([]);

  const createHealthBar = (percentage) => {
    const canvas = document.createElement('canvas');
    canvas.width = 64;
    canvas.height = 8;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#5c1e1e';
    ctx.fillRect(0, 0, 64, 8);
    ctx.fillStyle = '#00ff00';
    ctx.fillRect(0, 0, Math.max(0, Math.min(1, percentage)) * 64, 8);

    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({ map: texture });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(30, 4, 1);
    return sprite;
  };

  const createTextSprite = (text, color) => {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = '#111827';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = `#${color.toString(16).padStart(6, '0')}`;
    ctx.font = 'Bold 32px Inter';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, canvas.width / 2, canvas.height / 2);

    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;
    const material = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(100, 25, 1);
    return sprite;
  };

  const renderFrame = useCallback((frame) => {
    const scene = sceneRef.current;
    if (!scene) return;

    // Update live stats
    const activeFriendlies = (frame.friendlies || []).filter(d => d.health > 0).length;
    const activeEnemies = (frame.enemies || []).filter(d => d.health > 0).length;
    const initialEnemies = params.enemy_count || 8;
    const enemiesKilled = initialEnemies - activeEnemies;
    const assetHealth = (frame.assets && frame.assets[0]) ? frame.assets[0].health || 100 : 100;
    setLiveStats({ friendlies: activeFriendlies, enemies: activeEnemies, enemiesKilled, assetHealth });

    const removable = [];
    scene.children.forEach(child => {
      if (child.userData?.persistent) return;
      if (child.userData?.removable) {
        removable.push(child);
        return;
      }
      if (child.type === 'Mesh' || child.type === 'Line' || child.type === 'Sprite') {
        removable.push(child);
      }
    });

    removable.forEach(obj => {
      scene.remove(obj);
      if (obj.geometry) obj.geometry.dispose();
      if (obj.material) {
        if (Array.isArray(obj.material)) {
          obj.material.forEach(m => m.dispose());
        } else {
          obj.material.dispose();
        }
      }
    });

    (frame.assets || []).forEach(asset => {
      console.log('Asset health:', asset.health);
      
      const geometry = new THREE.CylinderGeometry(50, 50, 100, 8);
      const material = new THREE.MeshPhongMaterial({
        color: 0x00ff00,
        emissive: 0x003300,
        emissiveIntensity: 0.5
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(asset.position[0], 50, asset.position[2]);
      mesh.userData.removable = true;
      scene.add(mesh);

      const ringGeo = new THREE.RingGeometry(380, 400, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: 0x00ff00,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.3
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = -Math.PI / 2;
      ring.position.set(asset.position[0], 5, asset.position[2]);
      ring.userData.removable = true;
      scene.add(ring);

      const sprite = createTextSprite('ASSET', 0x00ff00);
      sprite.position.set(asset.position[0], 180, asset.position[2]);
      sprite.userData.removable = true;
      scene.add(sprite);

      // Asset health bar (assuming 100 max health, or use asset.health if available)
      const assetHealth = asset.health !== undefined ? asset.health / 100 : 1.0;
      console.log('Asset health bar value:', assetHealth, 'Position Y:', 160);
      const assetHealthBar = createHealthBar(assetHealth);
      assetHealthBar.position.set(asset.position[0], 160, asset.position[2]);
      assetHealthBar.userData.removable = true;
      scene.add(assetHealthBar);
    });

    (frame.friendlies || []).forEach(drone => {
      if (drone.health <= 0) return;
      let color = 0x00aaff;
      let geometry;
      
      // Different shapes based on role
      if (drone.role === 'hunter') {
        color = 0xff6600;
        geometry = new THREE.OctahedronGeometry(15, 0); // Sharp octahedron for hunters
      } else if (drone.role === 'interceptor') {
        color = 0xff0066;
        geometry = new THREE.TetrahedronGeometry(15, 0); // Fast tetrahedron for interceptors
      } else {
        // Defender - default sphere
        geometry = new THREE.SphereGeometry(15, 16, 16);
      }

      const material = new THREE.MeshPhongMaterial({ color, emissive: color, emissiveIntensity: 0.4 });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(drone.position[0], drone.position[1], drone.position[2]);
      mesh.userData.removable = true;
      scene.add(mesh);

      const healthBar = createHealthBar(drone.health / 150);
      healthBar.position.set(drone.position[0], drone.position[1] + 30, drone.position[2]);
      healthBar.userData.removable = true;
      scene.add(healthBar);

      // Add role label
      const roleLabel = createTextSprite(drone.role?.toUpperCase() || 'DEFENDER', color);
      roleLabel.scale.set(50, 12, 1);
      roleLabel.position.set(drone.position[0], drone.position[1] + 45, drone.position[2]);
      roleLabel.userData.removable = true;
      scene.add(roleLabel);

      if (drone.target_id) {
        const target = (frame.enemies || []).find(e => e.id === drone.target_id);
        if (target && target.health > 0) {
          const points = [
            new THREE.Vector3(drone.position[0], drone.position[1], drone.position[2]),
            new THREE.Vector3(target.position[0], target.position[1], target.position[2])
          ];
          const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
          const lineMat = new THREE.LineBasicMaterial({ color: 0xff0000, transparent: true, opacity: 0.4 });
          const line = new THREE.Line(lineGeo, lineMat);
          line.userData.removable = true;
          scene.add(line);
        }
      }
    });

    (frame.enemies || []).forEach(drone => {
      if (drone.health <= 0) return;
      
      // Different shapes and colors for ground vs air enemies
      let color, geometry;
      console.log('Enemy drone type:', drone.type, 'drone_type:', drone.drone_type);
      
      if (drone.type === 'enemy_ground' || drone.drone_type === 'enemy_ground') {
        // Ground enemy - use a box/cube shape
        color = 0xff3333;
        geometry = new THREE.BoxGeometry(25, 15, 25);
        console.log('Rendering GROUND enemy as box');
      } else {
        // Air enemy - use cone/pyramid shape
        color = 0xff9933;
        geometry = new THREE.ConeGeometry(12, 30, 4);
        console.log('Rendering AIR enemy as cone');
      }
      
      const material = new THREE.MeshPhongMaterial({ color, emissive: color, emissiveIntensity: 0.5 });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(drone.position[0], drone.position[1], drone.position[2]);
      
      // Rotate cone enemies upside down
      if (drone.type !== 'enemy_ground' && drone.drone_type !== 'enemy_ground') {
        mesh.rotation.x = Math.PI;
      }
      
      mesh.userData.removable = true;
      scene.add(mesh);

      const healthBar = createHealthBar(drone.health / 85);
      healthBar.position.set(drone.position[0], drone.position[1] + 25, drone.position[2]);
      healthBar.userData.removable = true;
      scene.add(healthBar);

      // Add enemy type label
      const enemyType = (drone.type === 'enemy_ground' || drone.drone_type === 'enemy_ground') ? 'GROUND' : 'AIR';
      const typeLabel = createTextSprite(enemyType, color);
      typeLabel.scale.set(40, 10, 1);
      typeLabel.position.set(drone.position[0], drone.position[1] + 40, drone.position[2]);
      typeLabel.userData.removable = true;
      scene.add(typeLabel);
    });
  }, [params.enemy_count]);

  // Load algorithms on mount
  useEffect(() => {
    fetch(`${API_BASE}/algorithms`)
      .then(res => res.json())
      .then(data => {
        setAlgorithms(data);
        if (data.length > 0) {
          setParams(p => ({ ...p, swarm_algorithm: data[0].value }));
        }
      })
      .catch(err => console.warn('Failed to load algorithms', err));
  }, []);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x071025);
    sceneRef.current = scene;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const camera = new THREE.PerspectiveCamera(55, mount.clientWidth / mount.clientHeight, 1, 10000);
    camera.position.set(0, 900, 900);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    const hemi = new THREE.HemisphereLight(0xffffff, 0x222233, 0.8);
    scene.add(hemi);
    const dir = new THREE.DirectionalLight(0xffffff, 0.9);
    dir.position.set(-400, 800, 300);
    scene.add(dir);

    // ground with grid lines for tactical look
    const ground = new THREE.Mesh(
      new THREE.PlaneGeometry(4000, 4000),
      new THREE.MeshStandardMaterial({ color: 0x061020 })
    );
    ground.rotation.x = -Math.PI / 2;
    ground.position.y = -2;
    scene.add(ground);

    // grid helper
    const grid = new THREE.GridHelper(2000, 40, 0x0f3b4a, 0x072027);
    grid.position.y = -1.9;
    scene.add(grid);

    // Note: frame rendering will create the asset marker and protection ring
    // so we don't add a persistent placeholder here to avoid duplicates.

    // playback clock for smooth interpolation
    const playbackClock = { t: 0, lastNow: null };

    // start render loop
    const animate = (now) => {
      rafRef.current = requestAnimationFrame(animate);

      // advance playback clock
      if (!playbackClock.lastNow) playbackClock.lastNow = now || performance.now();
      const deltaMs = (now || performance.now()) - playbackClock.lastNow;
      playbackClock.lastNow = now || performance.now();
      if (playing && frames.length > 0) {
        playbackClock.t += (deltaMs / 1000.0) * 2.0; // 2x speed for faster playback
      }

      // find surrounding frames for interpolation
      let idx = currentFrameIndex.current;
      if (frames.length > 0) {
        // ensure playbackClock.t is within frames time range
        const startTime = frames[0].time || 0;
        const endTime = frames[frames.length - 1].time || startTime;
        if (playbackClock.t < startTime) playbackClock.t = startTime;
        if (playbackClock.t > endTime) playbackClock.t = endTime;

        // advance idx so that frames[idx].time <= t < frames[idx+1].time
        while (idx < frames.length - 2 && playbackClock.t > (frames[idx + 1].time || 0)) idx++;
        while (idx > 0 && playbackClock.t < (frames[idx].time || 0)) idx--;
        currentFrameIndex.current = idx;
      }

      const f = frames[idx];
      if (f) {
        // asset (frames store assets[])
        const assetFrame = Array.isArray(f.assets) && f.assets.length > 0 ? f.assets[0] : (f.asset || null);
        const nextFrame = frames[idx + 1] || null;
        const t0 = f.time || 0;
        const t1 = nextFrame ? (nextFrame.time || t0) : t0;
        const localT = (t1 - t0) <= 0 ? 0 : Math.min(1, (playbackClock.t - t0) / (t1 - t0));

        const lerpArray = (a, b, r) => {
          const A = Array.isArray(a) ? a : (a && a.position) ? a.position : (a && a.pos) ? a.pos : [0, 0, 0];
          const B = Array.isArray(b) ? b : (b && b.position) ? b.position : (b && b.pos) ? b.pos : A;
          return [A[0] + (B[0] - A[0]) * r, A[1] + (B[1] - A[1]) * r, A[2] + (B[2] - A[2]) * r];
        };

        const assetNext = nextFrame ? (Array.isArray(nextFrame.assets) && nextFrame.assets.length > 0 ? nextFrame.assets[0] : (nextFrame.asset || null)) : null;
        const ap = assetFrame ? lerpArray(assetFrame, assetNext || assetFrame, localT) : [0, 0, 0];

        // Build an interpolated frame object and render via renderFrame()
        const friendlies = Array.isArray(f.friendlies) ? f.friendlies : [];
        const enemies = Array.isArray(f.enemies) ? f.enemies : [];

        const interpFriendlies = friendlies.map((d, i) => {
          const nextF = nextFrame && Array.isArray(nextFrame.friendlies) ? nextFrame.friendlies[i] : null;
          const pInterp = lerpArray(d, nextF || d, localT);
          return Object.assign({}, d, { position: pInterp });
        });

        const interpEnemies = enemies.map((d, i) => {
          const nextE = nextFrame && Array.isArray(nextFrame.enemies) ? nextFrame.enemies[i] : null;
          const pInterp = lerpArray(d, nextE || d, localT);
          return Object.assign({}, d, { position: pInterp });
        });

        const interpolatedFrame = {
          time: playbackClock.t,
          assets: [{ position: ap }],
          friendlies: interpFriendlies,
          enemies: interpEnemies,
        };

        renderFrame(interpolatedFrame);
      }

      renderer.render(scene, camera);
    };

    animate();

    const handleResize = () => {
      if (!mount) return;
      const w = mount.clientWidth;
      const h = mount.clientHeight;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('resize', handleResize);
      // cleanup three objects
      try { mount.removeChild(renderer.domElement); } catch (e) {}
      scene.traverse((obj) => { if (obj.geometry) obj.geometry.dispose(); if (obj.material) obj.material.dispose(); });
      renderer.dispose();
    };
  }, [frames, playing]);

  // advance frame index when playing
  useEffect(() => {
    let timer = null;
    if (playing && frames.length > 0) {
      timer = setInterval(() => {
        currentFrameIndex.current = Math.min(frames.length - 1, currentFrameIndex.current + 1);
      }, 100);
    }
    return () => { if (timer) clearInterval(timer); };
  }, [playing, frames]);

  const fetchFrames = useCallback(async (id) => {
    try {
      const res = await fetch(`${API_BASE}/dynamic/${id}/data?start=0&end=2000`);
      if (!res.ok) return;
      const data = await res.json();
      if (Array.isArray(data.frames)) {
        setFrames(data.frames);
        currentFrameIndex.current = 0;
      }
    } catch (e) { console.warn(e); }
  }, []);

  // Poll status and refresh frames
  useEffect(() => {
    if (!simId) return;
    let poll = setInterval(async () => {
      try {
        const st = await fetch(`${API_BASE}/dynamic/${simId}/status`);
        if (!st.ok) return;
        const js = await st.json();
        setStatus(js.status || js.state || 'running');
        if (js.status === 'completed' || js.state === 'completed') {
          clearInterval(poll);
          await fetchFrames(simId);
          setPlaying(false);
        } else {
          // keep frames updated while running
          await fetchFrames(simId);
        }
      } catch (e) { console.warn(e); }
    }, 1000);

    // run immediate
    (async () => { try { await fetchFrames(simId); } catch (e) {} })();

    return () => clearInterval(poll);
  }, [simId, fetchFrames]);

  const startSimulation = async () => {
    setStatus('starting');
    setFrames([]);
    currentFrameIndex.current = 0;
    try {
      const { max_time, friendly_count, enemy_count, swarm_algorithm } = params;
      // generate linear path from -400 to 400 over max_time
      const steps = 12;
      const asset_path = [];
      for (let i = 0; i <= steps; i++) {
        const t = (i / steps) * max_time;
        const x = -400 + (800 * (i / steps));
        asset_path.push({ time: t, position: [x, 0, 0] });
      }

      const payload = {
        max_time,
        friendly_count,
        enemy_count,
        max_speed: 70,
        weapon_range: 150,
        detection_range: 1500,
        swarm_algorithm: swarm_algorithm || 'cbba-superiority',
        assets: [{ position: [0, 0, 0], value: 1 }],
        asset_path,
      };

      const res = await fetch(`${API_BASE}/dynamic/start`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
      });
      const js = await res.json();
      const id = js.id || js.simulation_id || js.sim_id || js.uuid || js.id_tag || null;
      setSimId(id);
      setStatus('running');
      setPlaying(true);
    } catch (e) {
      console.warn(e);
      setStatus('error');
      setPlaying(false);
    }
  };

  const stopSimulation = async () => {
    setPlaying(false);
    setStatus('stopped');
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 p-6 overflow-hidden">
      <div className="h-full w-full rounded-xl bg-gradient-to-br from-slate-900 to-slate-800 border border-slate-700 shadow-2xl flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold text-cyan-200">Dynamic Simulation (3D)</h2>
            <div className="text-sm text-gray-400">Sim: <span className="font-mono text-cyan-300">{simId || '-'}</span></div>
            <div className="text-sm text-gray-400">Status: <span className="font-semibold text-cyan-200 ml-2">{status}</span></div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={() => { setPlaying(p => !p); }} className="px-3 py-2 bg-cyan-600 rounded text-sm text-white flex items-center gap-2">
              {playing ? <StopCircle /> : <Play />} {playing ? 'Pause' : 'Play'}
            </button>
            <button onClick={onClose} className="px-3 py-2 bg-gray-800 rounded text-sm text-gray-200 flex items-center gap-2"><X /> Close</button>
          </div>
        </div>

        <div className="flex-1 flex gap-4 p-4">
          <div className="w-3/4 rounded bg-black/40 border border-slate-700" ref={mountRef} style={{ minHeight: 480 }} />

          <div className="w-1/4 space-y-4 p-2">
            <div className="bg-black/30 border border-slate-700 rounded p-3">
              <h4 className="text-sm font-semibold text-cyan-200 mb-2">Live Stats</h4>
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-400">Friendlies Active:</span>
                  <span className="text-cyan-300 font-bold">{liveStats.friendlies}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Enemies Active:</span>
                  <span className="text-red-400 font-bold">{liveStats.enemies}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Enemies Destroyed:</span>
                  <span className="text-green-400 font-bold">{liveStats.enemiesKilled}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Asset Health:</span>
                  <span className={`font-bold ${liveStats.assetHealth > 60 ? 'text-green-400' : liveStats.assetHealth > 30 ? 'text-yellow-400' : 'text-red-400'}`}>
                    {liveStats.assetHealth.toFixed(1)}%
                  </span>
                </div>
                {(status === 'completed' || status === 'stopped') && frames.length > 0 && (
                  <>
                    <div className="border-t border-cyan-900 my-2"></div>
                    <div className="text-xs font-semibold text-cyan-200 mb-1">Final Result:</div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Mission:</span>
                      <span className={`font-bold ${liveStats.assetHealth > 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {liveStats.assetHealth > 0 ? '✓ SUCCESS' : '✗ FAILED'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Drones Left:</span>
                      <span className="text-cyan-300 font-bold">{liveStats.friendlies}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Asset Status:</span>
                      <span className={`font-bold ${liveStats.assetHealth > 60 ? 'text-green-400' : 'text-yellow-400'}`}>
                        {liveStats.assetHealth > 0 ? 'Protected' : 'Destroyed'}
                      </span>
                    </div>
                  </>
                )}
              </div>
            </div>

            <div className="bg-black/30 border border-slate-700 rounded p-3">
              <label className="text-sm text-gray-300">Algorithm</label>
              <select 
                value={params.swarm_algorithm} 
                onChange={(e)=>setParams(p=>({...p, swarm_algorithm: e.target.value}))} 
                className="w-full mt-2 p-2 rounded bg-slate-900 text-sm"
              >
                {algorithms.map(algo => (
                  <option key={algo.value} value={algo.value}>{algo.label}</option>
                ))}
              </select>
              <label className="text-sm text-gray-300 mt-3">Max time (s)</label>
              <input type="number" value={params.max_time} onChange={(e)=>setParams(p=>({...p, max_time: Number(e.target.value)||30}))} className="w-full mt-2 p-2 rounded bg-slate-900 text-sm" />
              <label className="text-sm text-gray-300 mt-2">Friendlies</label>
              <input type="number" value={params.friendly_count} onChange={(e)=>setParams(p=>({...p, friendly_count: Number(e.target.value)||0}))} className="w-full mt-2 p-2 rounded bg-slate-900 text-sm" />
              <label className="text-sm text-gray-300 mt-2">Enemies</label>
              <input type="number" value={params.enemy_count} onChange={(e)=>setParams(p=>({...p, enemy_count: Number(e.target.value)||0}))} className="w-full mt-2 p-2 rounded bg-slate-900 text-sm" />
              <div className="mt-3 flex gap-2">
                <button onClick={startSimulation} className="flex-1 px-3 py-2 bg-cyan-600 rounded text-white">Start</button>
                <button onClick={stopSimulation} className="px-3 py-2 bg-red-600 rounded text-white">Stop</button>
              </div>
            </div>

            <div className="bg-black/30 border border-slate-700 rounded p-3">
              <h4 className="text-sm font-semibold text-cyan-200 mb-2">Battlefield Legend</h4>
              <div className="space-y-2 text-xs">
                <div className="text-xs font-semibold text-gray-200 mb-1">Friendly Drones:</div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-cyan-500"></div>
                  <span className="text-gray-300">Defender (Sphere)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-pink-600 transform rotate-45"></div>
                  <span className="text-gray-300">Interceptor (Tetrahedron)</span>
                </div>
                <div className="border-t border-gray-700 my-2"></div>
                <div className="text-xs font-semibold text-gray-200 mb-1">Enemy Drones:</div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-red-600"></div>
                  <span className="text-gray-300">Ground Enemy (Square)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-orange-500 transform rotate-180" style={{clipPath: 'polygon(50% 0%, 0% 100%, 100% 100%)'}}>▼</div>
                  <span className="text-gray-300">Air Enemy (Cone)</span>
                </div>
                <div className="border-t border-gray-700 my-2"></div>
                <div className="text-xs font-semibold text-gray-200 mb-1">Assets:</div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-gray-300">Protected Asset (Cylinder)</span>
                </div>
                <div className="border-t border-gray-700 my-2"></div>
                <div className="text-xs text-gray-400">
                  <div>✓ All units have health bars</div>
                  <div>✓ Red lines = Active targeting</div>
                </div>
              </div>
            </div>

            <div className="bg-black/30 border border-slate-700 rounded p-3 text-sm overflow-auto max-h-[200px]">
              <div className="text-xs text-gray-400">Frames: <span className="font-mono text-cyan-300">{frames.length}</span></div>
              <div className="text-xs text-gray-400 mt-2">Current index: <span className="font-mono text-cyan-300">{currentFrameIndex.current}</span></div>
              <div className="mt-3">
                <button onClick={() => fetchFrames(simId)} disabled={!simId} className="px-2 py-1 bg-slate-700 rounded text-xs">Fetch Frames</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
