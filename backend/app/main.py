"""
SeedRisk AI backend entrypoint.

Run with: uvicorn app.main:app --reload  (from the backend/ directory)
"""

from fastapi import FastAPI

from app.routers import matches

app = FastAPI(
    title="SeedRisk AI API",
    description="Wimbledon-focused upset predictor and match analyst — backend API.",
    version="0.1.0",
)

app.include_router(matches.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Simple liveness check: confirms the server is up and responding."""
    return {"status": "ok"}
