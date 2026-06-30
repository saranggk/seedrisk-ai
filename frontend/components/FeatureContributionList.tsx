import type { FeatureContribution } from "@/lib/types";

const DIRECTION_STYLES: Record<
  FeatureContribution["direction"],
  { text: string; bar: string; icon: string }
> = {
  increases_upset_risk: { text: "text-court-purple", bar: "bg-court-purple", icon: "▲" },
  decreases_upset_risk: { text: "text-court-green", bar: "bg-court-green", icon: "▼" },
  neutral: { text: "text-zinc-400", bar: "bg-zinc-300", icon: "–" },
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
  const maxAbsImpact = Math.max(...contributions.map((c) => Math.abs(c.impact)), 0.0001);

  return (
    <ul className="flex flex-col divide-y divide-zinc-100 rounded-xl border border-zinc-200">
      {contributions.map((contribution) => {
        const style = DIRECTION_STYLES[contribution.direction];
        const barWidthPct = (Math.abs(contribution.impact) / maxAbsImpact) * 100;

        return (
          <li key={contribution.feature} className="flex flex-col gap-1.5 bg-white p-4">
            <div className="flex items-center justify-between gap-3">
              <span className="font-medium text-zinc-800">{contribution.label}</span>
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
            <p className="text-xs text-zinc-500">{contribution.reason}</p>
          </li>
        );
      })}
    </ul>
  );
}
