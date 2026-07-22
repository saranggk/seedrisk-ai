import Link from "next/link";
import type { MatchWithPrediction, PickChoice, RiskLabel } from "@/lib/types";
import { RiskBadge } from "./RiskBadge";

function formatPct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

const CARD_LEFT_BORDER: Record<RiskLabel, string> = {
  Low: "border-l-risk-low",
  Medium: "border-l-risk-medium",
  High: "border-l-risk-high",
  "Trap Match": "border-l-risk-trap",
};

const CARD_TINT: Record<RiskLabel, string> = {
  Low: "bg-white",
  Medium: "bg-white",
  High: "bg-risk-high/10",
  "Trap Match": "bg-risk-trap/10",
};

interface PickProps {
  pickMode: boolean;
  currentPick: PickChoice | null;
  onPick: (matchId: string, choice: PickChoice) => void;
}

export function MatchCard({
  match,
  prediction,
  pickProps,
}: MatchWithPrediction & { pickProps?: PickProps }) {
  const { favorite, underdog, round } = match;
  const leftBorder = CARD_LEFT_BORDER[prediction.risk_label];
  const tint = CARD_TINT[prediction.risk_label];
  const favPct = Math.round(prediction.favorite_win_probability * 100);
  const undPct = Math.round(prediction.upset_probability * 100);
  const pickMode = pickProps?.pickMode ?? false;
  const currentPick = pickProps?.currentPick ?? null;

  const cardClassName = `flex h-full flex-col gap-4 rounded-xl border border-zinc-200 border-l-4 ${leftBorder} ${tint} p-5 shadow-sm`;

  const cardContent = (
    <>
      {/* Round + risk badge */}
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-widest text-zinc-400">
          {round}
        </span>
        <RiskBadge riskLabel={prediction.risk_label} />
      </div>

      {/* Players */}
      <div className="flex flex-col gap-1.5 border-b border-zinc-100 pb-4">
        <div className="flex items-baseline justify-between gap-2">
          <span className="font-display font-bold text-court-green">{favorite.player_name}</span>
          <span className="shrink-0 font-data text-xs text-zinc-400">#{favorite.ranking} · FAV</span>
        </div>
        <div className="flex items-baseline justify-between gap-2">
          <span className="font-display font-semibold text-zinc-700">{underdog.player_name}</span>
          <span className="shrink-0 font-data text-xs text-zinc-400">#{underdog.ranking} · UND</span>
        </div>
      </div>

      {/* Probability bars */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-zinc-500">Favourite win</span>
          <span className="font-data font-bold text-court-green">{formatPct(prediction.favorite_win_probability)}</span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-zinc-100">
          <div className="h-full rounded-full bg-court-green" style={{ width: `${favPct}%` }} />
        </div>
        <div className="flex items-center justify-between text-xs">
          <span className="text-zinc-500">Upset probability</span>
          <span className="font-data font-bold text-court-purple">{formatPct(prediction.upset_probability)}</span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-zinc-100">
          <div className="h-full rounded-full bg-court-purple" style={{ width: `${undPct}%` }} />
        </div>
      </div>

      {/* Top factors */}
      <div>
        <p className="mb-1.5 text-xs font-semibold uppercase tracking-widest text-zinc-400">
          Key factors
        </p>
        <ul className="space-y-1">
          {prediction.top_factors.map((factor) => (
            <li key={factor} className="flex gap-2 text-xs text-zinc-600">
              <span className="mt-0.5 shrink-0 text-zinc-300">—</span>
              <span>{factor}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Bottom action: pick buttons in pick mode, detail link otherwise */}
      {pickMode ? (
        <div className="mt-auto border-t border-zinc-100 pt-3">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-zinc-400">
            Your pick
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => pickProps?.onPick(match.match_id, "favorite")}
              className={`flex-1 rounded-lg border py-1.5 text-xs font-semibold transition-colors ${
                currentPick === "favorite"
                  ? "bg-court-green text-white border-court-green"
                  : "bg-white text-zinc-600 border-zinc-200 hover:border-zinc-400"
              }`}
            >
              Favourite
            </button>
            <button
              onClick={() => pickProps?.onPick(match.match_id, "upset")}
              className={`flex-1 rounded-lg border py-1.5 text-xs font-semibold transition-colors ${
                currentPick === "upset"
                  ? "bg-court-purple text-white border-court-purple"
                  : "bg-white text-zinc-600 border-zinc-200 hover:border-zinc-400"
              }`}
            >
              Upset
            </button>
          </div>
          {currentPick === "upset" && prediction.risk_label === "Low" && (
            <p className="mt-1.5 text-xs font-semibold text-risk-medium">
              Bold pick — model says Low risk
            </p>
          )}
        </div>
      ) : (
        <div className="mt-auto border-t border-zinc-100 pt-1">
          <span className="text-xs font-semibold uppercase tracking-widest text-court-purple">
            View details →
          </span>
        </div>
      )}
    </>
  );

  if (pickMode) {
    return <div className={cardClassName}>{cardContent}</div>;
  }
  return (
    <Link
      href={`/matches/${match.match_id}`}
      className={`${cardClassName} transition-shadow hover:shadow-md`}
    >
      {cardContent}
    </Link>
  );
}
