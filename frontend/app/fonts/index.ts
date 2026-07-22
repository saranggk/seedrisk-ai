import localFont from "next/font/local";

// Self-hosted (not next/font/google) — see layout.tsx for why: fetching from
// Google's CDN on first compile previously hung local dev on a slow/restricted
// network. These are static SIL OFL-licensed files under ./files/, so loading
// them has no network dependency at build or dev time.

// Variable names are suffixed `-raw` and remapped to `--font-display` /
// `--font-body` / `--font-data` in globals.css's @theme block. Naming these
// the same as the Tailwind theme tokens directly would make the theme
// token's `var(--font-display)` reference itself (self-referential custom
// property = invalid value), since both would share one name in scope.

export const displayFont = localFont({
  src: "./files/fraunces-600.woff2",
  weight: "600",
  style: "normal",
  variable: "--font-display-raw",
  display: "swap",
});

export const bodyFont = localFont({
  src: "./files/work-sans-variable.woff2",
  weight: "400 500",
  style: "normal",
  variable: "--font-body-raw",
  display: "swap",
});

export const dataFont = localFont({
  src: "./files/jetbrains-mono-variable.woff2",
  weight: "500 600",
  style: "normal",
  variable: "--font-data-raw",
  display: "swap",
});
