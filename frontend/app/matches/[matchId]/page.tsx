"use client";

import type { ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ApiError, getMatch, getMatchPrediction } from "@/lib/api";
import type { Match, PredictionResponse } from "@/lib/types";
import { LoadingState } from "@/components/LoadingState";
import { ErrorState } from "@/components/ErrorState";
import { MatchNotFound } from "@/components/MatchNotFound";
import { RiskBadge } from "@/components/RiskBadge";
import { PlayerComparisonTable } from "@/components/PlayerComparisonTable";
import { FeatureContributionList } from "@/components/FeatureContributionList";
import { AnalystReportSection } from "@/components/AnalystReportSection";

type DetailState =
  | { status: "loading" }
  | { status: "not_found" }
  | { status: "error"; error: ApiError }
  | { status: "ready"; match: Match; prediction: PredictionResponse };

function formatPct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export default function MatchDetailPage() {
  const { matchId } = useParams<{ matchId: string }>();
  const [state, setState] = useState<DetailState>({ status: "loading" });

  const fetchDetail = useCallback(() => {
    Promise.all([getMatch(matchId), getMatchPrediction(matchId)])
      .then(([match, prediction]) => setState({ status: "ready", match, prediction }))
      .catch((error: unknown) => {
        if (error instanceof ApiError && error.status === 404) {
          setState({ status: "not_found" });
          return;
        }
        const apiError =
          error instanceof ApiError
            ? error
            : new ApiError("Something unexpected went wrong.", { isNetworkError: false });
        setState({ status: "error", error: apiError });
      });
  }, [matchId]);

  useEffect(() => {
    fetchDetail();
  }, [fetchDetail]);

  const handleRetry = useCallback(() => {
    setState({ status: "loading" });
    fetchDetail();
  }, [fetchDetail]);

  return (
    <main className="mx-auto max-w-4xl px-6 py-8">
      <Link
        href="/"
        className="inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-widest text-zinc-400 hover:text-court-purple"
      >
        ← Dashboard
      </Link>

      <div className="mt-6">
        {state.status === "loading" && <LoadingState message="Loading match details…" />}
        {state.status === "not_found" && <MatchNotFound matchId={matchId} />}
        {state.status === "error" && (
          <ErrorState error={state.error} onRetry={handleRetry} backHref="/" />
        )}
        {state.status === "ready" && (
          <MatchDetail match={state.match} prediction={state.prediction} />
        )}
      </div>
    </main>
  );
}

function MatchDetail({
  match,
  prediction,
}: {
  match: Match;
  prediction: PredictionResponse;
}) {
  const { favorite, underdog, round } = match;
  const favPct = Math.round(prediction.favorite_win_probability * 100);
  const undPct = Math.round(prediction.upset_probability * 100);

  return (
    <div className="flex flex-col gap-10">
      {/* Match header card */}
      <header className="rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between gap-2">
          <span className="text-xs font-semibold uppercase tracking-widest text-zinc-400">
            {round}
          </span>
          <RiskBadge riskLabel={prediction.risk_label} />
        </div>

        <div className="flex flex-col gap-1.5 border-b border-zinc-100 pb-5">
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
            <span className="font-display text-xl font-bold text-court-green">{favorite.player_name}</span>
            <span className="font-data text-sm text-zinc-400">#{favorite.ranking} · Favourite</span>
          </div>
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
            <span className="font-display text-lg font-semibold text-zinc-700">{underdog.player_name}</span>
            <span className="font-data text-sm text-zinc-400">#{underdog.ranking} · Underdog</span>
          </div>
        </div>

        {/* Prediction summary */}
        <div className="mt-5 grid grid-cols-2 gap-6 sm:grid-cols-3">
          <div>
            <div className="mb-1.5 text-xs font-semibold uppercase tracking-widest text-zinc-400">
              Favourite win
            </div>
            <div className="font-data text-3xl font-bold text-court-green">
              {formatPct(prediction.favorite_win_probability)}
            </div>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-zinc-100">
              <div
                className="h-full rounded-full bg-court-green"
                style={{ width: `${favPct}%` }}
              />
            </div>
          </div>
          <div>
            <div className="mb-1.5 text-xs font-semibold uppercase tracking-widest text-zinc-400">
              Upset probability
            </div>
            <div className="font-data text-3xl font-bold text-court-purple">
              {formatPct(prediction.upset_probability)}
            </div>
            <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-zinc-100">
              <div
                className="h-full rounded-full bg-court-purple"
                style={{ width: `${undPct}%` }}
              />
            </div>
          </div>
          <div className="col-span-2 sm:col-span-1">
            <div className="mb-1.5 text-xs font-semibold uppercase tracking-widest text-zinc-400">
              Risk label
            </div>
            <div className="mt-1">
              <RiskBadge riskLabel={prediction.risk_label} />
            </div>
          </div>
        </div>
      </header>

      {/* Top model factors */}
      <Section
        label="Top model factors"
        note="The 3 largest prediction drivers by absolute impact — not necessarily reasons the underdog could win. A factor leads this list because it had the biggest influence, whether it protected the favourite or threatened them."
      >
        <ul className="space-y-2.5 rounded-xl border border-zinc-200 bg-white p-5">
          {prediction.top_factors.map((factor) => (
            <li key={factor} className="flex gap-3 text-sm text-zinc-700">
              <span className="mt-0.5 shrink-0 text-zinc-300">—</span>
              <span>{factor}</span>
            </li>
          ))}
        </ul>
      </Section>

      {/* Player comparison */}
      <Section label="Player comparison">
        <PlayerComparisonTable favorite={favorite} underdog={underdog} />
      </Section>

      {/* Feature contributions — full model breakdown */}
      <Section
        label="Model drivers"
        note="Every factor the model considered, with its signed impact on upset probability. Purple bars increase upset risk; green bars protect the favourite. This is the model showing its work — nothing is hidden."
      >
        <FeatureContributionList contributions={prediction.feature_contributions} />
      </Section>

      {/* Analyst report */}
      <AnalystReportSection matchId={match.match_id} />
    </div>
  );
}

function Section({
  label,
  note,
  children,
}: {
  label: string;
  note?: string;
  children: ReactNode;
}) {
  return (
    <section className="flex flex-col gap-3">
      <div>
        <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-400">{label}</h2>
        {note && <p className="mt-1 text-xs leading-relaxed text-zinc-500">{note}</p>}
      </div>
      <div>{children}</div>
    </section>
  );
}
