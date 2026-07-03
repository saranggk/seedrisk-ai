/**
 * TypeScript types mirroring the backend's Pydantic models
 * (backend/app/models.py). Keeping the field names identical to the FastAPI
 * response means we can deserialize JSON straight into these types with no
 * mapping layer — if the backend shape ever changes, these types should
 * change to match it field-for-field.
 */

export interface Player {
  player_name: string;
  ranking: number;
  seed: number | null;
  grass_win_pct: number;
  recent_win_pct: number;
  wimbledon_win_pct: number;
  hold_rate_grass: number;
  break_rate_grass: number;
  tiebreak_win_pct: number;
  last_10_record: string;
  h2h_wins: number;
  h2h_losses: number;
}

export interface Match {
  match_id: string;
  round: string;
  favorite: Player;
  underdog: Player;
}

export type FeatureDirection =
  | "increases_upset_risk"
  | "decreases_upset_risk"
  | "neutral";

export interface FeatureContribution {
  feature: string;
  label: string;
  impact: number;
  direction: FeatureDirection;
  reason: string;
}

export type RiskLabel = "Low" | "Medium" | "High" | "Trap Match";

export interface PredictionResponse {
  match_id: string;
  favorite_name: string;
  underdog_name: string;
  favorite_win_probability: number;
  upset_probability: number;
  risk_label: RiskLabel;
  // The 3 largest model factors by absolute impact — not necessarily "top
  // upset reasons." A factor can lead this list because it strongly
  // protects the favorite (e.g. a big ranking gap), not just because it
  // threatens them. See backend/app/models.py for the full explanation.
  top_factors: string[];
  feature_contributions: FeatureContribution[];
}

/** A match paired with its prediction, fetched separately and joined client-side. */
export interface MatchWithPrediction {
  match: Match;
  prediction: PredictionResponse;
}

export type PickChoice = "favorite" | "upset";

/**
 * API response for POST /picks/analysis.
 * slate_grade, picks_count, and expected_correct are pre-computed in Python —
 * Claude only writes the four prose fields (same principle as AnalystReportResponse).
 */
export interface PicksAnalysisResponse {
  slate_grade: "Aggressive" | "Balanced" | "Conservative";
  slate_summary: string;
  boldest_pick: string;
  best_aligned_pick: string;
  portfolio_note: string;
  picks_count: number;
  expected_correct: number;
  source: "claude" | "mock";
}

/**
 * API response for POST /matches/{id}/analysis. These fields are Claude's (or
 * the backend's deterministic mock generator's) explanation of the
 * PredictionResponse above — they never carry probabilities or a risk label
 * of their own and cannot override the model's output.
 */
export interface AnalystReportResponse {
  match_summary: string;
  why_favorite_is_favored: string;
  why_upset_could_happen: string;
  key_stat_to_watch: string;
  upset_recipe: string[];
  final_take: string;
  confidence_note: string;
  // "claude" when ANTHROPIC_API_KEY was set and the call succeeded, "mock" otherwise.
  source: "claude" | "mock";
}
