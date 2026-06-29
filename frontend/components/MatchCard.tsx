import Link from "next/link";
import type { MatchWithPrediction } from "@/lib/types";
import { RiskBadge } from "./RiskBadge";

function formatPct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function MatchCard({ match, prediction }: MatchWithPrediction) {
  const { favorite, underdog, round } = match;

  return (
    <Link
      href={`/matches/${match.match_id}`}
      className="flex flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md hover:border-zinc-300"
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wide text-zinc-500">
          {round}
        </span>
        <RiskBadge riskLabel={prediction.risk_label} />
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex items-baseline justify-between">
          <span className="font-semibold text-court-green">{favorite.player_name}</span>
          <span className="text-sm text-zinc-500">#{favorite.ranking} · Favorite</span>
        </div>
        <div className="flex items-baseline justify-between">
          <span className="font-semibold text-zinc-900">{underdog.player_name}</span>
          <span className="text-sm text-zinc-500">#{underdog.ranking} · Underdog</span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 rounded-lg bg-zinc-50 p-3 text-center">
        <div>
          <div className="text-xs text-zinc-500">Favorite win probability</div>
          <div className="text-lg font-bold text-court-green">
            {formatPct(prediction.favorite_win_probability)}
          </div>
        </div>
        <div>
          <div className="text-xs text-zinc-500">Upset probability</div>
          <div className="text-lg font-bold text-court-purple">
            {formatPct(prediction.upset_probability)}
          </div>
        </div>
      </div>

      <div>
        <div className="mb-1.5 text-xs font-medium uppercase tracking-wide text-zinc-500">
          Top model factors
        </div>
        <ul className="space-y-1 text-sm text-zinc-700">
          {prediction.top_factors.map((factor) => (
            <li key={factor} className="flex gap-2">
              <span className="text-zinc-400">•</span>
              <span>{factor}</span>
            </li>
          ))}
        </ul>
      </div>

      <span className="self-end text-sm font-medium text-court-purple">View details →</span>
    </Link>
  );
}
