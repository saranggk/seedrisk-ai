"use client";

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
      <div className="mb-4 flex items-start justify-between gap-4 border-b border-zinc-200 pb-3">
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-widest text-zinc-400">
            Analyst Report
          </h2>
          <p className="mt-0.5 text-xs text-zinc-500">
            An AI-written explanation of the model&apos;s output — not an independent prediction.
          </p>
        </div>
        {state.status === "ready" && (
          <button
            onClick={handleGenerate}
            className="shrink-0 text-xs font-medium text-zinc-400 hover:text-court-purple hover:underline"
          >
            Regenerate
          </button>
        )}
      </div>

      {state.status === "idle" && (
        <button
          onClick={handleGenerate}
          className="rounded-md bg-court-purple px-5 py-2.5 text-sm font-semibold text-white transition-opacity hover:opacity-90"
        >
          Generate analyst report
        </button>
      )}

      {state.status === "loading" && (
        <div className="flex items-center gap-3 rounded-xl border border-zinc-100 bg-zinc-50 px-5 py-6 text-sm text-zinc-500">
          <div className="h-5 w-5 shrink-0 animate-spin rounded-full border-2 border-zinc-200 border-t-court-purple" />
          Generating analyst report…
        </div>
      )}

      {state.status === "error" && (
        <div className="flex flex-col gap-3 rounded-xl border border-red-200 bg-red-50 p-5">
          <div>
            <p className="font-medium text-red-800">Couldn&apos;t generate the analyst report</p>
            <p className="mt-0.5 text-sm text-red-700">{state.error.message}</p>
          </div>
          <button
            onClick={handleGenerate}
            className="self-start rounded-md bg-red-700 px-4 py-2 text-sm font-medium text-white hover:bg-red-800"
          >
            Try again
          </button>
        </div>
      )}

      {state.status === "ready" && (
        <div className="flex flex-col gap-5 rounded-xl border border-zinc-200 bg-white p-6 shadow-sm">
          {/* Demo mode notice — blush tint, shown when source is mock */}
          {state.report.source === "mock" && (
            <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-xs text-rose-700">
              <span className="font-semibold">Demo mode</span> — ANTHROPIC_API_KEY isn&apos;t
              configured on the backend, so this is a deterministic report built from the model
              output, not live Claude commentary.
            </div>
          )}

          <ReportField label="Match summary" body={state.report.match_summary} />
          <ReportField
            label="Why the favourite is favoured"
            body={state.report.why_favorite_is_favored}
          />
          <ReportField
            label="Why an upset could happen"
            body={state.report.why_upset_could_happen}
          />
          <ReportField label="Key stat to watch" body={state.report.key_stat_to_watch} />

          <div className="border-b border-zinc-100 pb-5">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-widest text-zinc-400">
              Upset recipe
            </h3>
            <ul className="space-y-2">
              {state.report.upset_recipe.map((item) => (
                <li key={item} className="flex gap-2.5 text-sm text-zinc-700">
                  <span className="mt-0.5 shrink-0 text-court-purple">▸</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Final Take — dark green panel */}
          <div className="rounded-lg bg-court-green px-5 py-4">
            <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-widest text-court-green-light">
              Final analyst take
            </h3>
            <p className="text-sm leading-relaxed text-white/90">{state.report.final_take}</p>
          </div>

          {/* Confidence note — muted, italicised */}
          <p className="text-xs leading-relaxed text-zinc-400 italic">
            {state.report.confidence_note}
          </p>
        </div>
      )}
    </section>
  );
}

function ReportField({ label, body }: { label: string; body: string }) {
  return (
    <div className="border-b border-zinc-100 pb-5 last:border-0 last:pb-0">
      <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-widest text-zinc-400">
        {label}
      </h3>
      <p className="text-sm leading-relaxed text-zinc-700">{body}</p>
    </div>
  );
}
