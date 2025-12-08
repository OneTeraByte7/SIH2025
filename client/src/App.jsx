import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Play, Pause, RotateCcw, Settings, BarChart3, Zap, AlertCircle, Plus, Eye, EyeOff, Maximize2, Camera, Sliders, MapPin, Download, Aperture, Shield, Orbit, Radar, Waves, SkipForward, SkipBack } from 'lucide-react';
import { jsPDF } from 'jspdf';
import * as THREE from 'three';
import AnalyticsDashboard from './Dashboard.jsx';
import LandingPage from './LandingPage.jsx';
import DynamicPage from './DynamicPage.jsx';
import LegendPanel from './LegendPanel.jsx';
import AssetPlacementMap from './AssetPlacementMap.jsx';
import { API_BASE, MAP_EXTENT, defaultSwarmAlgorithmOptions } from './constants';
import './App.css';

const EnhancedDroneSwarmSystem = () => {
  const [presets, setPresets] = useState({});
  const [currentSim, setCurrentSim] = useState(null);
  const [frames, setFrames] = useState([]);
  const [stats, setStats] = useState(null);
  const [analytics, setAnalytics] = useState(null);

  // Debug: Log when frames change
  useEffect(() => {
    console.log('🎬 Frames updated:', frames.length, 'frames loaded');
    if (frames.length > 0) {
      console.log('   First frame time:', frames[0]?.time);
      console.log('   Last frame time:', frames[frames.length - 1]?.time);
      console.log('   First frame friendlies:', frames[0]?.friendlies?.length || 0);
      console.log('   First frame enemies:', frames[0]?.enemies?.length || 0);
    }
  }, [frames]);

  const [playing, setPlaying] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(0);
  const [playSpeed, setPlaySpeed] = useState(1);
  const [showSettings, setShowSettings] = useState(false);
  const [showCustom, setShowCustom] = useState(false);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [showDynamic, setShowDynamic] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [cameraMode, setCameraMode] = useState('orbital');
  const [showGrid, setShowGrid] = useState(true);
  const [visualQuality] = useState('high');
  const [swarmAlgorithm, setSwarmAlgorithm] = useState('cbba-superiority');
  const [selectedAssetIndex, setSelectedAssetIndex] = useState(0);
  const [lastScenario, setLastScenario] = useState(null);
  const [showLanding, setShowLanding] = useState(true);
  const [landingExiting, setLandingExiting] = useState(false);

  const [swarmAlgorithmOptions, setSwarmAlgorithmOptions] = useState(defaultSwarmAlgorithmOptions);

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/algorithms`);
        if (!res.ok) throw new Error('No algorithm list');
        const data = await res.json();

        const ICON_MAP = {
          'adaptive-shield': Shield,
          'orbital-halo': Orbit,
          'spectral-wave': Waves,
          'sentinel-veil': Radar,
          'cbba-superiority': Shield,
          'cvt-cbf': Radar,
          'qipfd-quantum': Orbit
        };

        const mapped = data.map(item => ({
          value: item.value,
          label: item.label || item.value.replace('-', ' ').toUpperCase(),
          description: item.description || '',
          icon: ICON_MAP[item.value] || Shield
        }));

        if (mounted && Array.isArray(mapped) && mapped.length > 0) {
          setSwarmAlgorithmOptions(mapped);
          // Update default algorithm to first available one
          setSwarmAlgorithm(mapped[0].value);
          setCustomConfig(prev => ({ ...prev, swarm_algorithm: mapped[0].value }));
        }
      } catch (err) {
        // keep defaults on error
        console.warn('Failed to fetch algorithms list, using defaults', err);
      }
    })();
    return () => { mounted = false; };
  }, []);

  const [customConfig, setCustomConfig] = useState({
    name: 'Custom Scenario',
    friendly_count: 20,
    enemy_count: 15,
    ground_attack_ratio: 0.4,
    max_time: 120,
    max_speed: 70.0,
    weapon_range: 150.0,
    detection_range: 1500.0,
    swarm_algorithm: 'cbba-superiority',
    assets: [{ position: [0, 0, 0], value: 1.0 }]
  });

  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef = useRef(null);
  const animationIdRef = useRef(null);
  const gridHelperRef = useRef(null);
  const orbitAngleRef = useRef(0);
  const cameraModeRef = useRef(cameraMode);

  const trailsRef = useRef([]);

  useEffect(() => {
    if (showLanding) {
      const originalOverflow = document.body.style.overflow;
      document.body.dataset.prevOverflow = originalOverflow;
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = document.body.dataset.prevOverflow || '';
        delete document.body.dataset.prevOverflow;
      };
    }

    document.body.style.overflow = document.body.dataset.prevOverflow || '';
    delete document.body.dataset.prevOverflow;
    return undefined;
  }, [showLanding]);

  const handleLandingDismiss = useCallback(() => {
    setLandingExiting((prev) => {
      if (prev) return prev;
      setTimeout(() => {
        setShowLanding(false);
        requestAnimationFrame(() => setLandingExiting(false));
      }, 750);
      return true;
    });
  }, []);

  const sanitizeNumber = useCallback((value, fallback) => {
    if (typeof value === 'number' && Number.isFinite(value)) return value;
    if (typeof value === 'string' && value.trim() !== '') {
      const parsed = Number(value);
      if (Number.isFinite(parsed)) return parsed;
    }
    return fallback;
  }, []);

  const prepareScenarioPayload = useCallback((config) => {
    const defaults = {
      friendly_count: 20,
      enemy_count: 15,
      ground_attack_ratio: 0.4,
      max_time: 120,
      max_speed: 70,
      weapon_range: 150,
      detection_range: 1500
    };

    const assets = Array.isArray(config.assets) ? config.assets : [];
    const normalizedAssets = assets.map((asset, idx) => {
      const source = asset?.position ?? [0, 0, 0];
      let coords;
      if (Array.isArray(source)) {
        coords = source;
      } else if (typeof source === 'string') {
        coords = source.split(/[\s,]+/).filter(Boolean).map(Number);
      } else if (typeof source === 'object' && source !== null) {
        coords = [source.x, source.y, source.z];
      } else {
        coords = [0, 0, 0];
      }

      const [x = 0, y = 0, z = 0] = coords;

      return {
        ...asset,
        position: [
          sanitizeNumber(x, 0),
          sanitizeNumber(y, 0),
          sanitizeNumber(z, 0)
        ],
        value: sanitizeNumber(asset?.value, 1 + idx * 0.1)
      };
    });

    const safeAssets = normalizedAssets.length
      ? normalizedAssets
      : [{ position: [0, 0, 0], value: 1 }];

    return {
      ...config,
      friendly_count: sanitizeNumber(config.friendly_count, defaults.friendly_count),
      enemy_count: sanitizeNumber(config.enemy_count, defaults.enemy_count),
      ground_attack_ratio: sanitizeNumber(config.ground_attack_ratio, defaults.ground_attack_ratio),
      max_time: sanitizeNumber(config.max_time, defaults.max_time),
      max_speed: sanitizeNumber(config.max_speed, defaults.max_speed),
      weapon_range: sanitizeNumber(config.weapon_range, defaults.weapon_range),
      detection_range: sanitizeNumber(config.detection_range, defaults.detection_range),
      assets: safeAssets,
      swarm_algorithm: config.swarm_algorithm ?? swarmAlgorithm
    };
  }, [sanitizeNumber, swarmAlgorithm]);

  const updateGridVisibility = useCallback(() => {
    const scene = sceneRef.current;
    if (!scene) return;

    if (showGrid) {
      if (!gridHelperRef.current) {
        const gridHelper = new THREE.GridHelper(2000, 20, 0x00ff00, 0x004400);
        gridHelper.material.opacity = 0.35;
        gridHelper.material.transparent = true;
        gridHelper.userData.persistent = true;
        scene.add(gridHelper);
        gridHelperRef.current = gridHelper;
      }
    } else if (gridHelperRef.current) {
      scene.remove(gridHelperRef.current);
      if (gridHelperRef.current.geometry) gridHelperRef.current.geometry.dispose();
      if (gridHelperRef.current.material) gridHelperRef.current.material.dispose();
      gridHelperRef.current = null;
    }
  }, [showGrid]);

  const renderFrame = useCallback((frame) => {
    const scene = sceneRef.current;
    if (!scene) return;

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

    frame.assets?.forEach(asset => {
      console.log('[App.jsx] Asset health:', asset.health);
      
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
      
      // Asset health bar
      const assetHealth = asset.health !== undefined ? asset.health / 100 : 1.0;
      console.log('[App.jsx] Asset health bar value:', assetHealth, 'Position Y:', 160);
      const assetHealthBar = createHealthBar(assetHealth);
      assetHealthBar.position.set(asset.position[0], 160, asset.position[2]);
      assetHealthBar.userData.removable = true;
      scene.add(assetHealthBar);
    });

    frame.friendlies?.forEach(drone => {
      if (drone.health <= 0) return;

      // Color based on role, but all use sphere geometry
      let color = 0x00aaff; // Default defender color (cyan)
      if (drone.role === 'hunter') color = 0xff6600; // Orange
      if (drone.role === 'interceptor') color = 0xff0066; // Pink

      const geometry = new THREE.SphereGeometry(15, 16, 16);
      const material = new THREE.MeshPhongMaterial({
        color,
        emissive: color,
        emissiveIntensity: 0.4
      });
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
        const target = frame.enemies?.find(e => e.id === drone.target_id);
        if (target && target.health > 0) {
          const points = [
            new THREE.Vector3(drone.position[0], drone.position[1], drone.position[2]),
            new THREE.Vector3(target.position[0], target.position[1], target.position[2])
          ];
          const lineGeo = new THREE.BufferGeometry().setFromPoints(points);
          const lineMat = new THREE.LineBasicMaterial({
            color: 0xff0000,
            transparent: true,
            opacity: 0.4
          });
          const line = new THREE.Line(lineGeo, lineMat);
          line.userData.removable = true;
          scene.add(line);
        }
      }
    });

    frame.enemies?.forEach(drone => {
      if (drone.health <= 0) return;
      
      console.log('[App.jsx] Enemy drone type:', drone.type, 'drone_type:', drone.drone_type);
      
      // Different shapes and colors for ground vs air enemies
      let color, geometry;
      if (drone.type === 'enemy_ground' || drone.drone_type === 'enemy_ground') {
        // Ground enemy - use a box/cube shape
        color = 0xff3333;
        geometry = new THREE.BoxGeometry(25, 15, 25);
        console.log('[App.jsx] Rendering GROUND enemy as box');
      } else {
        // Air enemy - use cone/pyramid shape
        color = 0xff9933;
        geometry = new THREE.ConeGeometry(12, 30, 4);
        console.log('[App.jsx] Rendering AIR enemy as cone');
      }

      const material = new THREE.MeshPhongMaterial({
        color,
        emissive: color,
        emissiveIntensity: 0.5
      });
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
  }, []);

  const initThreeJS = useCallback(() => {
    if (!mountRef.current) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0a);
    scene.fog = new THREE.Fog(0x0a0a0a, 2000, 4000);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(
      60,
      mountRef.current.clientWidth / mountRef.current.clientHeight,
      1,
      5000
    );
    camera.position.set(1500, 1000, 1500);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({
      antialias: visualQuality === 'high',
      alpha: true
    });
    renderer.setSize(mountRef.current.clientWidth, mountRef.current.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    renderer.shadowMap.enabled = visualQuality === 'high';
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const ambientLight = new THREE.AmbientLight(0x404040, 2);
    ambientLight.userData.persistent = true;
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
    dirLight.position.set(500, 1000, 500);
    dirLight.castShadow = visualQuality === 'high';
    dirLight.userData.persistent = true;
    scene.add(dirLight);

    const pointLight = new THREE.PointLight(0x00ffff, 0.5, 2000);
    pointLight.position.set(0, 500, 0);
    pointLight.userData.persistent = true;
    scene.add(pointLight);

    updateGridVisibility();

    const animate = () => {
      animationIdRef.current = requestAnimationFrame(animate);
      if (!cameraRef.current || !sceneRef.current || !rendererRef.current) return;

      if (cameraModeRef.current === 'orbital') {
        orbitAngleRef.current += 0.0025;
        const radius = 1500;
        cameraRef.current.position.x = Math.cos(orbitAngleRef.current) * radius;
        cameraRef.current.position.z = Math.sin(orbitAngleRef.current) * radius;
        cameraRef.current.position.y = 900;
        cameraRef.current.lookAt(0, 0, 0);
      }

      rendererRef.current.render(sceneRef.current, cameraRef.current);
    };

    animate();
  }, [updateGridVisibility, visualQuality]);

  useEffect(() => {
    cameraModeRef.current = cameraMode;
  }, [cameraMode]);

  const fetchPresets = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/scenarios/presets`);
      if (!res.ok) throw new Error('Failed to fetch presets');
      const data = await res.json();
      setPresets(data);
    } catch (err) {
      console.error('Failed to fetch presets', err);
      setError('Cannot connect to backend');
    }
  }, []);

  useEffect(() => {
    fetchPresets();
  }, [fetchPresets]);

  useEffect(() => {
    const mountElement = mountRef.current;
    if (!mountElement) return;

    initThreeJS();

    return () => {
      if (animationIdRef.current) {
        cancelAnimationFrame(animationIdRef.current);
      }
      if (rendererRef.current) {
        rendererRef.current.dispose();
      }
      if (rendererRef.current?.domElement && mountElement.contains(rendererRef.current.domElement)) {
        mountElement.removeChild(rendererRef.current.domElement);
      }
      if (gridHelperRef.current) {
        gridHelperRef.current.geometry.dispose();
        gridHelperRef.current.material.dispose();
        gridHelperRef.current = null;
      }
      trailsRef.current = [];
      sceneRef.current = null;
      rendererRef.current = null;
      cameraRef.current = null;
    };
  }, [initThreeJS]);

  useEffect(() => {
    const handleResize = () => {
      if (!mountRef.current || !cameraRef.current || !rendererRef.current) return;
      const width = mountRef.current.clientWidth;
      const height = mountRef.current.clientHeight;
      cameraRef.current.aspect = width / height;
      cameraRef.current.updateProjectionMatrix();
      rendererRef.current.setSize(width, height);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    if (playing && frames.length > 0) {
      const interval = setInterval(() => {
        setCurrentFrame(prev => {
          const nextFrame = prev + 1;
          if (nextFrame >= frames.length) {
            // Reached the end - stop playing but stay on last frame
            setPlaying(false);
            console.log('[Playback] ✅ Reached end of simulation at frame', frames.length - 1);
            console.log('[Playback] Final state:', frames[frames.length - 1]);
            
            // Show completion message
            if (frames[frames.length - 1]) {
              const finalFrame = frames[frames.length - 1];
              const friendliesAlive = finalFrame.friendlies?.filter(f => f.health > 0).length || 0;
              const enemiesAlive = finalFrame.enemies?.filter(e => e.health > 0).length || 0;
              console.log(`[Playback] 🏁 SIMULATION ENDED | Friendlies: ${friendliesAlive} | Enemies: ${enemiesAlive}`);
            }
            
            return frames.length - 1;
          }
          return nextFrame;
        });
      }, 100 / playSpeed);
      return () => clearInterval(interval);
    }
  }, [playing, frames, playSpeed]);

  useEffect(() => {
    if (frames.length > 0 && sceneRef.current) {
      renderFrame(frames[currentFrame]);
    }
  }, [currentFrame, frames, renderFrame]);

  useEffect(() => {
    updateGridVisibility();
  }, [showGrid, updateGridVisibility]);


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

  const startSimulation = async (config) => {
    const payload = prepareScenarioPayload({ ...config, swarm_algorithm: config.swarm_algorithm ?? swarmAlgorithm });
    setLoading(true);
    setError(null);
    setShowSettings(false);
    setShowCustom(false);
    setLastScenario(payload);

    try {
      const res = await fetch(`${API_BASE}/simulation/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) throw new Error('Failed to start simulation');

  const data = await res.json();
      setCurrentSim(data.simulation_id);

      if (config === customConfig) {
        setCustomConfig(payload);
        setSelectedAssetIndex(0);
      }
      pollSimulation(data.simulation_id);
    } catch (err) {
      setError('Failed to start simulation: ' + err.message);
      setLoading(false);
    }
  };

  const pollSimulation = async (simId) => {
    const checkStatus = async () => {
      try {
        const res = await fetch(`${API_BASE}/simulation/${simId}/status`);
        if (!res.ok) throw new Error('status error');
        const data = await res.json();

        console.log('📊 Poll:', data.status, '| Progress:', data.progress?.toFixed(1) || '?', '%');

        if (data.status === 'completed') {
          console.log('✅ Simulation complete! Fetching data...');
          
          const dataRes = await fetch(`${API_BASE}/simulation/${simId}/data`);
          const simData = await dataRes.json();

          console.log('📦 Received', simData.frames?.length || 0, 'frames');

          setFrames(simData.frames);
          setStats(data.statistics);
          setCurrentFrame(0);
          setLoading(false);

          const analyticsRes = await fetch(`${API_BASE}/simulation/${simId}/analytics`);
          const analyticsData = await analyticsRes.json();
          setAnalytics(analyticsData);
          
          console.log('🎯 All data loaded! Ready to play.');
        } else if (data.status === 'running' || data.status === 'initializing') {
          setTimeout(() => checkStatus(), 1000);
        } else if (data.status === 'error') {
          console.error('❌ Simulation error:', data.statistics?.error || 'Unknown error');
          setError(data.statistics?.error || 'Simulation failed');
          setLoading(false);
        } else {
          console.warn('⚠️ Unknown status:', data.status);
          setTimeout(() => checkStatus(), 1000);
        }
      } catch (err) {
        console.error('❌ Poll failed:', err);
        setError('Lost connection to simulation');
        setLoading(false);
      }
    };
    checkStatus();
  };

  const handleCustomChange = (field, value) => {
    setCustomConfig(prev => ({ ...prev, [field]: value }));
  };

  const addAsset = () => {
    setCustomConfig(prev => {
      const index = prev.assets.length;
      const angle = (index * Math.PI) / 3;
      const radius = 400 + index * 150;
      const newPosition = [
        Math.round(Math.cos(angle) * radius),
        0,
        Math.round(Math.sin(angle) * radius)
      ];

      setSelectedAssetIndex(index);
      return {
        ...prev,
        assets: [...prev.assets, { position: newPosition, value: 1.0 }]
      };
    });
  };

  const updateAssetValue = (index, rawValue) => {
    setCustomConfig(prev => {
      const updated = prev.assets.map((asset, i) => {
        if (i !== index) return asset;
        const value = parseFloat(rawValue);
        return {
          ...asset,
          value: Number.isFinite(value) ? value : asset.value
        };
      });

      return { ...prev, assets: updated };
    });
  };

  const updateAssetPosition = (index, axis, rawValue) => {
    setCustomConfig(prev => {
      const updated = prev.assets.map((asset, i) => {
        if (i !== index) return asset;

        const position = [...asset.position];
        const value = parseFloat(rawValue);
        position[axis] = Number.isFinite(value) ? value : position[axis] ?? 0;

        return {
          ...asset,
          position
        };
      });

      return { ...prev, assets: updated };
    });
  };

  const setAssetGroundPosition = (index, x, z) => {
    setCustomConfig(prev => {
      const updated = prev.assets.map((asset, i) => {
        if (i !== index) return asset;
        const [, altitude = 0] = Array.isArray(asset.position) ? asset.position : [0, 0, 0];
        return {
          ...asset,
          position: [x, altitude, z]
        };
      });

      return { ...prev, assets: updated };
    });
  };

  const removeAsset = (index) => {
    setCustomConfig(prev => ({
      ...prev,
      assets: prev.assets.filter((_, i) => i !== index)
    }));
    setSelectedAssetIndex(prev => {
      if (prev === index) {
        return Math.max(0, prev - 1);
      }
      if (prev > index) {
        return prev - 1;
      }
      return prev;
    });
  };

  const saveCustomScenario = () => {
    const prepared = prepareScenarioPayload(customConfig);
    const json = JSON.stringify(prepared, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${customConfig.name.replace(/\s+/g, '_')}.json`;
    a.click();
  };

  const loadCustomScenario = (event) => {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const config = JSON.parse(e.target.result);
        const prepared = prepareScenarioPayload(config);
        setCustomConfig(prepared);
        if (prepared.swarm_algorithm) {
          setSwarmAlgorithm(prepared.swarm_algorithm);
        }
        setSelectedAssetIndex(0);
      } catch (err) {
        console.error('Failed to parse scenario file', err);
        setError('Invalid scenario file');
      }
    };
    reader.readAsText(file);
  };

  const downloadReport = (format = 'json') => {
    if (!stats || !analytics) {
      setError('Run a simulation to generate a report.');
      return;
    }

    const reportPayload = {
      simulation_id: currentSim,
      generated_at: new Date().toISOString(),
      scenario: lastScenario,
      stats,
      analytics,
      frames
    };

    if (format === 'pdf') {
      const doc = new jsPDF({ unit: 'pt', format: 'a4' });
      const marginLeft = 48;
      let cursorY = 60;

      const scenario = lastScenario ?? customConfig;
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(18);
      doc.text('QIPFD Mission Report', marginLeft, cursorY);
      cursorY += 20;

      doc.setFont('helvetica', 'normal');
      doc.setFontSize(10);
      doc.text(`Generated: ${new Date(reportPayload.generated_at).toLocaleString()}`, marginLeft, cursorY);
      cursorY += 18;
      if (currentSim) {
        doc.text(`Simulation ID: ${currentSim}`, marginLeft, cursorY);
        cursorY += 18;
      }

      doc.setFont('helvetica', 'bold');
      doc.setFontSize(12);
      doc.text('Scenario', marginLeft, cursorY);
      cursorY += 16;

      doc.setFont('helvetica', 'normal');
      const scenarioLines = [
        `Name: ${scenario?.name ?? 'Custom Scenario'}`,
        `Friendlies: ${scenario?.friendly_count ?? '—'}    Enemies: ${scenario?.enemy_count ?? '—'}`,
        `Ground Attack Ratio: ${scenario?.ground_attack_ratio ?? '—'}`,
        `Max Time: ${scenario?.max_time ?? '—'}s    Max Speed: ${scenario?.max_speed ?? '—'} m/s`,
        `Weapon Range: ${scenario?.weapon_range ?? '—'} m    Detection Range: ${scenario?.detection_range ?? '—'} m`
      ];
      scenarioLines.forEach(line => {
        doc.text(line, marginLeft, cursorY);
        cursorY += 14;
      });

      cursorY += 6;
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(12);
      doc.text('Mission Outcomes', marginLeft, cursorY);
      cursorY += 16;

      doc.setFont('helvetica', 'normal');
      const outcomeLines = [
        `Duration: ${stats.duration.toFixed(1)} seconds`,
        `Friendly Losses: ${stats.friendly_losses}    Enemy Losses: ${stats.enemy_losses}`,
        `Kill Ratio: ${stats.kill_ratio.toFixed(2)} : 1`,
        `Survival Rate: ${(stats.survival_rate * 100).toFixed(1)}%`,
        `Assets Protected: ${stats.assets_protected}`,
        `Mission Result: ${stats.mission_success ? 'SUCCESS' : 'FAILURE'}`
      ];
      outcomeLines.forEach(line => {
        doc.text(line, marginLeft, cursorY);
        cursorY += 14;
      });

      cursorY += 6;
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(12);
      doc.text('Analytics Snapshot', marginLeft, cursorY);
      cursorY += 16;

      doc.setFont('helvetica', 'normal');
      const analyticsLines = [
        `Frames Captured: ${reportPayload.frames.length}`,
        `Timeline Samples: ${analytics.timestamps?.length ?? 0}`,
        `Last Timestamp: ${analytics.timestamps?.length ? analytics.timestamps[analytics.timestamps.length - 1].toFixed(1) : '—'} s`
      ];
      analyticsLines.forEach(line => {
        doc.text(line, marginLeft, cursorY);
        cursorY += 14;
      });

      if (scenario?.assets?.length) {
        cursorY += 6;
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(12);
        doc.text('Asset Placement (metres)', marginLeft, cursorY);
        cursorY += 16;

        doc.setFont('helvetica', 'normal');
        scenario.assets.forEach((asset, index) => {
          const [x = 0, y = 0, z = 0] = asset.position ?? [];
          const value = asset.value ?? 1;
          doc.text(`Asset ${index + 1}: X ${x}, Y ${y}, Z ${z}, Value ${value}`, marginLeft, cursorY);
          cursorY += 14;
        });
      }

      doc.save(`simulation_report_${currentSim ?? 'session'}.pdf`);
      return;
    }

    const blob = new Blob([JSON.stringify(reportPayload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `simulation_report_${currentSim ?? 'session'}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const activeFrame = frames[currentFrame];
  const currentAlgorithmMeta = swarmAlgorithmOptions.find(option => option.value === swarmAlgorithm) ?? swarmAlgorithmOptions[0] ?? null;
  const lastRunAlgorithmMeta = lastScenario?.swarm_algorithm
    ? swarmAlgorithmOptions.find(option => option.value === lastScenario.swarm_algorithm) ?? null
    : null;
  const infoAlgorithmMeta = lastRunAlgorithmMeta ?? currentAlgorithmMeta;
  const CurrentAlgorithmIcon = currentAlgorithmMeta?.icon;

  return (
    <>
    <div className={`app-shell min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 text-gray-100 p-6 ${showLanding ? 'app-shell--masked' : ''}`}>
      <div className="max-w-[2000px] mx-auto space-y-6">
        <div className="border border-cyan-900/40 rounded-xl bg-black/40 backdrop-blur-md p-6 shadow-2xl shadow-cyan-900/20">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
            <div>
              <h1 className="text-4xl font-bold bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent flex items-center gap-3">
                <Zap className="w-10 h-10 text-cyan-400" />
                AeroSentinel
              </h1>
              <p className="text-gray-400 text-sm mt-2 ml-14">
                Quantum-Inspired Probabilistic Field Defence (QIPFD) Tactical Simulation Suite
              </p>
            </div>
            <div className="flex flex-wrap gap-3 items-center">
              <button
                onClick={() => setShowCustom(true)}
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 rounded-lg flex items-center gap-2 transition-all shadow-lg shadow-purple-500/50"
              >
                <Plus className="w-4 h-4" />
                Custom Scenario
              </button>
              <button
                onClick={() => setShowSettings(true)}
                className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 rounded-lg flex items-center gap-2 transition-all shadow-lg shadow-cyan-500/50"
              >
                <Settings className="w-4 h-4" />
                Presets
              </button>
              {analytics && (
                <button
                  onClick={() => setShowAnalytics(true)}
                  className="px-4 py-2 bg-gradient-to-r from-orange-600 to-orange-500 hover:from-orange-500 hover:to-orange-400 rounded-lg flex items-center gap-2 transition-all shadow-lg shadow-orange-500/50"
                >
                  <BarChart3 className="w-4 h-4" />
                  Analytics
                </button>
              )}
              {stats && analytics && (
                <div className="flex flex-wrap gap-2 ml-auto">
                  <button
                    onClick={() => downloadReport('pdf')}
                    className="px-4 py-2 rounded-lg text-sm font-semibold bg-gradient-to-r from-sky-600/80 to-blue-500/80 hover:from-sky-500/90 hover:to-blue-400/90 flex items-center gap-2 shadow-lg shadow-sky-500/30"
                  >
                    <Download className="w-4 h-4" /> PDF Report
                  </button>
                  <button
                    onClick={() => downloadReport('json')}
                    className="px-4 py-2 rounded-lg text-sm font-semibold bg-gradient-to-r from-cyan-700/70 to-cyan-500/70 hover:from-cyan-600/90 hover:to-cyan-400/90 flex items-center gap-2 shadow-lg shadow-cyan-500/30"
                  >
                    <Download className="w-4 h-4" /> JSON Report
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {error && (
          <div className="p-4 bg-red-900/30 border border-red-700/40 rounded-lg flex items-center gap-3 backdrop-blur-sm">
            <AlertCircle className="w-5 h-5 text-red-400" />
            <span className="text-red-300 text-sm">{error}</span>
          </div>
        )}

        {loading && (
          <div className="p-4 bg-cyan-900/30 border border-cyan-700/40 rounded-lg flex items-center gap-3 backdrop-blur-sm">
            <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-cyan-500"></div>
            <span className="text-sm">Running simulation... computing swarm dynamics</span>
          </div>
        )}

        <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
          <div className="xl:col-span-3 space-y-4">
            <div className="bg-black/40 backdrop-blur rounded-xl border border-cyan-900/40 shadow-2xl">
              <div className="flex items-center justify-between px-4 py-3 border-b border-cyan-900/30">
                <h3 className="text-xl font-semibold flex items-center gap-2">
                  <Camera className="w-5 h-5 text-cyan-400" />
                  Tactical Battlefield View
                </h3>
                <div className="flex gap-2">
                  <button
                    onClick={() => setShowControls(prev => !prev)}
                    className="p-2 bg-gray-700 hover:bg-gray-600 rounded transition-colors"
                    title="Toggle Controls"
                  >
                    <Sliders className="w-4 h-4" />
                  </button>
                </div>
              </div>

              <div className="relative">
                <div
                  ref={mountRef}
                  className="w-full bg-black rounded-b-xl border border-cyan-900/30"
                  style={{ height: '600px' }}
                />

                <div className="absolute left-4 bottom-4 flex flex-col gap-2 pointer-events-none">
                  <button
                    onClick={() => setShowGrid(prev => !prev)}
                    className={`pointer-events-auto flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium transition-colors backdrop-blur bg-black/70 border-cyan-500/40 hover:bg-cyan-500/20 ${showGrid ? 'text-cyan-200' : 'text-gray-300'}`}
                    title="Toggle Grid"
                  >
                    {showGrid ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                    <span>{showGrid ? 'Hide Grid' : 'Show Grid'}</span>
                  </button>
                  <button
                    onClick={() => setCameraMode(prev => (prev === 'orbital' ? 'static' : 'orbital'))}
                    className="pointer-events-auto flex items-center gap-2 px-3 py-2 rounded-lg border text-sm font-medium transition-colors backdrop-blur bg-black/70 border-cyan-500/40 hover:bg-cyan-500/20 text-cyan-200"
                    title="Switch Camera Mode"
                  >
                    <Maximize2 className="w-4 h-4" />
                    <span>{cameraMode === 'orbital' ? 'Static Camera' : 'Orbital Camera'}</span>
                  </button>
                </div>
              </div>
            </div>

            {showControls && (
              <div className="bg-gray-900/50 border border-gray-800/60 rounded-xl p-4 backdrop-blur">
                <div className="flex flex-wrap items-center gap-3">
                  <button
                    onClick={() => setPlaying(prev => !prev)}
                    disabled={frames.length === 0}
                    className="px-6 py-3 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 disabled:from-gray-700 disabled:to-gray-700 rounded-lg flex items-center gap-2 transition-all font-semibold shadow-lg disabled:cursor-not-allowed"
                  >
                    {playing ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                    {playing ? 'Pause' : 'Play'}
                  </button>

                  <button
                    onClick={() => { setCurrentFrame(0); setPlaying(false); }}
                    disabled={frames.length === 0}
                    className="px-4 py-3 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 rounded-lg transition-all disabled:cursor-not-allowed"
                    title="Restart"
                  >
                    <RotateCcw className="w-5 h-5" />
                  </button>

                  <button
                    onClick={() => { 
                      setCurrentFrame(Math.max(0, currentFrame - 50)); 
                      setPlaying(false); 
                    }}
                    disabled={frames.length === 0 || currentFrame === 0}
                    className="px-4 py-3 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 rounded-lg transition-all disabled:cursor-not-allowed"
                    title="Skip back 50 frames"
                  >
                    <SkipBack className="w-5 h-5" />
                  </button>

                  <button
                    onClick={() => { 
                      setCurrentFrame(Math.min(frames.length - 1, currentFrame + 50)); 
                      setPlaying(false); 
                    }}
                    disabled={frames.length === 0 || currentFrame >= frames.length - 1}
                    className="px-4 py-3 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 rounded-lg transition-all disabled:cursor-not-allowed"
                    title="Skip forward 50 frames"
                  >
                    <SkipForward className="w-5 h-5" />
                  </button>

                  <button
                    onClick={() => { 
                      setCurrentFrame(frames.length - 1); 
                      setPlaying(false);
                      console.log('[Playback] Jumped to end, frame:', frames.length - 1);
                    }}
                    disabled={frames.length === 0}
                    className="px-4 py-3 bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 disabled:from-gray-700 disabled:to-gray-700 rounded-lg transition-all disabled:cursor-not-allowed font-semibold"
                    title="Jump to End"
                  >
                    End
                  </button>

                  <button
                    onClick={() => setShowDynamic(true)}
                    className="px-3 py-3 bg-gray-800 hover:bg-gray-700 rounded-lg text-sm"
                    title="Dynamic Simulation"
                  >
                    Dynamic
                  </button>

                  <div className="flex-1 min-w-[200px]">
                    <input
                      type="range"
                      min="0"
                      max={Math.max(frames.length - 1, 0)}
                      value={currentFrame}
                      onChange={(e) => setCurrentFrame(parseInt(e.target.value, 10))}
                      disabled={frames.length === 0}
                      className="w-full h-3 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                    />
                  </div>

                  <span className="text-sm text-gray-400 font-mono min-w-[140px] text-right bg-gray-800 px-3 py-2 rounded flex flex-col">
                    <span>{frames.length > 0 ? `Frame ${currentFrame + 1} / ${frames.length}` : 'No data'}</span>
                    {frames.length > 0 && (
                      <span className="text-xs text-gray-500">
                        {((currentFrame / Math.max(frames.length - 1, 1)) * 100).toFixed(1)}% complete
                      </span>
                    )}
                  </span>
                </div>

                <div className="flex items-center gap-4 mt-4">
                  <span className="text-sm text-gray-400">Speed:</span>
                  <input
                    type="range"
                    min="0.25"
                    max="4"
                    step="0.25"
                    value={playSpeed}
                    onChange={(e) => setPlaySpeed(parseFloat(e.target.value))}
                    className="flex-1 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-cyan-500"
                  />
                  <span className="text-sm text-cyan-400 font-mono min-w-[40px]">{playSpeed}x</span>
                </div>

                {activeFrame && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-4 text-sm">
                    <div className="bg-gray-800/70 p-3 rounded-lg">
                      <span className="text-gray-400">Time</span>
                      <span className="text-cyan-400 ml-2 font-mono">{activeFrame.time.toFixed(1)}s</span>
                    </div>
                    <div className="bg-gray-800/70 p-3 rounded-lg">
                      <span className="text-gray-400">Friendlies</span>
                      <span className="text-green-400 ml-2 font-mono">{activeFrame.friendlies.filter(d => d.health > 0).length}</span>
                    </div>
                    <div className="bg-gray-800/70 p-3 rounded-lg">
                      <span className="text-gray-400">Enemies</span>
                      <span className="text-red-400 ml-2 font-mono">{activeFrame.enemies.filter(d => d.health > 0).length}</span>
                    </div>
                    <div className="bg-gray-800/70 p-3 rounded-lg">
                      <span className="text-gray-400">Interceptors</span>
                      <span className="text-pink-400 ml-2 font-mono">{activeFrame.friendlies.filter(d => d.role === 'interceptor' && d.health > 0).length}</span>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div className="bg-black/40 backdrop-blur rounded-xl border border-cyan-900/40 p-4 space-y-3">
              <label className="flex items-center gap-2 text-lg font-semibold" htmlFor="swarm-algorithm-select">
                <Aperture className="w-5 h-5 text-cyan-400" />
                <span>Swarm Algorithm</span>
              </label>
              <p className="text-xs text-gray-400">
                Choose the coordination strategy that sets your swarm formation and engagement posture before each launch.
              </p>
              <select
                id="swarm-algorithm-select"
                value={swarmAlgorithm}
                onChange={(event) => {
                  const nextValue = event.target.value;
                  setSwarmAlgorithm(nextValue);
                  setCustomConfig(prev => ({ ...prev, swarm_algorithm: nextValue }));
                }}
                className="w-full rounded-lg border border-cyan-900/50 bg-black/60 px-3 py-2 text-sm text-cyan-100 focus:border-cyan-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/40"
              >
                {swarmAlgorithmOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
              {currentAlgorithmMeta && (
                <div className="flex items-start gap-3 rounded-xl border border-cyan-900/40 bg-cyan-500/5 px-3 py-3">
                  <span className="mt-1 inline-flex h-9 w-9 items-center justify-center rounded-full border border-cyan-400/60 bg-cyan-500/10 text-cyan-200">
                    <CurrentAlgorithmIcon className="w-4 h-4" />
                  </span>
                  <div>
                    <p className="font-semibold text-sm text-cyan-100">{currentAlgorithmMeta.label}</p>
                    <p className="text-xs text-gray-400 leading-relaxed">{currentAlgorithmMeta.description}</p>
                  </div>
                </div>
              )}
            </div>

            <div className="bg-black/40 backdrop-blur rounded-xl border border-cyan-900/40 p-4 space-y-3">
              <div className="flex items-center gap-2 text-lg font-semibold">
                <Zap className="w-5 h-5 text-cyan-400" />
                <span>Mission Status</span>
              </div>

              {stats ? (
                <div className="space-y-2 text-sm">
                  {[{
                    label: 'Duration',
                    value: `${(stats.duration || 0).toFixed(1)}s`,
                    color: 'text-gray-300'
                  }, {
                    label: 'Friendly Losses',
                    value: stats.friendly_losses || 0,
                    color: 'text-red-400'
                  }, {
                    label: 'Enemy Destroyed',
                    value: stats.enemy_losses || 0,
                    color: 'text-green-400'
                  }, {
                    label: 'Kill Ratio',
                    value: `${(stats.kill_ratio || 0).toFixed(2)}:1`,
                    color: 'text-cyan-400'
                  }, {
                    label: 'Survival Rate',
                    value: `${((stats.survival_rate || 0) * 100).toFixed(1)}%`,
                    color: 'text-blue-400'
                  }, {
                    label: 'Assets Protected',
                    value: stats.assets_protected || 0,
                    color: 'text-green-400'
                  }].map((item) => (
                    <div
                      key={item.label}
                      className="flex justify-between py-2 border-b border-gray-800/50 hover:bg-gray-800/30 px-2 rounded transition-colors"
                    >
                      <span className="text-gray-400">{item.label}:</span>
                      <span className={`font-mono font-semibold ${item.color}`}>{item.value}</span>
                    </div>
                  ))}

                  <div className={`mt-4 p-4 rounded-lg font-bold text-center text-sm shadow-lg ${
                    stats.mission_success
                      ? 'bg-gradient-to-r from-green-900/50 to-green-800/50 text-green-400 border border-green-700/50'
                      : 'bg-gradient-to-r from-red-900/50 to-red-800/50 text-red-400 border border-red-700/50'
                  }`}>
                    {stats.mission_success ? '✓ MISSION SUCCESS' : '✗ MISSION FAILED'}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <AlertCircle className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No simulation data</p>
                  <p className="text-xs mt-1">Launch a scenario to begin</p>
                </div>
              )}
            </div>

            {currentSim && (
              <div className="bg-gray-900/40 border border-gray-800/50 rounded-xl p-4 text-sm">
                <h4 className="text-gray-300 font-semibold mb-2">Simulation Info</h4>
                <p className="text-gray-400">
                  Session ID: <span className="font-mono text-cyan-400">{currentSim}</span>
                </p>
                {infoAlgorithmMeta && (
                  <p className="text-gray-400 mt-1">
                    Formation Mode: <span className="font-semibold text-cyan-300">{infoAlgorithmMeta.label}</span>
                  </p>
                )}
              </div>
            )}

            <LegendPanel activeFrame={activeFrame} />
          </div>
        </div>
      </div>

      {showSettings && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center z-50 p-6">
          <div className="bg-gray-900/90 border border-cyan-900/40 rounded-2xl p-6 w-full max-w-3xl">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-semibold text-cyan-300">Preset Scenarios</h2>
              <button onClick={() => setShowSettings(false)} className="text-gray-400 hover:text-gray-200">✕</button>
            </div>
            <div className="grid md:grid-cols-2 gap-4">
              {Object.entries(presets).map(([key, preset]) => (
                <div key={key} className="bg-black/40 border border-cyan-900/30 rounded-xl p-4 flex flex-col gap-2">
                  <h3 className="text-lg font-semibold text-cyan-200">{preset.name}</h3>
                  <div className="text-xs text-gray-400 grid grid-cols-2 gap-1">
                    <span>Friendlies: <strong className="text-green-300">{preset.friendly_count}</strong></span>
                    <span>Enemies: <strong className="text-red-300">{preset.enemy_count}</strong></span>
                    <span>Max Time: <strong>{preset.max_time}s</strong></span>
                    <span>Speed: <strong>{preset.max_speed}m/s</strong></span>
                  </div>
                  <button
                    onClick={() => startSimulation(preset)}
                    className="mt-3 px-4 py-2 bg-gradient-to-r from-cyan-600 to-cyan-500 hover:from-cyan-500 hover:to-cyan-400 rounded-lg text-sm font-semibold"
                  >
                    Launch Scenario
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {showCustom && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md overflow-y-auto z-50 p-6">
          <div className="bg-gray-900/90 border border-purple-900/40 rounded-2xl p-6 w-full max-w-4xl mx-auto space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-semibold text-purple-200">Custom Scenario Builder</h2>
              <div className="flex gap-2">
                <button
                  onClick={saveCustomScenario}
                  className="px-3 py-2 text-xs bg-purple-700/60 hover:bg-purple-600/60 rounded-lg"
                >
                  Save Config
                </button>
                <label className="px-3 py-2 text-xs bg-gray-800 hover:bg-gray-700 rounded-lg cursor-pointer">
                  Load Config
                  <input type="file" accept="application/json" className="hidden" onChange={loadCustomScenario} />
                </label>
                <button onClick={() => setShowCustom(false)} className="text-gray-400 hover:text-gray-200">✕</button>
              </div>
            </div>

            <div className="grid md:grid-cols-2 gap-6 text-sm">
              <div className="space-y-3">
                <label className="block">
                  <span className="text-gray-400">Scenario Name</span>
                  <input
                    type="text"
                    value={customConfig.name}
                    onChange={(e) => handleCustomChange('name', e.target.value)}
                    className="mt-1 w-full bg-black/40 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </label>
                <label className="block">
                  <span className="text-gray-400">Swarm Algorithm</span>
                  <select
                    value={customConfig.swarm_algorithm ?? swarmAlgorithm}
                    onChange={(e) => {
                      const val = e.target.value;
                      handleCustomChange('swarm_algorithm', val);
                      setSwarmAlgorithm(val);
                    }}
                    className="mt-1 w-full bg-black/40 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  >
                    {swarmAlgorithmOptions.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </label>
                <label className="block">
                  <span className="text-gray-400">Friendly Count</span>
                  <input
                    type="number"
                    value={customConfig.friendly_count === '' ? '' : customConfig.friendly_count}
                    onChange={(e) => handleCustomChange('friendly_count', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                    className="mt-1 w-full bg-black/40 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </label>
                <label className="block">
                  <span className="text-gray-400">Enemy Count</span>
                  <input
                    type="number"
                    value={customConfig.enemy_count === '' ? '' : customConfig.enemy_count}
                    onChange={(e) => handleCustomChange('enemy_count', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                    className="mt-1 w-full bg-black/40 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </label>
                <label className="block">
                  <span className="text-gray-400">Ground Attack Ratio</span>
                  <input
                    type="number"
                    step="0.05"
                    value={customConfig.ground_attack_ratio === '' ? '' : customConfig.ground_attack_ratio}
                    onChange={(e) => handleCustomChange('ground_attack_ratio', e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="mt-1 w-full bg-black/40 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </label>
              </div>
              <div className="space-y-3">
                <label className="block">
                  <span className="text-gray-400">Max Time (s)</span>
                  <input
                    type="number"
                    value={customConfig.max_time === '' ? '' : customConfig.max_time}
                    onChange={(e) => handleCustomChange('max_time', e.target.value === '' ? '' : parseInt(e.target.value, 10))}
                    className="mt-1 w-full bg-black/40 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </label>
                <label className="block">
                  <span className="text-gray-400">Max Speed (m/s)</span>
                  <input
                    type="number"
                    value={customConfig.max_speed === '' ? '' : customConfig.max_speed}
                    onChange={(e) => handleCustomChange('max_speed', e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="mt-1 w-full bg-black/40 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </label>
                <label className="block">
                  <span className="text-gray-400">Weapon Range (m)</span>
                  <input
                    type="number"
                    value={customConfig.weapon_range === '' ? '' : customConfig.weapon_range}
                    onChange={(e) => handleCustomChange('weapon_range', e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="mt-1 w-full bg-black/40 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </label>
                <label className="block">
                  <span className="text-gray-400">Detection Range (m)</span>
                  <input
                    type="number"
                    value={customConfig.detection_range === '' ? '' : customConfig.detection_range}
                    onChange={(e) => handleCustomChange('detection_range', e.target.value === '' ? '' : parseFloat(e.target.value))}
                    className="mt-1 w-full bg-black/40 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                  />
                </label>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-purple-200">Assets</h3>
                <button
                  onClick={addAsset}
                  className="px-3 py-2 text-xs bg-purple-700/60 hover:bg-purple-600/60 rounded-lg"
                >
                  Add Asset
                </button>
              </div>

              <div className="space-y-2">
                {customConfig.assets.map((asset, index) => (
                  <div
                    key={index}
                    className={`bg-black/40 border rounded-xl p-4 space-y-4 text-sm transition-colors placement-card ${selectedAssetIndex === index ? 'border-purple-500/70 shadow-lg shadow-purple-900/30' : 'border-purple-900/30'}`}
                  >
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-purple-100 font-semibold">Asset {index + 1}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          Position:
                          <span className="ml-2 font-mono text-purple-200">X {asset.position?.[0] ?? 0}</span>
                          <span className="ml-3 font-mono text-purple-200">Y {asset.position?.[1] ?? 0}</span>
                          <span className="ml-3 font-mono text-purple-200">Z {asset.position?.[2] ?? 0}</span>
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button
                          onClick={() => setSelectedAssetIndex(index)}
                          className={`px-3 py-2 rounded-lg text-xs flex items-center gap-2 transition-all ${selectedAssetIndex === index ? 'bg-purple-600/70 hover:bg-purple-600 text-white' : 'bg-purple-700/40 hover:bg-purple-600/60 text-purple-100'}`}
                        >
                          <MapPin className="w-4 h-4" />
                          Place on Map
                        </button>
                        <button
                          onClick={() => removeAsset(index)}
                          className="px-3 py-2 bg-red-600/60 hover:bg-red-600 rounded-lg text-xs"
                        >
                          Remove
                        </button>
                      </div>
                    </div>

                    <div className="grid sm:grid-cols-2 gap-4">
                      <label className="block">
                        <span className="text-gray-400">Altitude (Y)</span>
                        <input
                          type="number"
                          step="10"
                          value={asset.position?.[1] ?? 0}
                          onChange={(e) => updateAssetPosition(index, 1, e.target.value)}
                          className="mt-1 w-full bg-black/40 border border-gray-700 rounded-lg px-3 py-2 text-gray-200"
                        />
                      </label>
                      <div>
                        <span className="text-gray-400">Strategic Value</span>
                        <div className="mt-2 flex items-center gap-3">
                          <input
                            type="range"
                            min="0.5"
                            max="3"
                            step="0.1"
                            value={asset.value ?? 1}
                            onChange={(e) => updateAssetValue(index, e.target.value)}
                            className="flex-1 accent-purple-500"
                          />
                          <span className="font-mono text-purple-200 text-xs">{(asset.value ?? 1).toFixed(1)}x</span>
                        </div>
                      </div>
                    </div>

                    <p className="text-xs text-gray-400">
                      Tip: Select an asset, then click anywhere on the holographic grid below to reposition it quickly. Use altitude to raise or lower the platform.
                    </p>
                  </div>
                ))}
              </div>

              {customConfig.assets.length > 0 && (
                <AssetPlacementMap
                  assets={customConfig.assets}
                  selectedIndex={selectedAssetIndex}
                  onSelectAsset={setSelectedAssetIndex}
                  onPositionChange={setAssetGroundPosition}
                />
              )}

              <div className="flex justify-end gap-3">
                <button
                  onClick={() => setShowCustom(false)}
                  className="px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  onClick={() => startSimulation(customConfig)}
                  className="px-4 py-2 bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 rounded-lg font-semibold"
                >
                  Launch Custom Scenario
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {showDynamic && (
        <DynamicPage onClose={() => setShowDynamic(false)} />
      )}
    </div>

    {showLanding && (
      <LandingPage onDismiss={handleLandingDismiss} isExiting={landingExiting} />
    )}

    {showAnalytics && analytics && (
      <AnalyticsDashboard
        simulationId={currentSim}
        onClose={() => setShowAnalytics(false)}
      />
    )}
  </>
  );
};

export default EnhancedDroneSwarmSystem;