"""
Endpoint exposing the batch backtest calibration harness's reliability bins
to the live API. See backend/scripts/backtest_calibration/ for how
data/calibration_report.json is generated.
"""

from fastapi import APIRouter

from app.data.loader import load_calibration_report
from app.models import CalibrationResponse

router = APIRouter()

# Loaded once at startup, matching matches.py's module-level MATCHES pattern.
_CALIBRATION_REPORT: dict = load_calibration_report()


@router.get("/calibration", response_model=CalibrationResponse)
def get_calibration() -> CalibrationResponse:
    """
    Return the committed calibration report's overall reliability bins.

    Only reliability_bins is exposed — CalibrationResponse has no other
    fields, so FastAPI's response_model serialization strips brier_score,
    by_tour, by_risk_label, and scored_count from the HTTP response even
    though _CALIBRATION_REPORT itself holds all of them.
    """
    return CalibrationResponse(reliability_bins=_CALIBRATION_REPORT["reliability_bins"])
