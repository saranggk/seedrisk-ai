"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError, getMatchesWithPredictions, postPicksAnalysis } from "@/lib/api";
import type { MatchWithPrediction, PickChoice, PicksAnalysisResponse, RiskLabel } from "@/lib/types";
import { RISK_BG_SOLID, RISK_BORDER } from "@/lib/riskColors";
import { MatchCard } from "@/components/MatchCard";
import { LoadingState } from "@/components/LoadingState";
import { ErrorState } from "@/components/ErrorState";
import { Modal } from "@/components/Modal";

type LoadState =
  | { status: "loading" }
  | { status: "error"; error: ApiError }
  | { status: "ready"; matches: MatchWithPrediction[] };

type PicksState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "done"; result: PicksAnalysisResponse }
  | { status: "error" };

type SortOrder = "none" | "desc" | "asc";
type FilterValue = "All" | RiskLabel;

const FILTER_OPTIONS: FilterValue[] = ["All", "Low", "Medium", "High", "Trap Match"];

const FILTER_ACTIVE_CLASS: Record<FilterValue, string> = {
  All: "bg-text-primary text-surface border-text-primary",
  Low: `${RISK_BG_SOLID.Low} text-on-accent ${RISK_BORDER.Low}`,
  Medium: `${RISK_BG_SOLID.Medium} text-on-accent ${RISK_BORDER.Medium}`,
  High: `${RISK_BG_SOLID.High} text-on-accent ${RISK_BORDER.High}`,
  "Trap Match": `${RISK_BG_SOLID["Trap Match"]} text-on-accent ${RISK_BORDER["Trap Match"]}`,
};

const INACTIVE_CLASS =
  "bg-surface text-text-muted border-border hover:border-court-green";

