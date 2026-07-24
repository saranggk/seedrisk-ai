# SeedRisk AI

A Wimbledon-focused **upset predictor and match analyst**.

Given a tennis match between a favourite and an underdog, SeedRisk AI:

1. Calculates an **upset probability** and **risk label** using a stats-driven rule-based scoring model.
2. Backs every probability with the model's **real historical calibration** — how often the favourite actually won, in matches the model was this confident about — instead of a bare, unverified percentage.
3. Passes the numbers to Claude (via the Anthropic API), whose only job is to **explain the result in plain English** — it never invents stats and never makes the prediction itself.

---

## What it does

The dashboard shows all matches in the dataset as cards with risk badges (Low / Medium / High / Trap Match), a zero-anchored engine-eval bar, a calibration-aware confidence caption, and a summary strip. Matches can be filtered by risk label, sorted by upset probability, and searched by player name. A "Pick Mode" lets you call Favourite or Upset on each match and get a Claude-written grade of your slate. Each match card links to a detail page with:

- Full prediction summary with favourite win probability and upset probability, shown as one continuous engine-eval bar
- A calibration caption — a "Likely / Toss-up / Underdog Alert" bucket, backed by the model's real observed accuracy at that confidence level wherever there's enough historical data to say so
- Player-vs-player comparison: a radar chart for the six percentage-based stats (grass win %, recent form, Wimbledon history, serve/return rates, tiebreak %), plus ranking/seed/last-10/head-to-head as text
- Complete model breakdown — every factor shown with signed impact and a bar scaled to that factor's own fixed ceiling, so the same factor reads at the same visual scale across every match
- On-demand Claude analyst report explaining the model's output in plain English

A sun/moon toggle in the corner switches between a light "cream" theme and a dark "Night Session" theme (auto-detected from your OS preference by default, overridable and persisted).

---

## How the model works

The upset model (`backend/app/services/upset_model.py`) scores each match using a fixed set of weighted features: ranking gap, surface-specific win rates, recent form, Wimbledon-specific history, grass serve/return rates, tiebreak performance, and head-to-head record. Each feature contributes a signed impact to the final upset probability:

- **Positive impact** → pushes upset probability up (helps the underdog)
- **Negative impact** → pulls upset probability down (protects the favourite)

Every feature also carries `max_impact` — its fixed ceiling, regardless of the actual stat difference — so the frontend can render each factor's bar against a stable per-factor scale instead of whatever the largest impact happens to be in one match's list.

Risk labels are assigned by probability threshold:

| Risk label | Upset probability | Meaning                                         |
| ---------- | ----------------- | ----------------------------------------------- |
| Low        | < 20%             | Favourite heavily expected to win               |
| Medium     | 20–34%            | Meaningful upset risk, favourite still expected |
| High       | ≥ 35%              | Significant risk — could go either way          |
| Trap Match | ≥ 30% AND ranking gap ≥ 40 | Favourite looks safe by ranking but stats show meaningful upset risk |

**"Trap Match"** is a narrative override, not a higher probability bucket. It fires when the ranking gap is ≥ 40 positions (the favourite looks commanding on paper) but upset probability is still ≥ 30% (the underlying stats say the match is closer than it appears). The favourite is still favoured — but the mismatch between the safe-looking ranking and the elevated stats is what the label is calling out.

No machine learning is used. Every contributing factor traces back to a specific rule in the code.

---

## How the model checks itself: calibration

A batch harness (`backend/scripts/backtest_calibration/`) scores ~723 real historical ATP/WTA Wimbledon matches (2021–2025) against `predict_upset()` and computes a Brier score plus reliability bins — for matches where the model predicted, say, "90–95% favourite," how often did the favourite actually win? The committed result lives at `data/calibration_report.json`.

`GET /calibration` exposes those reliability bins live. The frontend uses them to bucket every prediction into "Likely" / "Toss-up" / "Underdog Alert" (reusing the same risk-label thresholds above) and, where the underlying bin has at least 20 historical matches, states the model's real observed accuracy at that confidence level. Thinner bins show the bucket label alone rather than quoting a rate based on a handful of matches.

