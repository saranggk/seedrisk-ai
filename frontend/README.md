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

- `/` — dashboard: all matches as cards with probability bars, risk badges, and a summary strip. Click any card to open its detail page.
- `/matches/[matchId]` — match detail (e.g. `/matches/M002`): prediction summary, player comparison (favourite left · stat centre · underdog right), full model driver breakdown, and an on-demand Claude analyst report. Invalid IDs (e.g. `/matches/M999`) show a "Match not found" state rather than a generic error.

The analyst report is generated on-demand (button click), not on page load — each click may call Claude. If no `ANTHROPIC_API_KEY` is configured on the backend, the report still renders using a deterministic mock with a "Demo mode" notice.

## Design system

Wimbledon-inspired colour roles (see `app/globals.css`):

| Token | Value | Used for |
|---|---|---|
| `court-green` | `#1b4332` | Favourite strength, headers, structure |
| `court-green-light` | `#2d6a4f` | Hover states, secondary green |
| `court-purple` | `#4c1d6b` | Upset probability, Trap Match, rising-risk bars |
| `court-red` | `#b91c1c` | High risk only |
| `court-amber` | `#92400e` | Medium risk badges |

Background is `#f7f3ec` — a warm cream evoking tournament feel.

## Component overview

```
components/
├── MatchCard.tsx                 Dashboard card — risk-coloured left border, probability bars
├── RiskBadge.tsx                 Outlined pill: Low (green) / Medium (amber) / High (red) / Trap Match (purple)
├── LoadingState.tsx              Spinner with configurable message
├── ErrorState.tsx                Error card with Retry and optional back link
├── MatchNotFound.tsx             Shown on detail page for unknown match IDs
├── PlayerComparisonTable.tsx     Favourite ← stat → underdog three-column layout
├── FeatureContributionList.tsx   Signed-impact bars, purple for upset risk / green for favourite protection
└── AnalystReportSection.tsx      On-demand analyst report, dark green Final Take panel, blush demo notice
lib/
├── types.ts                      TypeScript types mirroring backend/app/models.py
└── api.ts                        API client: getMatches, getMatch, getMatchPrediction, postMatchAnalysis
```
