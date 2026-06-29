"use client";

/**
 * Dashboard page (Phase 4).
 *
 * This is a Client Component ("use client") rather than a Server Component
 * because we want explicit, hand-managed loading/error states with
 * actionable copy (e.g. "start the backend") and a Retry button — a Server
 * Component's fetch failure would just surface as Next.js's generic error
 * boundary, with far less control over the message a local developer sees.
 *
 * Data flow: on mount, fetch all matches, then fetch each match's
 * prediction in parallel (see lib/api.ts for why those are separate
 * requests), then render one MatchCard per match+prediction pair.
 */

import { useCallback, useEffect, useState } from "react";
import { ApiError, getMatchesWithPredictions } from "@/lib/api";
import type { MatchWithPrediction } from "@/lib/types";
import { MatchCard } from "@/components/MatchCard";
import { LoadingState } from "@/components/LoadingState";
import { ErrorState } from "@/components/ErrorState";

type LoadState =
  | { status: "loading" }
  | { status: "error"; error: ApiError }
  | { status: "ready"; matches: MatchWithPrediction[] };

export default function DashboardPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  // Does the fetch and resolves to a final state, but never sets "loading"
  // itself — that's the initial state already, and effects shouldn't set
  // state synchronously on their own (React flags that as a footgun: it
  // causes an extra render pass). Retrying explicitly sets "loading" first,
  // from the button's click handler instead of from inside an effect.
  const fetchDashboardData = useCallback(() => {
    getMatchesWithPredictions()
      .then((matches) => setState({ status: "ready", matches }))
      .catch((error: unknown) => {
        const apiError =
          error instanceof ApiError
            ? error
            : new ApiError("Something unexpected went wrong.", { isNetworkError: false });
        setState({ status: "error", error: apiError });
      });
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const handleRetry = useCallback(() => {
    setState({ status: "loading" });
    fetchDashboardData();
  }, [fetchDashboardData]);

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <header className="mb-8 border-b border-zinc-200 pb-6">
        <p className="text-xs font-semibold uppercase tracking-widest text-court-purple">
          SeedRisk AI
        </p>
        <h1 className="mt-1 text-3xl font-bold text-court-green">
          Wimbledon Upset Intelligence
        </h1>
        <p className="mt-2 max-w-2xl text-sm text-zinc-600">
          A stats-driven look at which favorites are most vulnerable to an upset.
          Predictions come from an explainable rule-based model — no betting
          advice, just the data behind each matchup.
        </p>
      </header>

      {state.status === "loading" && <LoadingState />}
      {state.status === "error" && <ErrorState error={state.error} onRetry={handleRetry} />}
      {state.status === "ready" && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {state.matches.map(({ match, prediction }) => (
            <MatchCard key={match.match_id} match={match} prediction={prediction} />
          ))}
        </div>
      )}
    </main>
  );
}
