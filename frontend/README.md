# SeedRisk AI — Frontend

Next.js + TypeScript + Tailwind dashboard for SeedRisk AI. Fetches match
data and rule-based upset predictions from the FastAPI backend — there's no
local data or mock mode here, the backend must be running.

## Setup

```bash
cd frontend
npm install
cp .env.example .env.local   # adjust NEXT_PUBLIC_API_BASE_URL if needed
```

## Run

```bash
npm run dev
```

Open `http://localhost:3000`.

## Running frontend + backend together

The dashboard needs the FastAPI backend running at the URL in
`NEXT_PUBLIC_API_BASE_URL` (defaults to `http://127.0.0.1:8000`). In two
terminals:

```bash
# Terminal 1 — backend
cd backend
uvicorn app.main:app --reload

# Terminal 2 — frontend
cd frontend
npm run dev
```

If the backend isn't running, the dashboard shows an error card with the
exact command to start it, and a Retry button — no need to refresh the page.

## Pages

- `/` — dashboard: all matches as cards, each with prediction summary and top model factors. Click a card (or "View details →") to open its detail page.
- `/matches/[matchId]` — match detail page (e.g. `/matches/M002`): full prediction summary, player-by-player stat comparison, every feature contribution the model considered, and an on-demand Claude analyst report. Visiting an ID that doesn't exist (e.g. `/matches/M999`) shows a "Match not found" state with a link back to the dashboard, rather than a generic error.

The analyst report is generated on click ("Generate analyst report"), not automatically — each click is a real backend call that may invoke Claude. If the backend has no `ANTHROPIC_API_KEY` configured, the report still renders (a deterministic mock), with an amber "Demo mode" notice instead of failing.

## Project structure

```
app/
├── layout.tsx                 Root layout, page metadata
├── page.tsx                   Dashboard page (client component; fetches + renders matches)
├── globals.css                 Tailwind + Wimbledon-inspired theme colors
└── matches/[matchId]/
    └── page.tsx                Match detail page — dynamic route, fetches one match + its prediction
components/
├── MatchCard.tsx                One match's full card; whole card links to its detail page
├── RiskBadge.tsx                Color-coded badge for Low/Medium/High/Trap Match
├── LoadingState.tsx             Spinner shown while fetching
├── ErrorState.tsx               Friendly error card with Retry (and optional "back to dashboard" link)
├── MatchNotFound.tsx            Shown on the detail page when the match ID doesn't exist
├── PlayerComparisonTable.tsx     Favorite vs underdog, stat by stat
├── FeatureContributionList.tsx   Every model factor with signed impact, direction, and a proportional bar
└── AnalystReportSection.tsx      On-demand Claude analyst report, with its own loading/error state and a "Demo mode" notice when source is "mock"
lib/
├── types.ts                    TypeScript types mirroring backend/app/models.py
└── api.ts                       API client: getMatches, getMatch, getMatchPrediction, getMatchesWithPredictions, postMatchAnalysis
```
