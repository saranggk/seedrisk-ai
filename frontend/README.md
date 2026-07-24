# SeedRisk AI — Frontend

Next.js 16 + TypeScript + Tailwind v4 dashboard. Fetches match data and predictions from the FastAPI backend — no local data or mock mode here, the backend must be running.

## Setup

```bash
cd frontend
npm install
cp .env.example .env.local   # adjust NEXT_PUBLIC_API_BASE_URL if needed
npm run dev
```

Open `http://localhost:3000`. Requires the backend at `http://127.0.0.1:8000` (default).

## Running both together

```bash
# Terminal 1 — backend
cd backend && uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend && npm run dev
```

If the backend isn't running, the dashboard shows an actionable error card with the start command and a Retry button.

## Pages

- `/` — dashboard: all matches as cards with an engine-eval bar, calibration caption, risk badge, and a summary strip. Filter by risk label, sort by upset %, search by player name. "Pick Mode" lets you call Favourite/Upset on each card and grade your slate via Claude in an accessible results modal. Click any card (outside Pick Mode) to open its detail page.
- `/matches/[matchId]` — match detail (e.g. `/matches/M002`): prediction summary as one continuous engine-eval bar with a calibration caption, a radar-chart player comparison (favourite vs. underdog across six percentage stats, plus ranking/seed/record/H2H as text), full model driver breakdown, and an on-demand Claude analyst report. Invalid IDs (e.g. `/matches/M999`) show a "Match not found" state rather than a generic error.

The analyst report and picks analysis are both generated on-demand (button click), not on page load — each click may call Claude. If no `ANTHROPIC_API_KEY` is configured on the backend, both fall back to a deterministic mock with a "Demo mode" notice.

## Design system

All color, typography, and motion values are CSS custom properties in `app/globals.css`, re-exposed via Tailwind's `@theme inline` — components reference the generated utility classes (`bg-risk-high`, `text-on-accent`, `font-display`, etc.), never a raw Tailwind color or an ad-hoc hex value. Each token layer has both a light and a dark ("Night Session") value, toggled by a `dark` class on `<html>` (see `components/ThemeToggle.tsx`):

| Layer | Tokens | Used for |
|---|---|---|
| Court palette | `court-green`, `court-green-light`, `court-purple`, `court-red`, `court-amber` | Favourite/underdog identity color, historically Wimbledon-inspired |
| Risk semantics | `risk-low`, `risk-medium`, `risk-high`, `risk-trap` | Risk badges/borders/fills — aliases the court palette so both layers repaint together in dark mode |
| Neutral surface | `surface`, `surface-muted`, `text-primary`, `text-muted`, `border` | Card backgrounds, body text, dividers — replaces raw `zinc-*`/`white`/`black` |
| Accent-contrast | `on-accent` | Text sitting on top of a solid `court-*`/`risk-*` fill (badges, buttons, panels) — kept separate because those tokens flip to *bright* accent values in dark mode |
| Danger/notice | `danger` | Error states and "needs attention" notices (consolidates what were previously separate red/rose palettes) |
| Scrim | `scrim` | Modal backdrop dimming overlay |
| Type roles | `font-display` (Fraunces), `font-body` (Work Sans), `font-data` (JetBrains Mono, tabular figures) | Headings/player names, body copy, and numeric data respectively — self-hosted via `next/font/local`, not `next/font/google` (which can hang local dev fetching from Google's CDN) |
| Motion | `duration-standard`/`ease-standard` (200ms, overrides Tailwind's own transition defaults app-wide), `duration-rally` (320ms, the one signature "rally" overshoot-then-settle animation on `EngineEvalBar`'s mount) | |

## Component overview

```
components/
├── MatchCard.tsx                 Dashboard card — risk-coloured left border, engine-eval bar, calibration caption
├── EngineEvalBar.tsx             One zero-anchored split bar (favourite/upset), rallies into place on mount
├── PlayerRadarChart.tsx          Hand-rolled inline-SVG radar chart, six percentage-based stats
├── PlayerComparisonTable.tsx     Radar chart + favourite ← stat → underdog text rows (ranking/seed/record/H2H)
├── FeatureContributionList.tsx   Signed-impact bars, each scaled to that factor's own fixed max_impact ceiling
├── CalibrationCaption.tsx        "Likely/Toss-up/Underdog Alert" + real observed accuracy where enough data exists
├── RiskBadge.tsx                 Outlined pill: Low (green) / Medium (amber) / High (red) / Trap Match (purple)
├── Modal.tsx                     Reusable accessible dialog primitive — native <dialog>, zero extra dependencies
├── Spinner.tsx                   Shared loading spinner (size + accent color props)
├── ThemeToggle.tsx               Sun/moon dark-mode toggle, persisted override + prefers-color-scheme fallback
├── LoadingState.tsx              Full-page loading state, built on Spinner
├── ErrorState.tsx                Error card with Retry and optional back link
├── MatchNotFound.tsx             Shown on detail page for unknown match IDs
└── AnalystReportSection.tsx      On-demand analyst report, dark green Final Take panel, demo notice
lib/
├── types.ts                      TypeScript types mirroring backend/app/models.py
├── api.ts                        API client: getMatches, getMatch, getMatchPrediction, postMatchAnalysis, postPicksAnalysis, getCalibration
├── riskColors.ts                 Single source for risk-label → token-class mapping (components compose from these, never re-derive)
└── calibration.ts                Bucket-label mapping + reliability-bin lookup for CalibrationCaption
```
