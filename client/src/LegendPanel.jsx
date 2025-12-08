import React from 'react';
import { Palette } from 'lucide-react';

const LegendPanel = ({ activeFrame }) => {
  const friendlyCount = activeFrame?.friendlies?.filter(d => d.health > 0).length ?? 0;
  const enemyCount = activeFrame?.enemies?.filter(d => d.health > 0).length ?? 0;

  const legendItems = [

    {
      label: 'Friendly Drone (Defender)',
      description: 'Orange sphere — fast pursuit units that chase down intruders.',
      shape: 'circle',
      color: 'bg-orange-600'
    },
    {
      label: 'Enemy Air Threat',
      description: 'Orange cone — incoming hostile air drones breaching the perimeter.',
      shape: 'triangle',
      color: 'bg-orange-500'
    },
    {
      label: 'Enemy Ground Threat',
      description: 'Red square — armoured ground attackers targeting strategic assets.',
      shape: 'square',
      color: 'bg-red-600'
    },
    {
      label: 'Strategic Asset Zone',
      description: 'Green cylinder — critical infrastructure that must remain secure.',
      shape: 'circle',
      color: 'bg-green-500'
    },
    {
      label: 'Targeting Beam',
      description: 'Red line — shows active engagement corridors during combat.',
      shape: 'line',
      color: 'bg-red-500'
    }
  ];

  const renderShape = (shape, color) => {
    if (shape === 'circle') {
      return <div className={`w-3 h-3 rounded-full ${color}`}></div>;
    } else if (shape === 'square') {
      return <div className={`w-3 h-3 ${color}`}></div>;
    } else if (shape === 'triangle') {
      return (
        <div className="w-3 h-3 relative">
          <div className={`w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-b-[12px] ${color.replace('bg-', 'border-b-')}`}></div>
        </div>
      );
    } else if (shape === 'line') {
      return <div className={`w-6 h-0.5 ${color}`}></div>;
    }
    return null;
  };

  return (
    <div className="hologram-card border border-accent/40 rounded-xl p-4 bg-black/40 backdrop-blur space-y-4">
      <div className="flex items-center justify-between flex-col gap-3">
        <div className="flex items-center gap-2 text-white font-semibold">
          <Palette className="w-5 h-5 text-white/40" />
          Battlefield Legend
        </div>
        <div className="text-xs text-gray-400 flex items-center gap-3">
          <span className="chip-readout chip-readout--friendly">Friendly {friendlyCount}</span>
          <span className="chip-readout chip-readout--enemy">Enemy {enemyCount}</span>
        </div>
      </div>

      <div className="space-y-3">
        <p className="legend-note">
          Colour key : green assets indicate friendlies, orange markers show hunters, blue highlights interceptors, red/crimson mark enemy forces (squares are ground enemies, cones are air enemies), and yellow zones flag protected infrastructure.
        </p>
        {legendItems.map(item => (
          <div key={item.label} className="legend-row">
            <span className="flex items-center justify-center w-6 pt-2" aria-hidden="true">
              {renderShape(item.shape, item.color)}
            </span>
            <div className="flex-1">
              <p className="legend-label">{item.label}</p>
              <p className="legend-description">{item.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LegendPanel;
