import json
from unittest.mock import patch

import pytest

from backend.routers.llm import generate_validated_spec
from backend.routers.llm import inference as _real_inference

# Patch the name where it is USED: generate_validated_spec lives in
# backend.routers.llm and calls a bare inference(...), so we rebind the
# name in that module's namespace. _real_inference is a separate binding
# in this test module that the patch never touches, so the heal tests can
# still reach the genuine model on later calls.
PATCH_TARGET = "backend.routers.llm.inference"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def seed_then_real(first_response, counter):
    """Return `first_response` on call 1, then delegate to the real model."""
    def _side_effect(messages):
        counter["n"] += 1
        return first_response if counter["n"] == 1 else _real_inference(messages)
    return _side_effect


def succeeded(attempts):
    """The loop's success signal: the final attempt record is a success."""
    return bool(attempts) and attempts[-1]["outcome"] == "success"


def failure_types(attempts):
    """Every error_type recorded across failed attempts, in order."""
    return [a["error_type"] for a in attempts if a["outcome"] == "fail"]


# ---------------------------------------------------------------------------
# Fixtures
#
# inference() returns the raw model TEXT, so each of these is the string a
# model would emit. VALID_CONTENT must satisfy the CURRENT schema: object-form
# mark, label_field, and the two interaction params. If the gate tightens
# again, this fixture is the first thing to update.
# ---------------------------------------------------------------------------
_PARAMS = [
    {"name": "select", "select": "point"},
    {"name": "highlight", "select": {"type": "point", "on": "pointerover"}},
]

_ENCODING = {
    "x": {"field": "crime_type", "type": "nominal",
          "axis": {"title": "Crime type"}, "sort": "-y"},
    "y": {"field": "incident_count", "type": "quantitative",
          "axis": {"title": "Number of incidents"}},
    "tooltip": [
        {"field": "crime_type", "type": "nominal"},
        {"field": "incident_count", "type": "quantitative"},
    ],
}

_SQL = (
    "SELECT crime_type, COUNT(*) AS incident_count FROM incidents "
    "WHERE location_region = 'Southeast Asia' AND crime_type IS NOT NULL "
    "GROUP BY crime_type ORDER BY incident_count DESC LIMIT 15"
)


def _chart(**overrides):
    chart = {
        "role": "primary",
        "title": "Incidents by crime type",
        "summary": "Compare the bar heights to see which crime types are most frequently reported.",
        "sql": _SQL,
        "label_field": "crime_type",
        "vega_lite": {
            "$schema": "https://vega-lite.github.io/schema/vega-lite/v5.json",
            "mark": {"type": "bar", "stroke": "black"},
            "params": _PARAMS,
            "encoding": _ENCODING,
        },
    }
    chart.update(overrides)
    return chart


def _spec(**vis_overrides):
    vis = {
        "title": "Trafficking overview: Southeast Asia",
        "description": "A view built to explore reported exploitation incidents in Southeast Asia.",
        "layout_mode": "focused",
        "charts": [_chart()],
    }
    vis.update(vis_overrides)
    return json.dumps({"answerable": True, "vis_spec": vis})


# Known-good: should pass parse -> validate -> inject in one attempt.
VALID_CONTENT = _spec()

# Valid JSON, but omits the required `description`. Parses cleanly, then
# fails the Pydantic gate. Exercises the schema-validation healing path.
INVALID_SPEC_DESCRIPTION = json.dumps({
    "answerable": True,
    "vis_spec": {
        "title": "Trafficking overview: Southeast Asia",
        "layout_mode": "focused",
        "charts": [_chart()],
    },
})

# Valid JSON and valid schema, but the SQL references a column that does not
# exist. Passes the gate, fails semantic SQL validation. This is a DIFFERENT
# branch from the schema failure above and worth covering separately.
INVALID_SQL_COLUMN = _spec(charts=[_chart(
    sql=("SELECT crime_typo, COUNT(*) AS incident_count FROM incidents "
         "GROUP BY crime_typo ORDER BY incident_count DESC"),
    label_field="crime_typo",
)])

# Not even valid JSON -- exercises the parse-failure branch.
MALFORMED_JSON_CONTENT = "{ this is not valid json"

# No JSON object at all -- exercises the no_json_object branch, which is
# distinct from malformed JSON and should produce a different error_type.
PROSE_ONLY_CONTENT = "I'm sorry, I can't help with that request."

UNANSWERABLE_CONTENT = json.dumps({
    "answerable": False,
    "reason": "The dataset does not contain population figures.",
})


# ---------------------------------------------------------------------------
# Pure-mock tests -- deterministic, no model, fast. These guard the loop's
# orchestration and failure contract on every run.
# ---------------------------------------------------------------------------
def test_succeeds_on_first_attempt():
    """A valid spec on the first call is returned immediately, with no retry.
    The == 1 is the point: it proves the loop doesn't burn an extra model
    call when the first response is already good."""
    with patch(PATCH_TARGET) as mock_inf:
        mock_inf.side_effect = [VALID_CONTENT]
        spec, attempts = generate_validated_spec("a realistic, answerable query")

    assert succeeded(attempts), f"expected success, got {attempts}"
    assert spec["answerable"] is True
    assert len(attempts) == 1
    assert mock_inf.call_count == 1


