import type { Player } from "@/lib/types";

const AXES: { key: keyof Player; label: string }[] = [
  { key: "surface_win_pct", label: "Grass win %" },
  { key: "recent_win_pct", label: "Recent form" },
  { key: "tournament_win_pct", label: "Wimbledon win %" },
  { key: "surface_hold_rate", label: "Hold rate" },
  { key: "surface_break_rate", label: "Break rate" },
  { key: "tiebreak_win_pct", label: "Tiebreak %" },
];

const SIZE = 280;
const CENTER = SIZE / 2;
const MAX_RADIUS = SIZE / 2 - 40;
const RING_FRACTIONS = [1, 0.66, 0.33];

// Every axis is already a 0-1 percentage, so each value is directly usable
// as a normalized radius — no separate normalization step needed.
function axisPoint(index: number, value: number): { x: number; y: number } {
  const angle = (2 * Math.PI * index) / AXES.length - Math.PI / 2;
  const radius = MAX_RADIUS * value;
  return {
    x: CENTER + radius * Math.cos(angle),
    y: CENTER + radius * Math.sin(angle),
  };
}

function polygonPoints(player: Player): string {
  return AXES.map((axis, i) => {
    const { x, y } = axisPoint(i, player[axis.key] as number);
    return `${x},${y}`;
  }).join(" ");
}

function ringPoints(fraction: number): string {
  return AXES.map((_, i) => {
    const { x, y } = axisPoint(i, fraction);
    return `${x},${y}`;
  }).join(" ");
}

function labelPosition(index: number): {
  x: number;
  y: number;
  anchor: "start" | "end" | "middle";
} {
  const angle = (2 * Math.PI * index) / AXES.length - Math.PI / 2;
  const labelRadius = MAX_RADIUS + 18;
  const x = CENTER + labelRadius * Math.cos(angle);
  const y = CENTER + labelRadius * Math.sin(angle);
  const anchor: "start" | "end" | "middle" =
    Math.cos(angle) > 0.3 ? "start" : Math.cos(angle) < -0.3 ? "end" : "middle";
  return { x, y, anchor };
}

export function PlayerRadarChart({
  favorite,
  underdog,
}: {
  favorite: Player;
  underdog: Player;
}) {
  return (
    <div className="flex flex-col items-center gap-3 py-2">
      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} width="100%" height={SIZE} role="img" aria-label="Radar chart comparing favourite and underdog across grass win %, recent form, Wimbledon win %, hold rate, break rate, and tiebreak %">
        {RING_FRACTIONS.map((fraction) => (
          <polygon
            key={fraction}
            points={ringPoints(fraction)}
            fill="none"
            strokeWidth={1}
            className="stroke-border"
          />
        ))}
        {AXES.map((_, i) => {
          const { x, y } = axisPoint(i, 1);
          return (
            <line
              key={i}
              x1={CENTER}
              y1={CENTER}
              x2={x}
              y2={y}
              strokeWidth={1}
              className="stroke-border"
            />
          );
        })}

        <polygon
          points={polygonPoints(favorite)}
          fill="var(--color-court-green)"
          fillOpacity={0.18}
          stroke="var(--color-court-green)"
          strokeWidth={2}
        />
        <polygon
          points={polygonPoints(underdog)}
          fill="var(--color-court-purple)"
          fillOpacity={0.18}
          stroke="var(--color-court-purple)"
          strokeWidth={2}
        />

        {AXES.map((axis, i) => {
          const { x, y, anchor } = labelPosition(i);
          return (
            <text
              key={axis.key}
              x={x}
              y={y}
              fontSize={11}
              textAnchor={anchor}
              dominantBaseline="middle"
              className="fill-text-muted font-body"
            >
              {axis.label}
            </text>
          );
        })}
      </svg>
      <div className="flex items-center gap-4 text-xs">
        <span className="flex items-center gap-1.5 font-semibold text-court-green">
          <span className="h-2.5 w-2.5 rounded-full bg-court-green" /> Favourite
        </span>
        <span className="flex items-center gap-1.5 font-semibold text-court-purple">
          <span className="h-2.5 w-2.5 rounded-full bg-court-purple" /> Underdog
        </span>
      </div>
    </div>
  );
}
