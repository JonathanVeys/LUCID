"""
Sample specs for exercising the validation pipeline.

Each entry is a (label, expect_valid, raw_spec) tuple. Loop over them and
confirm the VALID one passes and each BROKEN one is caught by the stage it
targets. This is how you prove the validators actually bite, independent of
how good the model is.

Run something like:

    from db.introspect import load_schema      # adjust import to your layout
    from sqlalchemy import create_engine
    from validation.pipeline import validate    # your validate() function
    from tests.sample_specs import SAMPLES

    engine = create_engine("postgresql+psycopg2://postgres:devpassword@localhost:5544/thesis")
    schema = load_schema(engine)

    for label, expect_valid, raw in SAMPLES:
        spec, errors = validate(raw, schema)
        passed = errors is None
        ok = "OK " if passed == expect_valid else "XX "
        print(f"{ok}{label}: passed={passed}, errors={errors}")
"""

# A minimal valid Vega-Lite block reused across charts (the pipeline currently
# treats vega_lite as an opaque dict, so any object is fine until the JSON-schema
# stage is added).
def _vl(mark, x, y):
    return {
        "$schema": "https://vega.io/schema/vega-lite/v5.json",
        "mark": mark,
        "encoding": {
            "x": {"field": x, "type": "nominal"},
            "y": {"field": y, "type": "quantitative"},
        },
    }


# 1. Fully valid — should PASS every stage.
VALID = {
    "title": "Trafficking Incidents Overview",
    "description": "A focused look at reported incidents by type and region.",
    "layout_mode": "focused",
    "charts": [
        {
            "role": "primary",
            "title": "Incidents by crime type",
            "summary": "Count of incidents grouped by crime type.",
            "sql": "SELECT crime_type, COUNT(*) AS n FROM incidents GROUP BY crime_type",
            "vega_lite": _vl("bar", "crime_type", "n"),
        },
        {
            "role": "supporting",
            "title": "Victims by region",
            "summary": "Total victim count per region.",
            "sql": "SELECT location_region, SUM(victim_count) AS total FROM incidents GROUP BY location_region",
            "vega_lite": _vl("bar", "location_region", "total"),
        },
    ],
}

# 2. Wrapper failure — layout_mode is not in the enum. Caught by validate_vis_spec.
BAD_ENUM = {
    "title": "Bad layout mode",
    "description": "layout_mode is invalid.",
    "layout_mode": "fancy",          # not 'focused' | 'informative'
    "charts": [
        {
            "role": "primary",
            "title": "Incidents by type",
            "summary": "Count by crime type.",
            "sql": "SELECT crime_type, COUNT(*) AS n FROM incidents GROUP BY crime_type",
            "vega_lite": _vl("bar", "crime_type", "n"),
        }
    ],
}

# 3. Wrapper failure — empty charts list. Caught by min_length on charts.
NO_CHARTS = {
    "title": "No charts",
    "description": "Charts array is empty.",
    "layout_mode": "focused",
    "charts": [],
}

# 4. SQL syntax failure — malformed query. Caught by check_sql_syntax.
BAD_SYNTAX = {
    "title": "Broken SQL",
    "description": "The SQL does not parse.",
    "layout_mode": "focused",
    "charts": [
        {
            "role": "primary",
            "title": "Broken query",
            "summary": "Has a syntax error.",
            "sql": "SELECT crime_type COUNT(*) FROM WHERE incidents",   # garbled
            "vega_lite": _vl("bar", "crime_type", "n"),
        }
    ],
}

# 5. SQL semantic failure — column that doesn't exist. Caught by check_sql_semantic.
BAD_COLUMN = {
    "title": "Hallucinated column",
    "description": "References a column not in the schema.",
    "layout_mode": "focused",
    "charts": [
        {
            "role": "primary",
            "title": "Bad column",
            "summary": "Uses a non-existent column.",
            "sql": "SELECT offender_age, COUNT(*) AS n FROM incidents GROUP BY offender_age",  # no such column
            "vega_lite": _vl("bar", "offender_age", "n"),
        }
    ],
}

# 6. SQL semantic failure — table that doesn't exist. Caught by check_sql_semantic.
BAD_TABLE = {
    "title": "Hallucinated table",
    "description": "References a table not in the schema.",
    "layout_mode": "focused",
    "charts": [
        {
            "role": "primary",
            "title": "Bad table",
            "summary": "Queries a non-existent table.",
            "sql": "SELECT crime_type, COUNT(*) AS n FROM crimes GROUP BY crime_type",  # 'crimes' not 'incidents'
            "vega_lite": _vl("bar", "crime_type", "n"),
        }
    ],
}

# 7. Safety failure — not a SELECT. Caught by the SELECT-only check.
NOT_SELECT = {
    "title": "Destructive query",
    "description": "Attempts a non-SELECT statement.",
    "layout_mode": "focused",
    "charts": [
        {
            "role": "primary",
            "title": "Drop table",
            "summary": "Should be rejected outright.",
            "sql": "DROP TABLE incidents",
            "vega_lite": _vl("bar", "crime_type", "n"),
        }
    ],
}

# 8. Mixed — multiple charts, some good some bad. Tests collect-all + attribution.
MIXED = {
    "title": "Mixed validity",
    "description": "One good chart, two broken in different ways.",
    "layout_mode": "informative",
    "charts": [
        {
            "role": "primary",
            "title": "Good chart",
            "summary": "Valid.",
            "sql": "SELECT crime_type, COUNT(*) AS n FROM incidents GROUP BY crime_type",
            "vega_lite": _vl("bar", "crime_type", "n"),
        },
        {
            "role": "supporting",
            "title": "Bad column chart",
            "summary": "Non-existent column.",
            "sql": "SELECT nonexistent FROM incidents",
            "vega_lite": _vl("bar", "nonexistent", "n"),
        },
        {
            "role": "supporting",
            "title": "Syntax error chart",
            "summary": "Does not parse.",
            "sql": "SELECT FROM GROUP incidents",
            "vega_lite": _vl("bar", "x", "y"),
        },
    ],
}


SAMPLES = [
    ("VALID", True, VALID),
    ("BAD_ENUM", False, BAD_ENUM),
    ("NO_CHARTS", False, NO_CHARTS),
    ("BAD_SYNTAX", False, BAD_SYNTAX),
    ("BAD_COLUMN", False, BAD_COLUMN),
    ("BAD_TABLE", False, BAD_TABLE),
    ("NOT_SELECT", False, NOT_SELECT),
    ("MIXED", False, MIXED),
]