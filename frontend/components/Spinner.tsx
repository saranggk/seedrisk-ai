interface SpinnerProps {
  size?: "sm" | "lg";
  accentColor?: "court-green" | "court-purple";
}

const SIZE_CLASS: Record<NonNullable<SpinnerProps["size"]>, string> = {
  sm: "h-5 w-5",
  lg: "h-8 w-8",
};

const ACCENT_CLASS: Record<NonNullable<SpinnerProps["accentColor"]>, string> = {
  "court-green": "border-t-court-green",
  "court-purple": "border-t-court-purple",
};

export function Spinner({ size = "lg", accentColor = "court-green" }: SpinnerProps) {
  return (
    <div
      className={`shrink-0 animate-spin rounded-full border-2 border-border ${SIZE_CLASS[size]} ${ACCENT_CLASS[accentColor]}`}
    />
  );
}
