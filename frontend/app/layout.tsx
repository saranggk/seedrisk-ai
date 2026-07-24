import type { Metadata } from "next";
import "./globals.css";
import { bodyFont, dataFont, displayFont } from "./fonts";
import { ThemeToggle } from "@/components/ThemeToggle";

// Fonts are self-hosted via next/font/local (see app/fonts/index.ts), not
// next/font/google's Geist fonts — those fetch font files from Google's CDN
// on first compile, which can hang local dev for minutes on a slow or
// restricted network. Self-hosted static files have no such dependency.

export const metadata: Metadata = {
  title: "SeedRisk AI — Wimbledon Upset Intelligence",
  description: "A stats-driven upset predictor and match analyst for Wimbledon-style tennis matches.",
};

// Applies the `dark` class to <html> synchronously, before first paint —
// reads an explicit override first, falls back to the OS preference. Must
// run as a plain inline script (not a module) since it has to execute
// before React hydrates; ThemeToggle re-derives the same rule on mount
// rather than sharing this code, which is an acceptable, unavoidable
// duplication across that boundary.
const THEME_INIT_SCRIPT = `
(function () {
  try {
    var stored = localStorage.getItem("theme");
    var isDark = stored === "dark" || (!stored && window.matchMedia("(prefers-color-scheme: dark)").matches);
    if (isDark) document.documentElement.classList.add("dark");
  } catch (e) {}
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`h-full antialiased ${displayFont.variable} ${bodyFont.variable} ${dataFont.variable}`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col">
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
        <ThemeToggle />
        {children}
      </body>
    </html>
  );
}
