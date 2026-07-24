import { Fragment } from "react";
import type { Player } from "@/lib/types";
import { PlayerRadarChart } from "./PlayerRadarChart";

const ROWS: { label: string; render: (p: Player) => string }[] = [
  { label: "Ranking", render: (p) => `#${p.ranking}` },
  { label: "Seed", render: (p) => (p.seed != null ? `#${p.seed}` : "Unseeded") },
  { label: "Last 10 record", render: (p) => p.last_10_record },
  { label: "H2H vs opponent", render: (p) => `${p.h2h_wins}–${p.h2h_losses}` },
];

export function PlayerComparisonTable({
  favorite,
  underdog,
}: {
  favorite: Player;
  underdog: Player;
}) {
  return (
    <div className="overflow-hidden rounded-xl border border-border">
      {/* Player name header — grid-cols-3 keeps left/centre/right in equal thirds */}
      <div className="grid grid-cols-3 bg-court-green">
        <div className="px-5 py-3.5">
          <div className="text-xs font-semibold uppercase tracking-widest text-on-accent/70">
            Favourite
          </div>
          <div className="mt-0.5 font-display font-bold text-on-accent">{favorite.player_name}</div>
        </div>
        <div className="flex items-center justify-center">
          <span className="text-xs font-medium text-on-accent/50">vs</span>
        </div>
        <div className="px-5 py-3.5 text-right">
          <div className="text-xs font-semibold uppercase tracking-widest text-on-accent/50">
            Underdog
          </div>
          <div className="mt-0.5 font-display font-bold text-on-accent/80">{underdog.player_name}</div>
        </div>
      </div>

      {/* Percentage stats as a radar chart — mismatches read as polygon
          shape instead of a row-by-row text scan. */}
      <div className="border-b border-border bg-surface">
        <PlayerRadarChart favorite={favorite} underdog={underdog} />
      </div>

      {/* Non-percentage stats — ordinal/text values that don't map cleanly
          onto radar axes, so they stay as a plain comparison grid. */}
      <div className="grid grid-cols-3 text-sm">
        {ROWS.map((row, i) => {
          const isLast = i === ROWS.length - 1;
          const rowBg = i % 2 === 0 ? "bg-surface" : "bg-surface-muted";
          const border = isLast ? "" : "border-b border-border";
          return (
            <Fragment key={row.label}>
              <div className={`px-5 py-2.5 font-data font-semibold text-court-green ${rowBg} ${border}`}>
                {row.render(favorite)}
              </div>
              <div
                className={`px-3 py-2.5 text-center text-xs text-text-muted ${rowBg} ${border}`}
              >
                {row.label}
              </div>
              <div
                className={`px-5 py-2.5 text-right font-data font-semibold text-text-primary ${rowBg} ${border}`}
              >
                {row.render(underdog)}
              </div>
            </Fragment>
          );
        })}
      </div>
    </div>
  );
}
