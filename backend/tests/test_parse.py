"""
Unit tests for pure components (no DB, no model, no network).
These run anywhere, instantly, and are fully deterministic.

Adjust imports to your layout.
"""

from backend.validation.component_validation.parse_json import parse_model_json
# from routers.llm import build_healing_prompt   # or wherever it lives


class TestParseModelJson:
    def test_clean_json(self):
        data, errors = parse_model_json('{"title": "x", "charts": []}')
        assert errors is None
        assert data == {"title": "x", "charts": []}

    def test_fenced_json(self):
        data, errors = parse_model_json('```json\n{"title": "x"}\n```')
        assert errors is None
        assert data == {"title": "x"}

    def test_prose_wrapped(self):
        data, errors = parse_model_json('Here you go:\n{"title": "x"}\nDone!')
        assert errors is None
        assert data == {"title": "x"}

    def test_malformed_returns_errors(self):
        data, errors = parse_model_json('{"title": "x", }')   # trailing comma
        assert data is None
        assert errors  # non-empty list

    def test_no_json_returns_errors(self):
        data, errors = parse_model_json("I cannot help with that.")
        assert data is None
        assert errors

    def test_empty_returns_errors(self):
        data, errors = parse_model_json("   ")
        assert data is None
        assert errors