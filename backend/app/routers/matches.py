"""
Endpoints for serving match data.

Data flow for every request here:
  data/sample_matches.json
    -> loader.load_matches_raw()      (plain dicts, read from disk)
    -> Match(**match_dict)             (Pydantic validates + types the dict)
    -> FastAPI serializes the model    (back to JSON for the HTTP response)

The JSON file is loaded once, at import time, into MATCHES below — not on
every request. For a small local dataset this is the simplest option; a real
database (SQLite, later) would replace this in-memory list without changing
the endpoints' shape.
"""

from fastapi import APIRouter, HTTPException

from app.data.loader import load_matches_raw
from app.models import AnalystReportResponse, Match, MatchResponse, PicksAnalysisRequest, PicksAnalysisResponse, PredictionResponse
from app.services.analyst_generator import generate_analyst_report
from app.services.picks_analyst import generate_picks_analysis
from app.services.upset_model import predict_upset

router = APIRouter()

# Loaded once at startup. Each dict from the JSON file is validated against
# the Match model here — if the data didn't match the expected shape, this
# would fail loudly at import time instead of silently at request time.
MATCHES: list[Match] = [Match(**match) for match in load_matches_raw()]


def _find_match(match_id: str) -> Match:
    """Shared lookup used by every endpoint keyed on match_id."""
    for match in MATCHES:
        if match.match_id == match_id:
            return match
    raise HTTPException(status_code=404, detail=f"Match '{match_id}' not found")


@router.get("/matches", response_model=list[MatchResponse])
def get_matches() -> list[Match]:
    """Return every match in the local dataset."""
    return MATCHES


@router.get("/matches/{match_id}", response_model=MatchResponse)
def get_match(match_id: str) -> Match:
    """Return a single match by its match_id, or 404 if it doesn't exist."""
    return _find_match(match_id)


@router.get("/matches/{match_id}/prediction", response_model=PredictionResponse)
def get_match_prediction(match_id: str) -> PredictionResponse:
    """
    Run the rule-based upset model (app/services/upset_model.py) on one match
    and return its prediction, or 404 if the match doesn't exist.
    """
    match = _find_match(match_id)
    return predict_upset(match)


@router.post("/matches/{match_id}/analysis", response_model=AnalystReportResponse)
def post_match_analysis(match_id: str) -> AnalystReportResponse:
    """
    Generate an analyst report explaining the rule-based prediction for one
    match, or 404 if the match doesn't exist. Reuses predict_upset() for the
    model output — this endpoint never computes its own probabilities; see
    app/services/analyst_generator.py for how the report is built and why
    Claude can't override the prediction.
    """
    match = _find_match(match_id)
    prediction = predict_upset(match)
    return generate_analyst_report(match, prediction)


@router.post("/picks/analysis", response_model=PicksAnalysisResponse)
def post_picks_analysis(request: PicksAnalysisRequest) -> PicksAnalysisResponse:
    """
    Grade a user's slate of picks against the rule-based model's pre-computed
    predictions. Unknown match IDs are silently skipped; 422 if nothing valid remains.
    See app/services/picks_analyst.py for how grades and prose are generated.
    """
    picks_with_data = []
    for item in request.picks:
        try:
            match = _find_match(item.match_id)
            prediction = predict_upset(match)
            picks_with_data.append((item, match, prediction))
        except HTTPException:
            pass

    if not picks_with_data:
        raise HTTPException(status_code=422, detail="No valid match IDs in picks.")

    return generate_picks_analysis(picks_with_data)
