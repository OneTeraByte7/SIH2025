import React, { useState, useRef, useCallback } from 'react';
import { MapPin } from 'lucide-react';
import { MAP_EXTENT } from './constants';

const AssetPlacementMap = ({ assets, selectedIndex, onSelectAsset, onPositionChange }) => {
  const containerRef = useRef(null);
  const svgRef = useRef(null);
  const [draggingIndex, setDraggingIndex] = useState(null);

  const convertToPercent = useCallback((position) => {
    const [x = 0, , z = 0] = Array.isArray(position) ? position : [0, 0, 0];
    const clampedX = Math.max(-MAP_EXTENT, Math.min(MAP_EXTENT, x));
    const clampedZ = Math.max(-MAP_EXTENT, Math.min(MAP_EXTENT, z));

    const cx = ((clampedX + MAP_EXTENT) / (MAP_EXTENT * 2)) * 100;
    const cy = (1 - ((clampedZ + MAP_EXTENT) / (MAP_EXTENT * 2))) * 100;
    return { cx, cy };
  }, []);

  const computeWorldCoords = useCallback((event) => {
    if (!svgRef.current || !containerRef.current) return null;
    const svg = svgRef.current;
    const point = svg.createSVGPoint();
    point.x = event.clientX;
    point.y = event.clientY;

    const transformed = point.matrixTransform(svg.getScreenCTM().inverse());
    const clampedX = Math.max(0, Math.min(100, transformed.x));
    const clampedY = Math.max(0, Math.min(100, transformed.y));

    const normX = clampedX / 100;
    const normY = clampedY / 100;
    const x = Number(((normX - 0.5) * MAP_EXTENT * 2).toFixed(1));
    const z = Number(((0.5 - normY) * MAP_EXTENT * 2).toFixed(1));

    const rect = containerRef.current.getBoundingClientRect();
    return {
      x,
      z,
      left: (clampedX / 100) * rect.width,
      top: (clampedY / 100) * rect.height
    };
  }, []);

  const handlePointerMove = useCallback((event) => {
    if (draggingIndex == null) return;
    const coords = computeWorldCoords(event);
    if (!coords) return;
    onPositionChange(draggingIndex, coords.x, coords.z);
  }, [computeWorldCoords, draggingIndex, onPositionChange]);

  const handlePointerUp = useCallback(() => {
    setDraggingIndex(null);
  }, []);

  const handlePointerDown = useCallback((event) => {
    if (event.target?.tagName?.toLowerCase() === 'circle') return;
    if (selectedIndex == null || selectedIndex < 0) return;
    const coords = computeWorldCoords(event);
    if (!coords) return;
    onPositionChange(selectedIndex, coords.x, coords.z);
  }, [computeWorldCoords, onPositionChange, selectedIndex]);

  return (
    <div className="hologram-card border border-purple-900/40 rounded-xl p-4 bg-black/30 backdrop-blur space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-purple-200 font-semibold">
          <MapPin className="w-5 h-5" />
          Asset Placement Map
        </div>
      </div>

      <div
        ref={containerRef}
        className="asset-map-container"
        onPointerMove={handlePointerMove}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
        onPointerDown={handlePointerDown}
      >
        <svg ref={svgRef} viewBox="0 0 100 100" className="asset-map">
          {[...Array(10)].map((_, idx) => {
            const pos = (idx + 1) * 10;
            return (
              <g key={pos}>
                <line x1="0" y1={pos} x2="100" y2={pos} className="asset-map-grid" />
                <line x1={pos} y1="0" x2={pos} y2="100" className="asset-map-grid" />
              </g>
            );
          })}
          <line x1="0" y1="50" x2="100" y2="50" className="asset-map-axis" />
          <line x1="50" y1="0" x2="50" y2="100" className="asset-map-axis" />

          {assets.map((asset, index) => {
            const { cx, cy } = convertToPercent(asset.position);
            const isSelected = index === selectedIndex;
            return (
              <circle
                key={`asset-marker-${index}`}
                cx={cx}
                cy={cy}
                r={isSelected ? 3.8 : 3}
                className={`asset-map-marker ${isSelected ? 'asset-map-marker--active' : ''}`}
                onPointerDown={(event) => {
                  event.stopPropagation();
                  if (event.target.setPointerCapture) {
                    event.target.setPointerCapture(event.pointerId);
                  }
                  onSelectAsset(index);
                  setDraggingIndex(index);
                }}
                onPointerMove={(event) => {
                  if (draggingIndex !== index) return;
                  event.stopPropagation();
                  handlePointerMove(event);
                }}
                onPointerUp={(event) => {
                  event.stopPropagation();
                  if (event.target.releasePointerCapture) {
                    event.target.releasePointerCapture(event.pointerId);
                  }
                  setDraggingIndex(null);
                }}
              />
            );
          })}
        </svg>
      </div>

      <p className="text-xs text-gray-400">
        Drag any marker to reposition its asset on the grid. The centre represents the main base; outer rings show detection range.
      </p>

      <div className="flex flex-wrap gap-2 text-xs">
        {assets.map((_, index) => (
          <button
            key={`asset-select-${index}`}
            onClick={() => onSelectAsset(index)}
            className={`asset-select-chip ${index === selectedIndex ? 'asset-select-chip--active' : ''}`}
          >
            Asset {index + 1}
          </button>
        ))}
      </div>
    </div>
  );
};

export default AssetPlacementMap;
