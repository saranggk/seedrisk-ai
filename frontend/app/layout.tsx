import type { Metadata } from "next";
import "./globals.css";

// Using the system font stack (set in globals.css) instead of next/font/google's
// Geist fonts — those fetch font files from Google's CDN on first compile, which
// can hang local dev for minutes on a slow or restricted network. Not worth the
// dependency for this project.

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
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
