import type { Player } from "@/lib/types";

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

const ROWS: { label: string; render: (p: Player) => string }[] = [
  { label: "Ranking", render: (p) => `#${p.ranking}` },
  { label: "Seed", render: (p) => (p.seed != null ? `#${p.seed}` : "Unseeded") },
  { label: "Grass win %", render: (p) => pct(p.grass_win_pct) },
  { label: "Recent form (win %)", render: (p) => pct(p.recent_win_pct) },
  { label: "Wimbledon win %", render: (p) => pct(p.wimbledon_win_pct) },
  { label: "Grass hold rate", render: (p) => pct(p.hold_rate_grass) },
  { label: "Grass break rate", render: (p) => pct(p.break_rate_grass) },
  { label: "Tiebreak win %", render: (p) => pct(p.tiebreak_win_pct) },
  { label: "Last 10 record", render: (p) => p.last_10_record },
  { label: "Head-to-head (vs this opponent)", render: (p) => `${p.h2h_wins}-${p.h2h_losses}` },
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
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-zinc-50 text-left text-xs uppercase tracking-wide text-zinc-500">
            <th className="px-4 py-2 font-medium">Stat</th>
            <th className="px-4 py-2 font-medium text-court-green">{favorite.player_name}</th>
            <th className="px-4 py-2 font-medium text-zinc-900">{underdog.player_name}</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-zinc-100">
          {ROWS.map((row) => (
            <tr key={row.label}>
              <td className="px-4 py-2 text-zinc-500">{row.label}</td>
              <td className="px-4 py-2 font-medium text-zinc-900">{row.render(favorite)}</td>
              <td className="px-4 py-2 font-medium text-zinc-900">{row.render(underdog)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
