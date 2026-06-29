import type { RiskLabel } from "@/lib/types";

/**
 * Visual styling for each risk_label value returned by the backend's
 * rule-based model (see backend/app/services/upset_model.py for the
 * thresholds that decide which label a match gets).
 *
 * "Trap Match" gets its own distinct purple treatment rather than reusing
 * the High-risk red — it's a different narrative (a favorite that looks
 * safe on paper but isn't), not just "more risk than High."
 */
const RISK_STYLES: Record<RiskLabel, string> = {
  Low: "bg-emerald-100 text-emerald-800 ring-emerald-600/20",
  Medium: "bg-amber-100 text-amber-800 ring-amber-600/20",
  High: "bg-red-100 text-red-800 ring-red-600/20",
  "Trap Match": "bg-purple-100 text-purple-800 ring-purple-600/20",
};

export function RiskBadge({ riskLabel }: { riskLabel: RiskLabel }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${RISK_STYLES[riskLabel]}`}
    >
      {riskLabel === "Trap Match" ? "⚠ Trap Match" : riskLabel}
    </span>
  );
}
