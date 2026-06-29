import type { FeatureContribution } from "@/lib/types";

/**
 * Visual styling per direction — matches the same semantics as RiskBadge's
 * color logic (green = good for the favorite, red = risk, here applied to
 * an individual stat rather than the overall risk_label).
 */
const DIRECTION_STYLES: Record<FeatureContribution["direction"], { text: string; bar: string; icon: string }> = {
  increases_upset_risk: { text: "text-red-700", bar: "bg-red-500", icon: "▲" },
  decreases_upset_risk: { text: "text-emerald-700", bar: "bg-emerald-500", icon: "▼" },
  neutral: { text: "text-zinc-500", bar: "bg-zinc-300", icon: "●" },
};

function formatImpact(contribution: FeatureContribution): string {
  const pts = contribution.impact * 100;
  if (contribution.direction === "neutral") {
    return "0.0 pts neutral";
  }
  const sign = pts > 0 ? "+" : "";
  return `${sign}${pts.toFixed(1)} pts upset risk`;
}

/**
 * Feature contributions are the backend's rule-based model "showing its
 * work" (see backend/app/services/upset_model.py) — every number here
 * traces back to a specific, documented rule, not a black box. Showing all
 * of them (not just the top 3) is what makes the model auditable: a reader
 * can see exactly which stats pushed the prediction up, which pulled it
 * down, and by how much, rather than just trusting a single probability.
 */
export function FeatureContributionList({
  contributions,
}: {
  contributions: FeatureContribution[];
}) {
  const maxAbsImpact = Math.max(...contributions.map((c) => Math.abs(c.impact)), 0.0001);

  return (
    <ul className="flex flex-col divide-y divide-zinc-100 rounded-xl border border-zinc-200">
      {contributions.map((contribution) => {
        const style = DIRECTION_STYLES[contribution.direction];
        const barWidthPct = (Math.abs(contribution.impact) / maxAbsImpact) * 100;

        return (
          <li key={contribution.feature} className="flex flex-col gap-1.5 p-4">
            <div className="flex items-center justify-between gap-3">
              <span className="font-medium text-zinc-900">{contribution.label}</span>
              <span className={`whitespace-nowrap text-sm font-semibold ${style.text}`}>
                {style.icon} {formatImpact(contribution)}
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-zinc-100">
              <div
                className={`h-full rounded-full ${style.bar}`}
                style={{ width: `${barWidthPct}%` }}
              />
            </div>
            <p className="text-sm text-zinc-600">{contribution.reason}</p>
          </li>
        );
      })}
    </ul>
  );
}
