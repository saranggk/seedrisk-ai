"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, getMatchesWithPredictions } from "@/lib/api";
import type { MatchWithPrediction, RiskLabel } from "@/lib/types";
import { MatchCard } from "@/components/MatchCard";
import { LoadingState } from "@/components/LoadingState";
import { ErrorState } from "@/components/ErrorState";

type LoadState =
  | { status: "loading" }
  | { status: "error"; error: ApiError }
  | { status: "ready"; matches: MatchWithPrediction[] };

type SortOrder = "none" | "desc" | "asc";
type FilterValue = "All" | RiskLabel;

const FILTER_OPTIONS: FilterValue[] = ["All", "Low", "Medium", "High", "Trap Match"];

const FILTER_ACTIVE_CLASS: Record<FilterValue, string> = {
  All: "bg-zinc-800 text-white border-zinc-800",
  Low: "bg-emerald-600 text-white border-emerald-600",
  Medium: "bg-amber-500 text-white border-amber-500",
  High: "bg-court-red text-white border-court-red",
  "Trap Match": "bg-court-purple text-white border-court-purple",
};

const INACTIVE_CLASS =
  "bg-white text-zinc-600 border-zinc-200 hover:border-zinc-400";

function nextSort(s: SortOrder): SortOrder {
  return s === "none" ? "desc" : s === "desc" ? "asc" : "none";
}

function sortLabel(s: SortOrder): string {
  if (s === "desc") return "Upset % ↓";
  if (s === "asc") return "Upset % ↑";
  return "Sort ↕";
}

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
  const [activeFilter, setActiveFilter] = useState<FilterValue>("All");
  const [sortOrder, setSortOrder] = useState<SortOrder>("none");
  const [searchQuery, setSearchQuery] = useState("");

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

  const allMatches = state.status === "ready" ? state.matches : [];

  let displayed = allMatches;
  if (activeFilter !== "All") {
    displayed = displayed.filter((m) => m.prediction.risk_label === activeFilter);
  }
  if (searchQuery.trim()) {
    const q = searchQuery.trim().toLowerCase();
    displayed = displayed.filter(
      (m) =>
        m.match.favorite.player_name.toLowerCase().includes(q) ||
        m.match.underdog.player_name.toLowerCase().includes(q),
    );
  }
  if (sortOrder !== "none") {
    displayed = [...displayed].sort((a, b) =>
      sortOrder === "desc"
        ? b.prediction.upset_probability - a.prediction.upset_probability
        : a.prediction.upset_probability - b.prediction.upset_probability,
    );
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      {/* Tournament header */}
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

          {/* Controls */}
          <div className="mb-6 space-y-3">
            <input
              type="text"
              placeholder="Search by player name…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-zinc-200 bg-white px-4 py-2.5 text-sm text-zinc-800 placeholder:text-zinc-400 focus:border-zinc-400 focus:outline-none"
            />
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap gap-2">
                {FILTER_OPTIONS.map((label) => (
                  <button
                    key={label}
                    onClick={() => setActiveFilter(label)}
                    className={`rounded-full border px-3 py-1 text-xs font-semibold transition-colors ${
                      activeFilter === label ? FILTER_ACTIVE_CLASS[label] : INACTIVE_CLASS
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
              <button
                onClick={() => setSortOrder(nextSort(sortOrder))}
                className={`rounded-full border px-3 py-1 text-xs font-semibold transition-colors ${
                  sortOrder !== "none"
                    ? "bg-zinc-800 text-white border-zinc-800"
                    : INACTIVE_CLASS
                }`}
              >
                {sortLabel(sortOrder)}
              </button>
            </div>
            <p className="text-xs text-zinc-400">
              {displayed.length === allMatches.length
                ? `All ${allMatches.length} matches`
                : `Showing ${displayed.length} of ${allMatches.length} matches`}
            </p>
          </div>

          {displayed.length === 0 ? (
            <div className="py-16 text-center text-sm text-zinc-400">
              No matches found. Try adjusting your filters or search.
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {displayed.map(({ match, prediction }) => (
                <MatchCard key={match.match_id} match={match} prediction={prediction} />
              ))}
            </div>
          )}
        </>
      )}
    </main>
  );
}
