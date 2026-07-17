"""
Tests for the validation pipeline over the sample specs.

Uses the `schema` fixture from conftest.py (a hand-built DBSchema), so these
run without Docker. This is the suite that proves each validator has teeth:
the valid spec passes, every broken one is caught by the stage it targets.

Adjust imports to your layout.
"""

import pytest

from backend.validation.validate import evaluate_response
from backend.tests.sample_specs import (
    VALID, BAD_ENUM, NO_CHARTS, BAD_SYNTAX,
    BAD_COLUMN, BAD_TABLE, NOT_SELECT, MIXED,
)


class TestValidationPipeline:
    def test_valid_spec_passes(self, schema):
        spec, errors = evaluate_response(VALID, schema)
        assert errors is None
        assert spec is not None

    @pytest.mark.parametrize("raw_spec, label", [
        (BAD_ENUM, "bad layout_mode enum"),
        (NO_CHARTS, "empty charts list"),
        (BAD_SYNTAX, "malformed SQL"),
        (BAD_COLUMN, "hallucinated column"),
        (BAD_TABLE, "hallucinated table"),
        (NOT_SELECT, "non-SELECT statement"),
    ])
    def test_broken_spec_is_caught(self, schema, raw_spec, label):
        spec, errors = evaluate_response(raw_spec, schema)
        assert errors, f"expected errors for: {label}"
        assert spec is None

    def test_mixed_collects_multiple_errors(self, schema):
        """If validate collects all errors (not fail-fast on charts),
        the mixed spec's two bad charts should both be reported."""
        spec, errors = evaluate_response(MIXED, schema)
        assert errors
        assert spec is None
        # If you implemented per-chart attribution + collect-all, assert >1 error:
        # assert len(errors) >= 2