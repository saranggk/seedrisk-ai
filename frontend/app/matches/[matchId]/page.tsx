"use client";

/**
 * Match detail page (Phase 5).
 *
 * Route: /matches/[matchId] — e.g. /matches/M002. The [matchId] folder name
 * is Next.js's dynamic segment syntax: any URL path in that position is
 * captured as a string and made available via the useParams() hook below.
 * Visiting /matches/M002 renders this same component with matchId = "M002";
 * no per-match files or registration needed.
 *
 * Like the dashboard, this is a Client Component so loading/error/not-found
 * states can be hand-managed with actionable copy and a path back to the
 * dashboard, rather than relying on Next's generic error boundary.
 *
 * Data flow: fetch GET /matches/{id} and GET /matches/{id}/prediction in
 * parallel (same separation of concerns as the dashboard — see lib/api.ts).
 * If either 404s, the match doesn't exist and we show MatchNotFound instead
 * of a generic error.
 */

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
    <main className="mx-auto max-w-4xl px-6 py-10">
      <Link href="/" className="text-sm font-medium text-court-purple hover:underline">
        ← Back to dashboard
      </Link>

      <div className="mt-6">
        {state.status === "loading" && <LoadingState />}
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

  return (
    <div className="flex flex-col gap-8">
      {/* Match header */}
      <header className="flex flex-col gap-3 border-b border-zinc-200 pb-6">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wide text-zinc-500">
            {round}
          </span>
          <RiskBadge riskLabel={prediction.risk_label} />
        </div>
        <h1 className="text-2xl font-bold text-zinc-900">
          <span className="text-court-green">{favorite.player_name}</span>
          <span className="px-2 font-normal text-zinc-400">vs</span>
          <span>{underdog.player_name}</span>
        </h1>
        <p className="text-sm text-zinc-500">
          #{favorite.ranking} {favorite.player_name} (favorite) vs #{underdog.ranking}{" "}
          {underdog.player_name} (underdog)
        </p>
      </header>

      {/* Prediction summary */}
      <section>
        <h2 className="mb-3 text-xs font-medium uppercase tracking-wide text-zinc-500">
          Prediction summary
        </h2>
        <div className="grid grid-cols-2 gap-3 rounded-xl bg-zinc-50 p-4 text-center sm:grid-cols-3">
          <div>
            <div className="text-xs text-zinc-500">Favorite win probability</div>
            <div className="text-2xl font-bold text-court-green">
              {formatPct(prediction.favorite_win_probability)}
            </div>
          </div>
          <div>
            <div className="text-xs text-zinc-500">Upset probability</div>
            <div className="text-2xl font-bold text-court-purple">
              {formatPct(prediction.upset_probability)}
            </div>
          </div>
          <div className="col-span-2 flex flex-col items-center justify-center sm:col-span-1">
            <div className="text-xs text-zinc-500">Risk label</div>
            <div className="mt-1">
              <RiskBadge riskLabel={prediction.risk_label} />
            </div>
          </div>
        </div>
      </section>

      {/* Top model factors */}
      <section>
        <h2 className="mb-3 text-xs font-medium uppercase tracking-wide text-zinc-500">
          Top model factors
        </h2>
        <p className="mb-3 text-sm text-zinc-600">
          The largest prediction drivers by absolute impact — not necessarily &quot;reasons
          the underdog could win.&quot; A factor can top this list because it strongly
          protects the favorite, not just because it threatens them.
        </p>
        <ul className="space-y-2 rounded-xl border border-zinc-200 bg-white p-4 text-sm text-zinc-700">
          {prediction.top_factors.map((factor) => (
            <li key={factor} className="flex gap-2">
              <span className="text-zinc-400">•</span>
              <span>{factor}</span>
            </li>
          ))}
        </ul>
      </section>

      {/* Player comparison */}
      <section>
        <h2 className="mb-3 text-xs font-medium uppercase tracking-wide text-zinc-500">
          Player comparison
        </h2>
        <PlayerComparisonTable favorite={favorite} underdog={underdog} />
      </section>

      {/* Feature contributions — full model breakdown */}
      <section>
        <h2 className="mb-3 text-xs font-medium uppercase tracking-wide text-zinc-500">
          Model drivers (feature contributions)
        </h2>
        <p className="mb-3 text-sm text-zinc-600">
          Every factor the rule-based model considered, and exactly how much it nudged the
          upset probability up or down. This is the model &quot;showing its work&quot; — no
          factor here is hidden or unexplained.
        </p>
        <FeatureContributionList contributions={prediction.feature_contributions} />
      </section>

      {/* Claude analyst layer — explains the prediction above, never recomputes it */}
      <AnalystReportSection matchId={match.match_id} />
    </div>
  );
}
