import type { FeatureContribution } from "@/lib/types";

const DIRECTION_STYLES: Record<
  FeatureContribution["direction"],
  { text: string; bar: string; icon: string }
> = {
  increases_upset_risk: { text: "text-court-purple", bar: "bg-court-purple", icon: "▲" },
  decreases_upset_risk: { text: "text-court-green", bar: "bg-court-green", icon: "▼" },
  neutral: { text: "text-text-muted", bar: "bg-border", icon: "–" },
};

function formatImpact(contribution: FeatureContribution): string {
  const pts = contribution.impact * 100;
  if (contribution.direction === "neutral") {
    return "0.0 pts neutral";
  }
  const sign = pts > 0 ? "+" : "";
  return `${sign}${pts.toFixed(1)} pts upset risk`;
}

export function FeatureContributionList({
  contributions,
}: {
  contributions: FeatureContribution[];
}) {
  return (
    <ul className="flex flex-col divide-y divide-border rounded-xl border border-border">
      {contributions.map((contribution) => {
        const style = DIRECTION_STYLES[contribution.direction];
        // Scaled against this factor's own fixed cap (max_impact), not the
        // largest impact among the contributions on screen, so the same
        // factor always renders at the same visual scale across matches.
        const barWidthPct = Math.min(
          100,
          (Math.abs(contribution.impact) / contribution.max_impact) * 100
        );

        return (
          <li key={contribution.feature} className="flex flex-col gap-1.5 bg-surface p-4">
            <div className="flex items-center justify-between gap-3">
              <span className="font-medium text-text-primary">{contribution.label}</span>
              <span className={`whitespace-nowrap font-data text-sm font-semibold ${style.text}`}>
                {style.icon} {formatImpact(contribution)}
              </span>
            </div>
            <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface-muted">
              <div
                className={`h-full rounded-full ${style.bar}`}
                style={{ width: `${barWidthPct}%` }}
              />
            </div>
            <p className="text-xs text-text-muted">{contribution.reason}</p>
          </li>
        );
      })}
    </ul>
  );
}
