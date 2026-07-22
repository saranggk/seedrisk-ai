import type { RiskLabel } from "@/lib/types";
import { RISK_BORDER, RISK_TEXT, RISK_BG_TINT } from "@/lib/riskColors";

const RISK_LABELS: Record<RiskLabel, string> = {
  Low: "Low",
  Medium: "Medium",
  High: "High",
  "Trap Match": "⚠ Trap Match",
};

export function RiskBadge({ riskLabel }: { riskLabel: RiskLabel }) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold ${RISK_BORDER[riskLabel]} ${RISK_TEXT[riskLabel]} ${RISK_BG_TINT[riskLabel]}`}
    >
      {RISK_LABELS[riskLabel]}
    </span>
  );
}
