import type { CSSProperties } from "react";

interface EngineEvalBarProps {
  favoriteWinProbability: number;
  upsetProbability: number;
  size?: "compact" | "large";
}

// --rally-target isn't part of the standard CSSProperties type, so this
// narrows just that one extra key rather than casting the whole style
// object away from type-checking.
type RallyStyle = CSSProperties & { "--rally-target": string };

function formatPct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function rallyStyle(pct: number): RallyStyle {
  return { width: `${pct}%`, "--rally-target": `${pct}%` };
}

// One zero-anchored bar split at the favorite/upset boundary. The two sides
// always sum to 100% width since upset_probability = 1 - favorite_win_probability
// in predict_upset() — no separate scaling to reconcile, unlike two
// independently-scaled bars.
export function EngineEvalBar({
  favoriteWinProbability,
  upsetProbability,
  size = "compact",
}: EngineEvalBarProps) {
  const favPct = Math.round(favoriteWinProbability * 100);
  const undPct = 100 - favPct;
  const height = size === "large" ? "h-9" : "h-6";
  const textSize = size === "large" ? "text-sm" : "text-xs";
  const favFits = favPct > 12;
  const undFits = undPct > 12;

  return (
    <div className="flex w-full items-center gap-1.5">
      {!favFits && (
        <span className={`shrink-0 font-data font-bold text-court-green ${textSize}`}>
          {formatPct(favoriteWinProbability)}
        </span>
      )}
      <div
        className={`flex w-full min-w-0 flex-1 overflow-hidden rounded-lg border border-border ${height}`}
        role="img"
        aria-label={`${formatPct(favoriteWinProbability)} favourite win probability, ${formatPct(upsetProbability)} upset probability`}
      >
        <div
          className={`rally-bar flex items-center justify-start bg-court-green pl-2.5 font-data font-bold text-on-accent ${textSize}`}
          style={rallyStyle(favPct)}
        >
          {favFits && formatPct(favoriteWinProbability)}
        </div>
        <div
          className={`rally-bar flex items-center justify-end bg-court-purple pr-2.5 font-data font-bold text-on-accent ${textSize}`}
          style={rallyStyle(undPct)}
        >
          {undFits && formatPct(upsetProbability)}
        </div>
      </div>
      {!undFits && (
        <span className={`shrink-0 font-data font-bold text-court-purple ${textSize}`}>
          {formatPct(upsetProbability)}
        </span>
      )}
    </div>
  );
}
