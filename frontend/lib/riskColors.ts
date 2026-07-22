import type { RiskLabel } from "./types";

// Single source for risk-label -> semantic-token Tailwind classes. Components
// compose from these atoms instead of each re-deriving its own Low/Medium/
// High/Trap Match -> color mapping.

export const RISK_BORDER: Record<RiskLabel, string> = {
  Low: "border-risk-low",
  Medium: "border-risk-medium",
  High: "border-risk-high",
  "Trap Match": "border-risk-trap",
};

export const RISK_LEFT_BORDER: Record<RiskLabel, string> = {
  Low: "border-l-risk-low",
  Medium: "border-l-risk-medium",
  High: "border-l-risk-high",
  "Trap Match": "border-l-risk-trap",
};

export const RISK_TEXT: Record<RiskLabel, string> = {
  Low: "text-risk-low",
  Medium: "text-risk-medium",
  High: "text-risk-high",
  "Trap Match": "text-risk-trap",
};

export const RISK_BG_SOLID: Record<RiskLabel, string> = {
  Low: "bg-risk-low",
  Medium: "bg-risk-medium",
  High: "bg-risk-high",
  "Trap Match": "bg-risk-trap",
};

export const RISK_BG_TINT: Record<RiskLabel, string> = {
  Low: "bg-risk-low/10",
  Medium: "bg-risk-medium/10",
  High: "bg-risk-high/10",
  "Trap Match": "bg-risk-trap/10",
};
