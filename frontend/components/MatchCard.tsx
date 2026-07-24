import Link from "next/link";
import type { MatchWithPrediction, PickChoice, RiskLabel } from "@/lib/types";
import { RISK_LEFT_BORDER, RISK_BG_TINT } from "@/lib/riskColors";
import { RiskBadge } from "./RiskBadge";
import { EngineEvalBar } from "./EngineEvalBar";

const CARD_TINT: Record<RiskLabel, string> = {
  Low: "bg-surface",
  Medium: "bg-surface",
  High: RISK_BG_TINT.High,
  "Trap Match": RISK_BG_TINT["Trap Match"],
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
  const leftBorder = RISK_LEFT_BORDER[prediction.risk_label];
  const tint = CARD_TINT[prediction.risk_label];
  const pickMode = pickProps?.pickMode ?? false;
  const currentPick = pickProps?.currentPick ?? null;

  const cardClassName = `flex h-full flex-col gap-4 rounded-xl border border-border border-l-4 ${leftBorder} ${tint} p-5 shadow-sm`;

  const cardContent = (
    <>
      {/* Round + risk badge */}
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs font-semibold uppercase tracking-widest text-text-muted">
          {round}
        </span>
        <RiskBadge riskLabel={prediction.risk_label} />
      </div>

      {/* Players */}
      <div className="flex flex-col gap-1.5 border-b border-border pb-4">
        <div className="flex items-baseline justify-between gap-2">
          <span className="font-display font-bold text-court-green">{favorite.player_name}</span>
          <span className="shrink-0 font-data text-xs text-text-muted">#{favorite.ranking} · FAV</span>
        </div>
        <div className="flex items-baseline justify-between gap-2">
          <span className="font-display font-semibold text-text-primary">{underdog.player_name}</span>
          <span className="shrink-0 font-data text-xs text-text-muted">#{underdog.ranking} · UND</span>
        </div>
      </div>

      {/* Engine-eval bar */}
      <EngineEvalBar
        favoriteWinProbability={prediction.favorite_win_probability}
        upsetProbability={prediction.upset_probability}
      />

      {/* Top factors */}
      <div>
        <p className="mb-1.5 text-xs font-semibold uppercase tracking-widest text-text-muted">
          Key factors
        </p>
        <ul className="space-y-1">
          {prediction.top_factors.map((factor) => (
            <li key={factor} className="flex gap-2 text-xs text-text-muted">
              <span className="mt-0.5 shrink-0 text-text-muted">—</span>
              <span>{factor}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Bottom action: pick buttons in pick mode, detail link otherwise */}
      {pickMode ? (
        <div className="mt-auto border-t border-border pt-3">
          <p className="mb-2 text-xs font-semibold uppercase tracking-widest text-text-muted">
            Your pick
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => pickProps?.onPick(match.match_id, "favorite")}
              className={`flex-1 rounded-lg border py-1.5 text-xs font-semibold transition-colors ${
                currentPick === "favorite"
                  ? "bg-court-green text-on-accent border-court-green"
                  : "bg-surface text-text-muted border-border hover:border-court-green"
              }`}
            >
              Favourite
            </button>
            <button
              onClick={() => pickProps?.onPick(match.match_id, "upset")}
              className={`flex-1 rounded-lg border py-1.5 text-xs font-semibold transition-colors ${
                currentPick === "upset"
                  ? "bg-court-purple text-on-accent border-court-purple"
                  : "bg-surface text-text-muted border-border hover:border-court-green"
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
        <div className="mt-auto border-t border-border pt-1">
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
