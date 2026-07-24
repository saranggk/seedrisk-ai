"use client";

import { useCallback, useState } from "react";
import { ApiError, postMatchAnalysis } from "@/lib/api";
import type { AnalystReportResponse } from "@/lib/types";
import { Spinner } from "./Spinner";

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
      <div className="mb-4 flex items-start justify-between gap-4 border-b border-border pb-3">
        <div>
          <h2 className="text-xs font-semibold uppercase tracking-widest text-text-muted">
            Analyst Report
          </h2>
          <p className="mt-0.5 text-xs text-text-muted">
            An AI-written explanation of the model&apos;s output — not an independent prediction.
          </p>
        </div>
        {state.status === "ready" && (
          <button
            onClick={handleGenerate}
            className="shrink-0 text-xs font-medium text-text-muted hover:text-court-purple hover:underline"
          >
            Regenerate
          </button>
        )}
      </div>

      {state.status === "idle" && (
        <button
          onClick={handleGenerate}
          className="rounded-md bg-court-purple px-5 py-2.5 text-sm font-semibold text-on-accent transition-opacity hover:opacity-90"
        >
          Generate analyst report
        </button>
      )}

      {state.status === "loading" && (
        <div className="flex items-center gap-3 rounded-xl border border-border bg-surface-muted px-5 py-6 text-sm text-text-muted">
          <Spinner size="sm" accentColor="court-purple" />
          Generating analyst report…
        </div>
      )}

      {state.status === "error" && (
        <div className="flex flex-col gap-3 rounded-xl border border-danger/30 bg-danger/10 p-5">
          <div>
            <p className="font-medium text-danger">Couldn&apos;t generate the analyst report</p>
            <p className="mt-0.5 text-sm text-danger">{state.error.message}</p>
          </div>
          <button
            onClick={handleGenerate}
            className="self-start rounded-md bg-danger px-4 py-2 text-sm font-medium text-on-accent hover:opacity-90"
          >
            Try again
          </button>
        </div>
      )}

      {state.status === "ready" && (
        <div className="flex flex-col gap-5 rounded-xl border border-border bg-surface p-6 shadow-sm">
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

          <div className="border-b border-border pb-5">
            <h3 className="mb-2 text-xs font-semibold uppercase tracking-widest text-text-muted">
              Upset recipe
            </h3>
            <ul className="space-y-2">
              {state.report.upset_recipe.map((item) => (
                <li key={item} className="flex gap-2.5 text-sm text-text-primary">
                  <span className="mt-0.5 shrink-0 text-court-purple">▸</span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Final Take — dark green panel */}
          <div className="rounded-lg bg-court-green px-5 py-4">
            <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-widest text-on-accent/70">
              Final analyst take
            </h3>
            <p className="text-sm leading-relaxed text-on-accent/90">{state.report.final_take}</p>
          </div>

          {/* Confidence note — muted, italicised */}
          <p className="text-xs leading-relaxed text-text-muted italic">
            {state.report.confidence_note}
          </p>
        </div>
      )}
    </section>
  );
}

function ReportField({ label, body }: { label: string; body: string }) {
  return (
    <div className="border-b border-border pb-5 last:border-0 last:pb-0">
      <h3 className="mb-1.5 text-xs font-semibold uppercase tracking-widest text-text-muted">
        {label}
      </h3>
      <p className="text-sm leading-relaxed text-text-primary">{body}</p>
    </div>
  );
}
