import type { RiskLabel } from "@/lib/types";

const RISK_STYLES: Record<RiskLabel, string> = {
  Low: "border-emerald-600 text-emerald-700 bg-emerald-50",
  Medium: "border-amber-500 text-amber-700 bg-amber-50",
  High: "border-court-red text-court-red bg-red-50",
  "Trap Match": "border-court-purple text-court-purple bg-purple-50",
};

const RISK_LABELS: Record<RiskLabel, string> = {
  Low: "Low",
  Medium: "Medium",
  High: "High",
  "Trap Match": "⚠ Trap Match",
};

export function RiskBadge({ riskLabel }: { riskLabel: RiskLabel }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${RISK_STYLES[riskLabel]}`}
    >
      {RISK_LABELS[riskLabel]}
    </span>
  );
}
