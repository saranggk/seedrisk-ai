import type { Metadata } from "next";
import "./globals.css";
import { bodyFont, dataFont, displayFont } from "./fonts";

// Fonts are self-hosted via next/font/local (see app/fonts/index.ts), not
// next/font/google's Geist fonts — those fetch font files from Google's CDN
// on first compile, which can hang local dev for minutes on a slow or
// restricted network. Self-hosted static files have no such dependency.

export const metadata: Metadata = {
  title: "SeedRisk AI — Wimbledon Upset Intelligence",
  description: "A stats-driven upset predictor and match analyst for Wimbledon-style tennis matches.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`h-full antialiased ${displayFont.variable} ${bodyFont.variable} ${dataFont.variable}`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