def test_unanswerable_returns_immediately():
    """A genuinely impossible query returns answerable=False on the first
    pass, with no retries. An unanswerable response is a valid terminal
    state, NOT a failure -- injection is skipped entirely."""
    with patch(PATCH_TARGET) as mock_inf:
        mock_inf.side_effect = [UNANSWERABLE_CONTENT]
        spec, attempts = generate_validated_spec("an impossible query")

    assert succeeded(attempts)
    assert spec["answerable"] is False
    assert spec["reason"]
    assert mock_inf.call_count == 1


def test_exhausts_after_max_retry():
    """Every attempt fails; the loop gives up and reports failure rather
    than returning a usable spec. NOTE: MAX_RETRY=3 means range(4), so the
    loop makes 4 calls, not 3."""
    with patch(PATCH_TARGET) as mock_inf:
        mock_inf.side_effect = [INVALID_SPEC_DESCRIPTION] * 4
        spec, attempts = generate_validated_spec("a realistic query", MAX_RETRY=3)

    assert not succeeded(attempts)
    assert spec["answerable"] is False        # exhaustion returns a refusal-shaped dict
    assert len(attempts) == 4
    assert mock_inf.call_count == 4
    assert all(a["outcome"] == "fail" for a in attempts)


def test_records_one_attempt_per_call():
    """The attempts log must have exactly one record per inference call --
    this is the data the benchmark reads, so an off-by-one here silently
    corrupts every convergence metric."""
    with patch(PATCH_TARGET) as mock_inf:
        mock_inf.side_effect = [MALFORMED_JSON_CONTENT] * 4
        _, attempts = generate_validated_spec("a realistic query", MAX_RETRY=3)

    assert len(attempts) == mock_inf.call_count
    assert [a["attempt"] for a in attempts] == list(range(len(attempts)))


def test_failure_branches_produce_distinct_error_types():
    """Parse failure, schema failure and SQL-semantic failure must be
    classified differently. If these collapse to one error_type, the
    benchmark can't distinguish them and healing gets the wrong message."""
    seen = {}
    for name, content in [
        ("malformed_json", MALFORMED_JSON_CONTENT),
        ("no_json_object", PROSE_ONLY_CONTENT),
        ("schema", INVALID_SPEC_DESCRIPTION),
        ("sql_semantic", INVALID_SQL_COLUMN),
    ]:
        with patch(PATCH_TARGET) as mock_inf:
            mock_inf.side_effect = [content] * 4
            _, attempts = generate_validated_spec("a realistic query", MAX_RETRY=3)
        seen[name] = attempts[0]["error_type"]

    assert len(set(seen.values())) == len(seen), (
        f"error types are not distinct across failure branches: {seen}"
    )


def test_healing_prompt_is_appended_between_attempts():
    """Each failed attempt must add the assistant's output and a healing
    message to the conversation, so the model sees what it got wrong."""
    captured = []

    def _capture(messages):
        captured.append(list(messages))
        return MALFORMED_JSON_CONTENT

    with patch(PATCH_TARGET, side_effect=_capture):
        generate_validated_spec("a realistic query", MAX_RETRY=2)

    assert len(captured) >= 2
    # Each successive call must carry strictly more context than the last.
    assert len(captured[1]) > len(captured[0])
    assert captured[1][-1]["role"] == "user"      # healing prompt is last
    assert captured[1][-2]["role"] == "assistant" # preceded by the bad output


# ---------------------------------------------------------------------------
# Integration tests -- these hit the REAL model on the recovery call, so they
# are non-deterministic, slow, and cost a call. They are the empirical
# demonstration that the loop can genuinely repair a broken spec. Run them
# only when you mean to: `pytest -m integration`.
# ---------------------------------------------------------------------------
@pytest.mark.integration
def test_heals_from_invalid_spec():
    """Attempt 1 returns a schema-invalid spec (missing `description`); the
    model is then given the validation errors and must produce a valid spec."""
    calls = {"n": 0}
    with patch(PATCH_TARGET, side_effect=seed_then_real(INVALID_SPEC_DESCRIPTION, calls)):
        spec, attempts = generate_validated_spec("a realistic, answerable query")

    assert succeeded(attempts), f"model failed to heal an invalid spec; attempts: {attempts}"
    assert calls["n"] >= 2


@pytest.mark.integration
def test_heals_from_malformed_json():
    """Attempt 1 returns unparseable text; the model must then produce valid,
    parseable output. A different branch from the invalid-spec case above."""
    calls = {"n": 0}
    with patch(PATCH_TARGET, side_effect=seed_then_real(MALFORMED_JSON_CONTENT, calls)):
        spec, attempts = generate_validated_spec("a realistic, answerable query")

    assert succeeded(attempts), f"model failed to heal malformed JSON; attempts: {attempts}"
    assert calls["n"] >= 2


@pytest.mark.integration
def test_heals_from_bad_sql_column():
    """Attempt 1 returns a schema-valid spec whose SQL references a
    non-existent column. Exercises the semantic-SQL healing path, which is
    the one most likely to loop if the error message is unclear."""
    calls = {"n": 0}
    with patch(PATCH_TARGET, side_effect=seed_then_real(INVALID_SQL_COLUMN, calls)):
        spec, attempts = generate_validated_spec("a realistic, answerable query")

    assert succeeded(attempts), f"model failed to heal a bad column; attempts: {attempts}"
    assert calls["n"] >= 2