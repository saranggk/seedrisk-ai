# SeedRisk AI — Backend

FastAPI service serving match data. Currently reads directly from
`data/sample_matches.json` — no database yet.

## Setup

```bash
cd backend
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
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

## Interactive docs

FastAPI auto-generates a Swagger UI at `http://127.0.0.1:8000/docs` — useful
for trying endpoints directly in the browser without curl.
