"""
Schema contract tests for SeedRisk's core architectural guarantee:
Claude (or the mock generator) narrates the model's numbers, but can never
compute or carry one of its own.

WHY THIS EXISTS:
analyst_generator.py and picks_analyst.py's docstrings both assert this in
prose ("the structured output schema below doesn't even give it a field
where a number could go"), but nothing enforced it as code until now.
See docs/DECISIONS.md ADR-2 for the full rationale. This test makes the
guarantee survive a careless field addition or a future Claude model swap
that changes response shape.
"""

from pydantic import BaseModel

from app.models import AnalystReportFields, PicksAnalysisFields

# Field names that would smuggle a model number into a "prose only" schema.
FORBIDDEN_FIELD_NAMES = {
    "favorite_win_probability",
    "upset_probability",
    "risk_label",
    "slate_grade",
    "expected_correct",
}

# The only field types a prose-only explanation schema should ever need.
ALLOWED_FIELD_TYPES = {str, list[str]}


def _assert_prose_only(model: type[BaseModel]) -> None:
    """
    Raises AssertionError if `model` has a field that isn't str/list[str],
    or whose name matches a forbidden probability/label-like name.
    """
    for field_name, field_info in model.model_fields.items():
        assert field_name not in FORBIDDEN_FIELD_NAMES, (
            f"{model.__name__}.{field_name} uses a forbidden field name — "
            f"this schema must never carry a probability or risk label."
        )
        assert field_info.annotation in ALLOWED_FIELD_TYPES, (
            f"{model.__name__}.{field_name} has type {field_info.annotation}, "
            f"but prose-only response schemas may only use str or list[str]."
        )


def test_analyst_report_fields_is_prose_only():
    _assert_prose_only(AnalystReportFields)


def test_picks_analysis_fields_is_prose_only():
    _assert_prose_only(PicksAnalysisFields)


def test_contract_check_actually_catches_a_violation():
    """
    Regression proof: _assert_prose_only isn't a tautology that passes
    anything. A scratch model with a smuggled-in float field must fail it.
    """

    class _ScratchFieldsWithLeakedProbability(BaseModel):
        match_summary: str
        upset_probability: float  # the exact violation this test guards against

    try:
        _assert_prose_only(_ScratchFieldsWithLeakedProbability)
    except AssertionError:
        return  # expected: the helper caught the violation
    raise AssertionError(
        "_assert_prose_only did not catch a field named 'upset_probability' "
        "typed as float — the contract check is not load-bearing."
    )
