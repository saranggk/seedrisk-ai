import type { RiskLabel } from "@/lib/types";

const RISK_STYLES: Record<RiskLabel, string> = {
  Low: "border-risk-low text-risk-low bg-risk-low/10",
  Medium: "border-risk-medium text-risk-medium bg-risk-medium/10",
  High: "border-risk-high text-risk-high bg-risk-high/10",
  "Trap Match": "border-risk-trap text-risk-trap bg-risk-trap/10",
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
