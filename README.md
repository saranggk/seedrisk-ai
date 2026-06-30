# SeedRisk AI

A Wimbledon-focused **upset predictor and match analyst**.

Given a tennis match between a favourite and an underdog, SeedRisk AI:

1. Calculates an **upset probability** and **risk label** using a stats-driven rule-based scoring model.
2. Passes those numbers to Claude (via the Anthropic API), whose only job is to **explain the result in plain English** — it never invents stats and never makes the prediction itself.

---

## What it does

The dashboard shows all matches in the dataset with risk badges (Low / Medium / High / Trap Match), probability bars, and a summary strip. Each match card links to a detail page with:

- Full prediction summary with favourite win probability and upset probability
- Player-vs-player stat comparison (ranking, grass win %, recent form, Wimbledon history, serve/return rates, tiebreak %, last 10 record, head-to-head)
- Complete model breakdown — every factor shown with signed impact (+X / −X pts upset risk) and a proportional bar
- On-demand Claude analyst report explaining the model's output in plain English

---

## How the model works

The upset model (`backend/app/services/upset_model.py`) scores each match using a fixed set of weighted features: ranking gap, surface-specific win rates, recent form, Wimbledon-specific history, grass serve/return rates, tiebreak performance, and head-to-head record. Each feature contributes a signed impact to the final upset probability:

- **Positive impact** → pushes upset probability up (helps the underdog)
- **Negative impact** → pulls upset probability down (protects the favourite)

Risk labels are assigned by probability threshold:

| Risk label | Upset probability | Meaning                                         |
| ---------- | ----------------- | ----------------------------------------------- |
| Low        | < 20%             | Favourite heavily expected to win               |
| Medium     | 20–34%            | Meaningful upset risk, favourite still expected |
| High       | 35–49%            | Significant risk — could go either way          |
| Trap Match | ≥ 50%             | Underdog statistically more likely to win       |

**"Trap Match"** flags a favourite that looks safe on paper but has a statistical vulnerability — the model thinks the supposed underdog is the more likely winner.

No machine learning is used. Every contributing factor traces back to a specific rule in the code.

---

## What Claude does (and does not do)

The Claude analyst layer (`POST /matches/{id}/analysis`) receives the match, both players' stats, and the already-computed prediction, then writes a structured explanation in 7 fields:

> Match summary · Why the favourite is favoured · Why an upset could happen · Key stat to watch · Upset recipe · Final analyst take · Confidence note

**Claude never computes or changes `favorite_win_probability`, `upset_probability`, `risk_label`, or `top_factors`** — those are decided before Claude is called. Claude's only job is to turn them into readable prose, grounded strictly in the supplied data. The response schema doesn't even include a field where Claude could insert a number of its own.

If `ANTHROPIC_API_KEY` is not set, or the call fails, the endpoint falls back to a deterministic mock report built from the same model output — so the app always works.

---

## Setup

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Optional: edit .env and paste your key from https://console.anthropic.com/
uvicorn app.main:app --reload
```

The backend starts at `http://127.0.0.1:8000`. The API key is only needed for live Claude reports — the app works without it.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The frontend requires the backend to be running.

---

## ANTHROPIC_API_KEY

Set it in `backend/.env` to enable live Claude analyst reports. Without it, analyst reports use a deterministic mock and show a "Demo mode" notice. The response field `source` is `"claude"` when live and `"mock"` when using the fallback.

---

## Suggested demo flow

1. Open `http://localhost:3000` — dashboard with all 8 matches and a summary strip
2. Note the summary strip: total matches, High Risk count, Trap Match count, average upset %
3. Click any match card (M002 is a good example — it has interesting risk dynamics)
4. On the detail page, review the probability summary and probability bars
5. Scroll to **Model drivers** — see exactly which stats pushed upset risk up or down
6. Check **Player comparison** — favourite values left, stat labels centre, underdog values right
7. Click **Generate analyst report** to see Claude's plain-English explanation
8. Try visiting `/matches/M999` to see the match-not-found state

---

## Project structure

```
/frontend        Next.js 16 + TypeScript + Tailwind v4 dashboard
/backend         Python FastAPI — match data, rule-based model, Claude analyst
/data            Sample dataset (8 Wimbledon-style matches in JSON)
/docs            ROADMAP.md, DATA_DICTIONARY.md, METHODOLOGY.md
```

---

## Current limitations

- **Sample data only** — 8 hand-crafted matches, not real ATP/WTA data
- **No statistical validation** — model weights are manually tuned, no training or backtesting
- **No persistence** — data lives in `data/sample_matches.json`; no database
- **Local dev only** — no deployment configuration

---

## Potential future directions

- Real ATP/WTA data ingestion via an open tennis API
- Historical accuracy evaluation against real match outcomes
- Logistic regression or gradient-boosted model (same output interface)
- SQLite or Postgres persistence
- Bracket simulator
- Deployment (Fly.io, Vercel + Railway, etc.)

See [docs/ROADMAP.md](docs/ROADMAP.md) for the phased build history and [docs/METHODOLOGY.md](docs/METHODOLOGY.md) for a full explanation of the model.
