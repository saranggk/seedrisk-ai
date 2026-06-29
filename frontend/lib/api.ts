/**
 * API client for the SeedRisk AI FastAPI backend.
 *
 * Why predictions are fetched separately from matches:
 * The backend deliberately keeps "what is this match" (GET /matches) and
 * "what does the model think about this match" (GET /matches/{id}/prediction)
 * as two different endpoints (see Phase 3). Match data is static dataset
 * content; a prediction is computed on demand by the scoring model. Keeping
 * them separate means the dashboard can render match cards immediately and
 * fill in predictions as they arrive, and it mirrors what Phase 6 will do
 * for the LLM analyst report (POST /matches/{id}/analysis) — another
 * independently-fetched, derived piece of data for the same match.
 */

import type { Match, MatchWithPrediction, PredictionResponse } from "./types";

// Configurable so the frontend can point at a different backend (e.g. a
// deployed API) without code changes — see .env.example.
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

/**
 * Thrown for any failure talking to the backend — both "the server
 * responded with an error" and "the server couldn't be reached at all."
 * `isNetworkError` lets the UI tell those two cases apart, since "FastAPI
 * isn't running" needs different guidance than "match not found."
 */
export class ApiError extends Error {
  isNetworkError: boolean;
  status?: number;

  constructor(message: string, options: { isNetworkError: boolean; status?: number }) {
    super(message);
    this.name = "ApiError";
    this.isNetworkError = options.isNetworkError;
    this.status = options.status;
  }
}

async function apiFetch<T>(path: string): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`);
  } catch {
    // fetch() rejects (rather than resolving with an error status) when the
    // request never reached a server at all — e.g. FastAPI isn't running,
    // wrong port, or a CORS failure. That's the case the dashboard most
    // needs to explain clearly to a local developer.
    throw new ApiError(
      `Could not reach the SeedRisk API at ${API_BASE_URL}. Is the FastAPI backend running?`,
      { isNetworkError: true },
    );
  }

  if (!response.ok) {
    throw new ApiError(`Request to ${path} failed with status ${response.status}.`, {
      isNetworkError: false,
      status: response.status,
    });
  }

  return (await response.json()) as T;
}

export function getMatches(): Promise<Match[]> {
  return apiFetch<Match[]>("/matches");
}

export function getMatch(matchId: string): Promise<Match> {
  return apiFetch<Match>(`/matches/${matchId}`);
}

export function getMatchPrediction(matchId: string): Promise<PredictionResponse> {
  return apiFetch<PredictionResponse>(`/matches/${matchId}/prediction`);
}

/**
 * Fetches every match, then fetches each match's prediction in parallel,
 * and joins them client-side. This is the single call the dashboard page
 * needs; it exists here (not inline in the page) so the match detail page
 * (Phase 5) can reuse getMatches/getMatchPrediction individually instead.
 */
export async function getMatchesWithPredictions(): Promise<MatchWithPrediction[]> {
  const matches = await getMatches();

  const predictions = await Promise.all(
    matches.map((match) => getMatchPrediction(match.match_id)),
  );

  return matches.map((match, index) => ({
    match,
    prediction: predictions[index],
  }));
}
