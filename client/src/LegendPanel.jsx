import React from 'react';
import { Palette } from 'lucide-react';
import LegendDronePreview from './components/LegendDronePreview.jsx';

const LegendPanel = ({ activeFrame }) => {
  const friendlyCount = activeFrame?.friendlies?.filter(d => d.health > 0).length ?? 0;
  const enemyCount = activeFrame?.enemies?.filter(d => d.health > 0).length ?? 0;

  const legendItems = [
    {
      label: 'Friendly Drone (Defender)',
      description: 'Cyan interceptors with high-agility props guard the inner perimeter.',
      type: 'drone',
      preview: {
        color: 0x00aaff,
        accent: 0xe6f4ff,
        propellerColor: 0xffffff,
        showLandingSkids: false
      }
    },
    {
      label: 'Enemy Air Threat',
      description: 'Amber strike drones dive from above with heated rotor signatures.',
      type: 'drone',
      preview: {
        color: 0xff9933,
        accent: 0xffc199,
        propellerColor: 0x331100,
        showLandingSkids: false
      }
    },
    {
      label: 'Enemy Ground Threat',
      description: 'Scarlet gunship variants with landing skids hug the canyon floor.',
      type: 'drone',
      preview: {
        color: 0xff3333,
        accent: 0x401010,
        propellerColor: 0x1a0000,
        showLandingSkids: true
      }
    },
    {
      label: 'Strategic Asset Zone',
      description: 'Green resonant halo designates shielded mission infrastructure.',
      type: 'shape',
      shape: 'circle',
      colorClass: 'bg-green-500'
    },
    {
      label: 'Targeting Beam',
      description: 'Red vectored beam shows live engagement corridors during combat.',
      type: 'shape',
      shape: 'line',
      colorClass: 'bg-red-500'
    }
  ];

  const renderShape = (shape, colorClass) => {
    if (shape === 'circle') {
      return <div className={`w-3 h-3 rounded-full ${colorClass}`}></div>;
    } else if (shape === 'square') {
      return <div className={`w-3 h-3 ${colorClass}`}></div>;
    } else if (shape === 'triangle') {
      return (
        <div className="w-3 h-3 relative">
          <div className={`w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-b-[12px] ${colorClass.replace('bg-', 'border-b-')}`}></div>
        </div>
      );
    } else if (shape === 'line') {
      return <div className={`w-6 h-0.5 ${colorClass}`}></div>;
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
          Colour key : cyan drones are friendlies, hot amber marks airborne intruders, crimson frames belong to armoured ground units, while luminous green halos remain strategic assets.
        </p>
        {legendItems.map(item => (
          <div key={item.label} className="legend-row">
            <span className="flex items-center justify-center w-16 pt-1" aria-hidden="true">
              {item.type === 'drone' ? (
                <LegendDronePreview {...item.preview} />
              ) : (
                renderShape(item.shape, item.colorClass)
              )}
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
