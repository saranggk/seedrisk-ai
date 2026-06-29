"use client";

/**
 * Phase 6 — analyst report section on the match detail page.
 *
 * Generation is on-demand (a button), not automatic on page load: each click
 * is a real backend call that may invoke Claude, so we don't want one to fire
 * just from viewing the page. The report is explicitly framed throughout as
 * an explanation of the model's output, not a second opinion or a prediction
 * of its own — see backend/app/services/analyst_generator.py.
 */

import { useCallback, useState } from "react";
import { ApiError, postMatchAnalysis } from "@/lib/api";
import type { AnalystReportResponse } from "@/lib/types";

type State =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; error: ApiError }
  | { status: "ready"; report: AnalystReportResponse };

export function AnalystReportSection({ matchId }: { matchId: string }) {
  const [state, setState] = useState<State>({ status: "idle" });

  const handleGenerate = useCallback(() => {
    setState({ status: "loading" });
    postMatchAnalysis(matchId)
      .then((report) => setState({ status: "ready", report }))
      .catch((error: unknown) => {
        const apiError =
          error instanceof ApiError
            ? error
            : new ApiError("Something unexpected went wrong.", { isNetworkError: false });
        setState({ status: "error", error: apiError });
      });
  }, [matchId]);

  return (
    <section>
      <h2 className="mb-3 text-xs font-medium uppercase tracking-wide text-zinc-500">
        Analyst report
      </h2>

      {state.status === "idle" && (
        <button
          onClick={handleGenerate}
          className="rounded-md bg-court-purple px-4 py-2 text-sm font-medium text-white hover:opacity-90"
        >
          Generate analyst report
        </button>
      )}

      {state.status === "loading" && (
        <div className="flex items-center gap-3 py-6 text-sm text-zinc-500">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-zinc-300 border-t-court-purple" />
          Generating analyst report…
        </div>
      )}

      {state.status === "error" && (
        <div className="flex flex-col gap-3 rounded-xl border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-700">
            Couldn&apos;t generate the analyst report: {state.error.message}
          </p>
          <button
            onClick={handleGenerate}
            className="self-start rounded-md bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800"
          >
            Retry
          </button>
        </div>
      )}

      {state.status === "ready" && (
        <div className="flex flex-col gap-4 rounded-xl border border-zinc-200 bg-white p-5">
          {state.report.source === "mock" && (
            <p className="rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800">
              Demo mode: ANTHROPIC_API_KEY isn&apos;t configured on the backend, so this is a
              deterministic mock report built directly from the model output, not live Claude
              commentary.
            </p>
          )}

          <div>
            <h3 className="text-xs font-medium uppercase tracking-wide text-zinc-400">
              Match summary
            </h3>
            <p className="mt-1 text-sm text-zinc-800">{state.report.match_summary}</p>
          </div>

          <div>
            <h3 className="text-xs font-medium uppercase tracking-wide text-zinc-400">
              Why the favorite is favored
            </h3>
            <p className="mt-1 text-sm text-zinc-800">{state.report.why_favorite_is_favored}</p>
          </div>

          <div>
            <h3 className="text-xs font-medium uppercase tracking-wide text-zinc-400">
              Why the underdog has upset potential
            </h3>
            <p className="mt-1 text-sm text-zinc-800">{state.report.why_upset_could_happen}</p>
          </div>

          <div>
            <h3 className="text-xs font-medium uppercase tracking-wide text-zinc-400">
              Key stat to watch
            </h3>
            <p className="mt-1 text-sm text-zinc-800">{state.report.key_stat_to_watch}</p>
          </div>

          <div>
            <h3 className="text-xs font-medium uppercase tracking-wide text-zinc-400">
              Upset recipe
            </h3>
            <ul className="mt-1 space-y-1 text-sm text-zinc-800">
              {state.report.upset_recipe.map((item) => (
                <li key={item} className="flex gap-2">
                  <span className="text-zinc-400">•</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h3 className="text-xs font-medium uppercase tracking-wide text-zinc-400">
              Final analyst take
            </h3>
            <p className="mt-1 text-sm font-medium text-zinc-900">{state.report.final_take}</p>
          </div>

          <p className="border-t border-zinc-100 pt-3 text-xs text-zinc-500">
            {state.report.confidence_note}
          </p>

          <button
            onClick={handleGenerate}
            className="self-start text-sm font-medium text-court-purple hover:underline"
          >
            Regenerate
          </button>
        </div>
      )}
    </section>
  );
}
