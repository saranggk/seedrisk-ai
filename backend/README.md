# SeedRisk AI — Backend

FastAPI service serving match data. Currently reads directly from
`data/sample_matches.json` — no database yet.

## Setup

```bash
cd backend
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env   # optional — see "Claude analyst layer" below
```

## Run

```bash
uvicorn app.main:app --reload
```

The server starts at `http://127.0.0.1:8000`.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/matches` | List all matches |
| GET | `/matches/{match_id}` | Get one match by ID (404 if not found) |
| GET | `/matches/{match_id}/prediction` | Rule-based upset prediction for one match (404 if not found) |
| POST | `/matches/{match_id}/analysis` | Claude-generated (or mock) analyst report explaining the prediction (404 if not found) |

The prediction response includes `top_factors`: the 3 largest model factors
by absolute impact, not necessarily "reasons the underdog could win" — a
factor can top the list because it strongly *protects* the favorite (e.g. a
big ranking gap), not just because it threatens them.

## Claude analyst layer

`POST /matches/{id}/analysis` runs the rule-based model (same as `/prediction`)
and asks Claude to explain the result in plain English. Claude never computes
or changes `favorite_win_probability`, `upset_probability`, `risk_label`,
`top_factors`, or `feature_contributions` — it only writes prose grounded in
that already-decided output. See `backend/app/services/analyst_generator.py`
for the full prompt and the structured-output schema that constrains it.

**Setting up `ANTHROPIC_API_KEY`:**

```bash
cp .env.example .env
# edit .env and paste your key from https://console.anthropic.com/
```

The backend loads `.env` automatically on startup (via `python-dotenv`) — no
need to `export` it manually. `.env` is gitignored; never commit a real key.

**Model:** defaults to `claude-sonnet-4-6` — a grounded explanation task over
structured data doesn't need Opus-level reasoning. Override it by setting
`ANTHROPIC_MODEL` in `.env`.

**Mock mode:** if `ANTHROPIC_API_KEY` is unset, or the Claude call fails for
any reason (rate limit, network, bad key), the endpoint returns a fully
deterministic report built directly from the same rule-based output — no LLM
call is made, and the response includes `"source": "mock"` so the frontend
can show a "demo mode" note. With a working key, responses include
`"source": "claude"` instead.

**Testing it:**

```bash
curl -X POST http://127.0.0.1:8000/matches/M002/analysis | python3 -m json.tool
curl -i -X POST http://127.0.0.1:8000/matches/M999/analysis   # 404
```

## Interactive docs

FastAPI auto-generates a Swagger UI at `http://127.0.0.1:8000/docs` — useful
for trying endpoints directly in the browser without curl.