This is the one piece of the app backed by real historical outcomes rather than synthetic sample data — see [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) for how the real backtest dataset differs from the synthetic one the live dashboard runs on.

---

## What Claude does (and does not do)

The Claude analyst layer (`POST /matches/{id}/analysis`) receives the match, both players' stats, and the already-computed prediction, then writes a structured explanation in 7 fields:

> Match summary · Why the favourite is favoured · Why an upset could happen · Key stat to watch · Upset recipe · Final analyst take · Confidence note

A second Claude-backed endpoint, `POST /picks/analysis`, grades a user's whole slate of Pick Mode choices (Aggressive / Balanced / Conservative) and writes a portfolio-level summary.

**Claude never computes or changes `favorite_win_probability`, `upset_probability`, `risk_label`, `top_factors`, `slate_grade`, or `expected_correct`** — those are decided before Claude is called. Claude's only job is to turn them into readable prose, grounded strictly in the supplied data. The response schemas don't even include a field where Claude could insert a number of its own.

`ANTHROPIC_API_KEY` is required — the backend refuses to start without it. If a Claude call fails at request time (rate limit, network), both endpoints return a `502` rather than fabricating a report.

---

## Setup

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env and paste your key from https://console.anthropic.com/
uvicorn app.main:app --reload
```

The backend starts at `http://127.0.0.1:8000`. `ANTHROPIC_API_KEY` is required — the server refuses to start without it.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The frontend requires the backend to be running.

---

## ANTHROPIC_API_KEY

Set it in `backend/.env` — required for the backend to start. It powers live Claude analyst reports and picks analysis; there's no mock fallback.

---

## Suggested demo flow

1. Open `http://localhost:3000` — dashboard with all 16 matches and a summary strip
2. Note the summary strip: total matches, High Risk count, Trap Match count, average upset %
3. Use the risk label filter buttons to narrow by Low / Medium / High / Trap Match
4. Try the search bar to find a match by player name, or sort by upset probability
5. Toggle dark mode via the sun/moon icon in the corner
6. Click any match card (M002 is a good example — it has interesting risk dynamics)
7. On the detail page, watch the engine-eval bar rally into place, and read its calibration caption underneath
8. Scroll to **Player comparison** — the radar chart, plus ranking/seed/record/H2H as text
9. Scroll to **Model drivers** — see exactly which stats pushed upset risk up or down, each bar scaled to that factor's own ceiling
10. Click **Generate analyst report** to see Claude's plain-English explanation
11. Back on the dashboard, click **Pick Mode**, make a few picks, then **Analyze My Picks** to see the accessible results modal (Tab stays trapped inside it, Escape closes it)
12. Try visiting `/matches/M999` to see the match-not-found state

---

## Project structure

```
/frontend        Next.js 16 + TypeScript + Tailwind v4 dashboard
/backend         Python FastAPI — match data, rule-based model, calibration, Claude analyst
/data            Sample dataset (16 Wimbledon-style matches) + real backtest/calibration data
/docs            ROADMAP.md, DATA_DICTIONARY.md, METHODOLOGY.md, DECISIONS.md
```

---

## Current limitations

- **Sample data only** — the live dashboard runs on 16 hand-crafted matches, not real ATP/WTA data (calibration is checked against a separate real dataset — see above)
- **No persistence** — data lives in `data/sample_matches.json`; no database
- **Local dev only** — no deployment configuration

---

## Potential future directions

- Real ATP/WTA data ingestion for the live dashboard (not just the offline calibration check)
- Logistic regression or gradient-boosted model (same output interface)
- SQLite or Postgres persistence
- Bracket simulator
- Deployment (Fly.io, Vercel + Railway, etc.)

See [docs/ROADMAP.md](docs/ROADMAP.md) for the phased build history, [docs/METHODOLOGY.md](docs/METHODOLOGY.md) for a full explanation of the model, and [docs/DECISIONS.md](docs/DECISIONS.md) for the architectural decisions behind it.
