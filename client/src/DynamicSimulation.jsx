import React, { useState, useEffect, useRef } from 'react';
import { X, Play, RefreshCw } from 'lucide-react';

const API_BASE = 'http://localhost:5000/api';

export default function DynamicSimulation({ onClose }) {
  const [simId, setSimId] = useState(null);
  const [status, setStatus] = useState(null);
  const [frames, setFrames] = useState([]);
  const [loading, setLoading] = useState(false);
  const pollRef = useRef(null);

  const startSimulation = async () => {
    setLoading(true);
    try {
      // Simple asset path: straight line across X axis
      const asset_path = [
        { time: 0, position: [ -500, 0, 0 ] },
        { time: 5, position: [ 0, 0, 0 ] },
        { time: 10, position: [ 500, 0, 0 ] }
      ];

      const res = await fetch(`${API_BASE}/dynamic/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ asset_path })
      });
      if (!res.ok) throw new Error('Failed to start');
      const data = await res.json();
      setSimId(data.id || data.simulation_id || data.sim_id || data.uuid || data.id_tag || null);
      setStatus('running');
    } catch (err) {
      console.error(err);
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!simId) return;

    const poll = async () => {
      try {
        const res = await fetch(`${API_BASE}/dynamic/${simId}/status`);
        if (!res.ok) throw new Error('status fetch failed');
        const data = await res.json();
        setStatus(data.status || data.state || 'running');
        if (data.complete || data.status === 'complete' || data.state === 'complete') {
          clearInterval(pollRef.current);
          pollRef.current = null;
          // fetch final data
          const r2 = await fetch(`${API_BASE}/dynamic/${simId}/data`);
          if (r2.ok) {
            const payload = await r2.json();
            setFrames(Array.isArray(payload.frames) ? payload.frames : payload.history || []);
          }
        }
      } catch (err) {
        console.warn('dynamic poll error', err);
      }
    };

    pollRef.current = setInterval(poll, 2000);
    // run immediate
    poll();

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
      pollRef.current = null;
    };
  }, [simId]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-6">
      <div className="bg-gray-900/95 border border-cyan-900/40 rounded-2xl w-full max-w-3xl p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-cyan-200">Dynamic Simulation</h3>
          <div className="flex items-center gap-2">
            <button onClick={onClose} className="text-gray-400 hover:text-gray-200"><X /></button>
          </div>
        </div>

        <div className="space-y-3 text-sm">
          <div className="flex gap-2">
            <button
              onClick={startSimulation}
              disabled={loading || !!simId}
              className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-cyan-500 rounded-lg flex items-center gap-2"
            >
              <Play className="w-4 h-4" /> Start
            </button>
            <button
              onClick={async () => {
                if (!simId) return;
                setLoading(true);
                try {
                  const res = await fetch(`${API_BASE}/dynamic/${simId}/data`);
                  if (res.ok) {
                    const p = await res.json();
                    setFrames(Array.isArray(p.frames) ? p.frames : p.history || []);
                  }
                } catch (e) { console.warn(e); }
                setLoading(false);
              }}
              disabled={!simId}
              className="px-3 py-2 bg-gray-800 rounded-lg"
            >
              <RefreshCw className="w-4 h-4" /> Fetch Data
            </button>
          </div>

          <div className="text-xs text-gray-400">
            <div>Status: <strong className="ml-2 text-cyan-300">{status || 'idle'}</strong></div>
            <div>Session: <span className="font-mono text-sm ml-2">{simId || '-'}</span></div>
          </div>

          <div className="mt-3">
            <h4 className="text-sm font-semibold text-gray-200 mb-2">Frames (sample)</h4>
            <div className="max-h-60 overflow-auto bg-black/40 border border-gray-800/30 rounded p-2 text-xs">
              {frames.length === 0 && <div className="text-gray-500">No frames yet</div>}
              {frames.slice(0, 200).map((f, i) => (
                <div key={i} className="py-1 border-b border-gray-800/20">
                  <div className="font-mono text-xs text-cyan-200">t={typeof f.time==='number'?f.time.toFixed(2):f.time}s</div>
                  <div className="text-gray-300">pos: {Array.isArray(f.asset?.position)?f.asset.position.map(v=>Number(v).toFixed(1)).join(', '):JSON.stringify(f.asset?.position)}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
