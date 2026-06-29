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
