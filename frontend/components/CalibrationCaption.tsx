import type { ReliabilityBin, RiskLabel } from "@/lib/types";
import { getCalibrationSummary } from "@/lib/calibration";

export function CalibrationCaption({
  favoriteWinProbability,
  riskLabel,
  bins,
}: {
  favoriteWinProbability: number;
  riskLabel: RiskLabel;
  bins: ReliabilityBin[];
}) {
  const { label, observedRate } = getCalibrationSummary(favoriteWinProbability, riskLabel, bins);

  return (
    <p className="text-xs text-text-muted">
      {label}
      {observedRate !== null && (
        <> · historically right ~{Math.round(observedRate * 100)}% of the time at this confidence level</>
      )}
    </p>
  );
}
