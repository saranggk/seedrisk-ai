"use client";

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

function SummaryStrip({ matches }: { matches: MatchWithPrediction[] }) {
  const total = matches.length;
  const highCount = matches.filter((m) => m.prediction.risk_label === "High").length;
  const trapCount = matches.filter((m) => m.prediction.risk_label === "Trap Match").length;
  const avgUpset = Math.round(
    (matches.reduce((s, m) => s + m.prediction.upset_probability, 0) / total) * 100,
  );

  const stats: { label: string; value: string; accent: string }[] = [
    { label: "Matches", value: String(total), accent: "text-zinc-800" },
    { label: "High Risk", value: String(highCount), accent: "text-court-red" },
    { label: "Trap Matches", value: String(trapCount), accent: "text-court-purple" },
    { label: "Avg Upset", value: `${avgUpset}%`, accent: "text-court-purple" },
  ];

  return (
    <div className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
      {stats.map(({ label, value, accent }) => (
        <div
          key={label}
          className="rounded-lg border border-zinc-200 bg-white px-4 py-3 text-center shadow-sm"
        >
          <div className={`text-2xl font-bold ${accent}`}>{value}</div>
          <div className="mt-0.5 text-xs font-semibold uppercase tracking-widest text-zinc-400">
            {label}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const [state, setState] = useState<LoadState>({ status: "loading" });

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
      {/* Tournament header — dark green banner */}
      <header className="mb-8 overflow-hidden rounded-xl bg-court-green px-8 py-7">
        <p className="text-xs font-semibold uppercase tracking-widest text-emerald-400">
          Wimbledon · Upset Intelligence
        </p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-white">SeedRisk AI</h1>
        <p className="mt-1.5 max-w-xl text-sm leading-relaxed text-emerald-100/80">
          Stats-driven upset risk for Wimbledon matchups. An explainable rule-based model
          surfaces which favourites are most vulnerable — no betting advice, just the data.
        </p>
      </header>

      {state.status === "loading" && (
        <LoadingState message="Loading matches and predictions…" />
      )}
      {state.status === "error" && <ErrorState error={state.error} onRetry={handleRetry} />}
      {state.status === "ready" && (
        <>
          <SummaryStrip matches={state.matches} />
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {state.matches.map(({ match, prediction }) => (
              <MatchCard key={match.match_id} match={match} prediction={prediction} />
            ))}
          </div>
        </>
      )}
    </main>
  );
}
