import json
from unittest.mock import patch

import pytest

from backend.routers.llm import _generate_validated_spec
from backend.routers.llm import inference as _real_inference


# Patch the name where it is USED: generate_validated_spec lives in
# backend.routers.llm and calls a bare inference(...), so we rebind the
# name in that module's namespace. _real_inference is a separate binding
# in this test module that the patch never touches, so the heal tests can
# still reach the genuine model on later calls.
PATCH_TARGET = "backend.routers.llm.inference"


# ---------------------------------------------------------------------------
# Helper: build a side_effect that returns a fixed first response, then
# delegates every later call to the real model. Used by the integration
# tests to seed a guaranteed failure on attempt 1 and let the model heal.
# ---------------------------------------------------------------------------

def seed_then_real(first_response, counter):
    """Return `first_response` on call 1, then delegate to the real model."""
    def _side_effect(messages):
        counter["n"] += 1
        return first_response if counter["n"] == 1 else _real_inference(messages)
    return _side_effect


# ---------------------------------------------------------------------------
# Fixtures.
#
# inference() returns the raw model TEXT, so each of these is the string a
# model would emit. VALID_CONTENT is a known-good spec; the INVALID/MALFORMED
# ones each break a different branch of evaluate_response.
# ---------------------------------------------------------------------------

VALID_CONTENT = json.dumps({
    "answerable": True,
    "vis_spec": {
        "title": "Trafficking overview: Southeast Asia",
        "description": "A multi-angle view built to explore reported exploitation incidents across the Southeast Asia region.",
        "layout_mode": "informative",
        "charts": [{
            "role": "primary",
            "title": "Incidents by crime type",
            "summary": "Compare the bar heights to see which crime types are most frequently reported in the region.",
            "sql": "SELECT crime_type, COUNT(*) AS incident_count FROM incidents WHERE location_region = 'Southeast Asia' AND crime_type IS NOT NULL GROUP BY crime_type ORDER BY incident_count DESC LIMIT 1000",
            "vega_lite": {
                "$schema": "https://vega-lite.github.io/schema/vega-lite/v5.json",
                "mark": "bar",
                "encoding": {
                    "x": {"field": "crime_type", "type": "nominal", "axis": {"title": "Crime type"}, "sort": "-y"},
                    "y": {"field": "incident_count", "type": "quantitative", "axis": {"title": "Number of incidents"}},
                    "tooltip": [
                        {"field": "crime_type", "type": "nominal"},
                        {"field": "incident_count", "type": "quantitative"}
                    ]
                }
            }
        }]
    }
})

# Valid JSON, but the spec omits the required top-level `description` field,
# so it parses cleanly and then fails validation. Exercises the validate()
# branch of evaluate_response.
INVALID_SPEC_DESCRIPTION = json.dumps({
    "answerable": True,
    "vis_spec": {
        "title": "Trafficking overview: Southeast Asia",
        "layout_mode": "informative",
        "charts": [{
            "role": "primary",
            "title": "Incidents by crime type",
            "summary": "Compare the bar heights to see which crime types are most frequently reported in the region.",
            "sql": "SELECT crime_type, COUNT(*) AS incident_count FROM incidents WHERE location_region = 'Southeast Asia' AND crime_type IS NOT NULL GROUP BY crime_type ORDER BY incident_count DESC LIMIT 1000",
            "vega_lite": {
                "$schema": "https://vega-lite.github.io/schema/vega-lite/v5.json",
                "mark": "bar",
                "encoding": {
                    "x": {"field": "crime_type", "type": "nominal", "axis": {"title": "Crime type"}, "sort": "-y"},
                    "y": {"field": "incident_count", "type": "quantitative", "axis": {"title": "Number of incidents"}},
                    "tooltip": [
                        {"field": "crime_type", "type": "nominal"},
                        {"field": "incident_count", "type": "quantitative"}
                    ]
                }
            }
        }]
    }
})

# Not even valid JSON -- exercises the parse_model_json failure branch.
MALFORMED_JSON_CONTENT = "{ this is not valid json"

UNANSWERABLE_CONTENT = json.dumps({
    "answerable": False,
    "reason": "The dataset does not contain population figures.",
})


# ---------------------------------------------------------------------------
# Integration tests -- these hit the REAL model on the recovery call, so they
# are non-deterministic, slow, and cost a call. They are the empirical
# demonstration that the loop can genuinely repair a broken spec. Run them
# only when you mean to: `pytest -m integration`.
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_heals_from_invalid_spec():
    """Attempt 1 returns a schema-invalid spec (missing `description`);
    the model is then given the validation errors and must produce a valid
    spec. Exercises the validate-failure healing path."""
    calls = {"n": 0}
    with patch(PATCH_TARGET, side_effect=seed_then_real(INVALID_SPEC_DESCRIPTION, calls)):
        result, errors, _ = _generate_validated_spec("a realistic, answerable query")

    assert errors is None, f"model failed to heal an invalid spec; final errors: {errors}"
    # assert result["answerable"] is True
    assert calls["n"] >= 2  # attempt 1 failed (injected), recovery needed a real call


@pytest.mark.integration
def test_heals_from_malformed_json():
    """Attempt 1 returns unparseable text; the model must then produce
    valid, parseable output. Exercises the parse-failure healing path,
    which is a different branch from the invalid-spec case above."""
    calls = {"n": 0}
    with patch(PATCH_TARGET, side_effect=seed_then_real(MALFORMED_JSON_CONTENT, calls)):
        result, errors, _ = _generate_validated_spec("a realistic, answerable query")

    assert errors is None, f"model failed to heal malformed JSON; final errors: {errors}"
    # assert result["answerable"] is True
    assert calls["n"] >= 2  # the parse failure must have triggered a retry


# ---------------------------------------------------------------------------
# Pure-mock tests -- fully deterministic, no model, fast. These guard the
# loop's orchestration and failure contract on every run.
# ---------------------------------------------------------------------------

def test_succeeds_on_first_attempt():
    """A valid spec on the first call should be returned immediately, with
    no retry. The == 1 is the point: it proves the loop doesn't burn an
    extra model call when the first response is already good."""
    with patch(PATCH_TARGET) as mock_inf:
        mock_inf.side_effect = [VALID_CONTENT]
        result, errors, _ = _generate_validated_spec("a realistic, answerable query")

    assert errors is None
    # assert result["answerable"] is True
    assert mock_inf.call_count == 1  # stopped after one call -- no needless retry


def test_exhausts_after_max_retry():
    """Every attempt is invalid; the loop must give up and return the errors
    rather than a spec, stopping at exactly max_retry calls."""
    with patch(PATCH_TARGET) as mock_inf:
        mock_inf.side_effect = [INVALID_SPEC_DESCRIPTION] * 3
        result, errors, _ = _generate_validated_spec("a realistic, answerable query", MAX_RETRY=3)

    assert result is None
    assert errors  # non-empty list of validation errors
    assert mock_inf.call_count == 3


def test_unanswerable_returns_immediately():
    """A genuinely impossible query returns answerable=False on the first
    pass, with no retries and no error state."""
    with patch(PATCH_TARGET) as mock_inf:
        mock_inf.side_effect = [UNANSWERABLE_CONTENT]
        result, errors, _ = _generate_validated_spec("an impossible query")

    assert errors is None
    # assert result["answerable"] is False
    assert mock_inf.call_count == 1