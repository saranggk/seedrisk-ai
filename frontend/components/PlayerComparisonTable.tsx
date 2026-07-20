import { Fragment } from "react";
import type { Player } from "@/lib/types";

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

const ROWS: { label: string; render: (p: Player) => string }[] = [
  { label: "Ranking", render: (p) => `#${p.ranking}` },
  { label: "Seed", render: (p) => (p.seed != null ? `#${p.seed}` : "Unseeded") },
  { label: "Grass win %", render: (p) => pct(p.surface_win_pct) },
  { label: "Recent form", render: (p) => pct(p.recent_win_pct) },
  { label: "Wimbledon win %", render: (p) => pct(p.tournament_win_pct) },
  { label: "Grass hold rate", render: (p) => pct(p.surface_hold_rate) },
  { label: "Grass break rate", render: (p) => pct(p.surface_break_rate) },
  { label: "Tiebreak win %", render: (p) => pct(p.tiebreak_win_pct) },
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
    <div className="overflow-hidden rounded-xl border border-zinc-200">
      {/* Player name header — grid-cols-3 keeps left/centre/right in equal thirds */}
      <div className="grid grid-cols-3 bg-court-green">
        <div className="px-5 py-3.5">
          <div className="text-xs font-semibold uppercase tracking-widest text-emerald-400">
            Favourite
          </div>
          <div className="mt-0.5 font-bold text-white">{favorite.player_name}</div>
        </div>
        <div className="flex items-center justify-center">
          <span className="text-xs font-medium text-emerald-600/60">vs</span>
        </div>
        <div className="px-5 py-3.5 text-right">
          <div className="text-xs font-semibold uppercase tracking-widest text-zinc-400">
            Underdog
          </div>
          <div className="mt-0.5 font-bold text-zinc-100">{underdog.player_name}</div>
        </div>
      </div>

      {/* Stat rows — flat grid-cols-3 so all columns share the same widths.
          Equal thirds guarantee the centre label column is mathematically
          centred regardless of content width on either side. */}
      <div className="grid grid-cols-3 text-sm">
        {ROWS.map((row, i) => {
          const isLast = i === ROWS.length - 1;
          const rowBg = i % 2 === 0 ? "bg-white" : "bg-zinc-50";
          const border = isLast ? "" : "border-b border-zinc-100";
          return (
            <Fragment key={row.label}>
              <div className={`px-5 py-2.5 font-semibold text-court-green ${rowBg} ${border}`}>
                {row.render(favorite)}
              </div>
              <div
                className={`px-3 py-2.5 text-center text-xs text-zinc-400 ${rowBg} ${border}`}
              >
                {row.label}
              </div>
              <div
                className={`px-5 py-2.5 text-right font-semibold text-zinc-700 ${rowBg} ${border}`}
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