const GRADE_CLASS: Record<"Aggressive" | "Balanced" | "Conservative", string> = {
  Aggressive: RISK_BG_SOLID.High,
  Balanced: RISK_BG_SOLID.Medium,
  Conservative: RISK_BG_SOLID.Low,
};

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
    { label: "Matches", value: String(total), accent: "text-text-primary" },
    { label: "High Risk", value: String(highCount), accent: "text-court-red" },
    { label: "Trap Matches", value: String(trapCount), accent: "text-court-purple" },
    { label: "Avg Upset", value: `${avgUpset}%`, accent: "text-court-purple" },
  ];

  return (
    <div className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
      {stats.map(({ label, value, accent }) => (
        <div
          key={label}
          className="rounded-lg border border-border bg-surface px-4 py-3 text-center shadow-sm"
        >
          <div className={`font-data text-2xl font-bold ${accent}`}>{value}</div>
          <div className="mt-0.5 text-xs font-semibold uppercase tracking-widest text-text-muted">
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

  const [pickMode, setPickMode] = useState(false);
  const [picks, setPicks] = useState<Partial<Record<string, PickChoice>>>({});
  const [picksAnalysis, setPicksAnalysis] = useState<PicksState>({ status: "idle" });
  const [showAnalysis, setShowAnalysis] = useState(false);

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

  const handlePick = useCallback((matchId: string, choice: PickChoice) => {
    setPicks((prev) => ({ ...prev, [matchId]: choice }));
  }, []);

  const handleTogglePickMode = useCallback(() => {
    setPickMode((prev) => {
      if (prev) {
        setPicks({});
        setPicksAnalysis({ status: "idle" });
        setShowAnalysis(false);
      }
      return !prev;
    });
  }, []);

  const handleClearPicks = useCallback(() => {
    setPicks({});
    setPicksAnalysis({ status: "idle" });
    setShowAnalysis(false);
  }, []);

  const handleAnalyzePicks = useCallback(async () => {
    setPicksAnalysis({ status: "loading" });
    setShowAnalysis(false);
    try {
      const result = await postPicksAnalysis(picks);
      setPicksAnalysis({ status: "done", result });
      setShowAnalysis(true);
    } catch {
      setPicksAnalysis({ status: "error" });
    }
  }, [picks]);

  const allMatches = state.status === "ready" ? state.matches : [];
  const picksCount = Object.keys(picks).length;

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
    <>
      <main className={`mx-auto max-w-6xl px-6 py-10 ${pickMode ? "pb-28" : ""}`}>
        {/* Tournament header */}
        <header className="mb-8 overflow-hidden rounded-xl bg-court-green px-8 py-7">
          <p className="text-xs font-semibold uppercase tracking-widest text-on-accent/70">
            Wimbledon · Upset Intelligence
          </p>
          <h1 className="mt-2 font-display text-2xl font-bold tracking-tight text-on-accent">SeedRisk AI</h1>
          <p className="mt-1.5 max-w-xl text-sm leading-relaxed text-on-accent/80">
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
              {/* Pick Mode toggle */}
              <button
                onClick={handleTogglePickMode}
                className={`rounded-xl border px-5 py-2.5 text-sm font-bold transition-colors ${
                  pickMode
                    ? "bg-court-purple text-on-accent border-court-purple"
                    : INACTIVE_CLASS
                }`}
              >
                {pickMode ? "Exit Pick Mode" : "Pick Mode"}
              </button>

              {pickMode && (
                <p className="text-sm text-text-muted">
                  Select Favourite or Upset on each card, then analyze your slate.
                </p>
              )}

              <input
                type="text"
                placeholder="Search by player name…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-border bg-surface px-4 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:border-court-green focus:outline-none"
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
                      ? "bg-text-primary text-surface border-text-primary"
                      : INACTIVE_CLASS
                  }`}
                >
                  {sortLabel(sortOrder)}
                </button>
              </div>
              <p className="text-xs text-text-muted">
                {displayed.length === allMatches.length
                  ? `All ${allMatches.length} matches`
                  : `Showing ${displayed.length} of ${allMatches.length} matches`}
              </p>
            </div>

            {/* Match grid */}
            {displayed.length === 0 ? (
              <div className="py-16 text-center text-sm text-text-muted">
                No matches found. Try adjusting your filters or search.
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
                {displayed.map(({ match, prediction }) => (
                  <MatchCard
                    key={match.match_id}
                    match={match}
                    prediction={prediction}
                    pickProps={{
                      pickMode,
                      currentPick: picks[match.match_id] ?? null,
                      onPick: handlePick,
                    }}
                  />
                ))}
              </div>
            )}
          </>
        )}
      </main>

      {/* Sticky bottom bar — only visible in pick mode */}
      {state.status === "ready" && pickMode && (
        <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-border bg-surface/95 px-6 py-4 shadow-lg backdrop-blur-sm">
          <div className="mx-auto flex max-w-6xl items-center justify-between gap-4">
            <div>
              <p className="text-sm font-bold text-text-primary">Pick Mode</p>
              <p className="text-xs text-text-muted" aria-live="polite">
                {picksCount === 0
                  ? "No picks made yet"
                  : `${picksCount} ${picksCount === 1 ? "pick" : "picks"} made`}
              </p>
            </div>
            <div className="flex items-center gap-3">
              {picksCount > 0 && (
                <button
                  onClick={handleClearPicks}
                  className="rounded-lg border border-border px-4 py-2 text-sm font-semibold text-text-muted transition-colors hover:border-court-green"
                >
                  Clear
                </button>
              )}
              {picksAnalysis.status === "error" && (
                <p className="text-xs font-semibold text-danger">Analysis failed</p>
              )}
              <button
                onClick={
                  picksAnalysis.status === "done" && !showAnalysis
                    ? () => setShowAnalysis(true)
                    : handleAnalyzePicks
                }
                disabled={picksCount === 0 || picksAnalysis.status === "loading"}
                className="rounded-lg bg-court-green px-6 py-2.5 text-sm font-bold text-on-accent transition-opacity disabled:opacity-40"
              >
                {picksAnalysis.status === "loading"
                  ? "Analyzing…"
                  : picksAnalysis.status === "done" && !showAnalysis
                  ? "View Results"
                  : "Analyze My Picks"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Analysis results modal */}
      {picksAnalysis.status === "done" && (
        <Modal open={showAnalysis} onClose={() => setShowAnalysis(false)} label="Slate Analysis">
          {/* Modal header */}
          <div className="relative bg-court-purple px-6 py-5">
            <button
              onClick={() => setShowAnalysis(false)}
              aria-label="Close"
              className="absolute right-4 top-4 text-lg font-bold leading-none text-on-accent/60 transition-colors hover:text-on-accent"
            >
              ✕
            </button>
            <p className="text-xs font-semibold uppercase tracking-widest text-on-accent/70">
              Slate Analysis
            </p>
            <div className="mt-2 flex flex-wrap items-center gap-3">
              <span
                className={`rounded-full px-3 py-1 text-sm font-bold text-on-accent ${
                  GRADE_CLASS[picksAnalysis.result.slate_grade]
                }`}
              >
                {picksAnalysis.result.slate_grade}
              </span>
              <span className="text-sm text-on-accent/90">
                {picksAnalysis.result.picks_count}{" "}
                {picksAnalysis.result.picks_count === 1 ? "pick" : "picks"} · Expected
                correct: {picksAnalysis.result.expected_correct.toFixed(1)}
              </span>
            </div>
          </div>

          {/* Modal body */}
          <div className="max-h-[60vh] space-y-5 overflow-y-auto p-6">
            <p className="text-sm leading-relaxed text-text-primary">
              {picksAnalysis.result.slate_summary}
            </p>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="rounded-lg border border-border bg-surface-muted p-4">
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-widest text-text-muted">
                  Boldest Pick
                </p>
                <p className="text-sm text-text-primary">{picksAnalysis.result.boldest_pick}</p>
              </div>
              <div className="rounded-lg border border-border bg-surface-muted p-4">
                <p className="mb-1.5 text-xs font-semibold uppercase tracking-widest text-text-muted">
                  Best Aligned
                </p>
                <p className="text-sm text-text-primary">
                  {picksAnalysis.result.best_aligned_pick}
                </p>
              </div>
            </div>

            <p className="text-xs italic text-text-muted">
              {picksAnalysis.result.portfolio_note}
            </p>
            {picksAnalysis.result.source === "mock" && (
              <p className="text-xs font-semibold text-danger">
                Demo mode — configure ANTHROPIC_API_KEY for live AI analysis
              </p>
            )}
          </div>
        </Modal>
      )}
    </>
  );
}
