interface EngineEvalBarProps {
  favoriteWinProbability: number;
  upsetProbability: number;
  size?: "compact" | "large";
}

function formatPct(value: number): string {
  return `${Math.round(value * 100)}%`;
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

  return (
    <div
      className={`flex w-full overflow-hidden rounded-lg border border-border ${height}`}
      role="img"
      aria-label={`${formatPct(favoriteWinProbability)} favourite win probability, ${formatPct(upsetProbability)} upset probability`}
    >
      <div
        className={`flex items-center justify-start bg-court-green pl-2.5 font-data font-bold text-on-accent ${textSize}`}
        style={{ width: `${favPct}%` }}
      >
        {favPct > 12 && formatPct(favoriteWinProbability)}
      </div>
      <div
        className={`flex items-center justify-end bg-court-purple pr-2.5 font-data font-bold text-on-accent ${textSize}`}
        style={{ width: `${undPct}%` }}
      >
        {undPct > 12 && formatPct(upsetProbability)}
      </div>
    </div>
  );
}
