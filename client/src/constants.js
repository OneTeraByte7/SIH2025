import { Shield, Orbit, Radar, Waves } from "lucide-react";

export const MAP_EXTENT = 1500;
export const API_BASE = "http://localhost:5000/api";

export const legendItems = [
  {
    label: "Friendly Drone (Defender)",
    description:
      "Cyan sphere — perimeter guardians maintaining coverage around key zones.",
    swatch: "legend-chip legend-chip--friendly",
  },
  {
    label: "Hunter / Pursuit Drone",
    description:
      "Orange sphere — fast pursuit units that chase down intruders.",
    swatch: "legend-chip legend-chip--hunter",
  },
  {
    label: "Interceptor Specialist",
    description:
      "Pink sphere — agile response craft prioritising ground-based threats.",
    swatch: "legend-chip legend-chip--interceptor",
  },
  {
    label: "Enemy Air Threat",
    description:
      "Orange cone — incoming hostile air drones breaching the perimeter.",
    swatch: "legend-chip legend-chip--enemy-air",
  },
  {
    label: "Enemy Ground Threat",
    description:
      "Red square — armoured ground attackers targeting strategic assets.",
    swatch: "legend-chip legend-chip--enemy-ground",
  },
  {
    label: "Strategic Asset Zone",
    description:
      "Green cylinder — critical infrastructure that must remain secure.",
    swatch: "legend-chip legend-chip--asset",
  },
  {
    label: "Targeting Beam",
    description: "Red line — shows active engagement corridors during combat.",
    swatch: "legend-chip legend-chip--beam",
  },
];

export const defaultSwarmAlgorithmOptions = [];
