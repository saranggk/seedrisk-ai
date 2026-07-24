import type { ReliabilityBin, RiskLabel } from "./types";

// Below this many historical matches, a bin's observed_favorite_win_rate is
// noise, not signal (the committed report's thinnest bins have 0-18 matches;
// its substantial bins have 29+) -- quoting a specific rate from a thin bin
// would present it as real calibration insight when it isn't.
export const MIN_BIN_SAMPLE_SIZE = 20;

// Reuses the model's existing risk_label thresholds rather than a second,
// independent set of cutoffs -- one source of truth for "how confident is this."
const BUCKET_LABEL: Record<RiskLabel, string> = {
  Low: "Likely",
  Medium: "Toss-up",
  High: "Underdog Alert",
  "Trap Match": "Underdog Alert",
};

export function findReliabilityBin(
  favoriteWinProbability: number,
  bins: ReliabilityBin[],
): ReliabilityBin | null {
  if (bins.length === 0) return null;

  for (const bin of bins) {
    if (favoriteWinProbability >= bin.bin_low && favoriteWinProbability < bin.bin_high) {
      return bin;
    }
  }

  // The backend's own bin lookup (_bin_index in metrics.py) treats its final
  // bin as inclusive of the max value; this does the same for a probability
  // at or beyond the last bin's lower edge. Unlike the backend, a probability
  // below the first bin's lower edge still falls through to null here rather
  // than being force-fit into a bin — this data is generated from the same
  // model's own clamp range, so that's not expected to happen in practice.
  const lastBin = bins[bins.length - 1];
  return favoriteWinProbability >= lastBin.bin_low ? lastBin : null;
}

export interface CalibrationSummary {
  label: string;
  observedRate: number | null;
}

export function getCalibrationSummary(
  favoriteWinProbability: number,
  riskLabel: RiskLabel,
  bins: ReliabilityBin[],
): CalibrationSummary {
  const label = BUCKET_LABEL[riskLabel];
  const bin = findReliabilityBin(favoriteWinProbability, bins);

  if (bin === null || bin.count < MIN_BIN_SAMPLE_SIZE || bin.observed_favorite_win_rate === null) {
    return { label, observedRate: null };
  }

  return { label, observedRate: bin.observed_favorite_win_rate };
}
