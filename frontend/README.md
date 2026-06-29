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

## Project structure

```
app/
├── layout.tsx          Root layout, page metadata
├── page.tsx            Dashboard page (client component; fetches + renders matches)
└── globals.css         Tailwind + Wimbledon-inspired theme colors
components/
├── MatchCard.tsx        One match's full card: players, probabilities, top factors
├── RiskBadge.tsx        Color-coded badge for Low/Medium/High/Trap Match
├── LoadingState.tsx      Spinner shown while fetching
└── ErrorState.tsx        Friendly error card with Retry, shown when the backend is unreachable
lib/
├── types.ts             TypeScript types mirroring backend/app/models.py
└── api.ts                API client: getMatches, getMatchPrediction, getMatchesWithPredictions
```
