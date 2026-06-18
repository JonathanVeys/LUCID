"""
Shared pytest fixtures.

The key idea: the validation pipeline takes a DBSchema *object*, so tests build
a fake one matching the incidents table rather than introspecting live Postgres.
This makes the whole validation suite deterministic and Docker-free. Only a
separate, marked integration test needs the real database.

Adjust the imports below to match your actual module paths.
"""

import pytest

# Adjust to your layout, e.g. from schema.introspect import DBSchema, Table, Column
from backend.schema.introspect import DBSchema, Table, Column


@pytest.fixture
def schema() -> DBSchema:
    """A DBSchema mirroring the incidents table — no DB connection required."""
    columns = [
        Column("id", "INTEGER"),
        Column("article_url", "TEXT"),
        Column("article_title", "TEXT"),
        Column("article_domain", "TEXT"),
        Column("reported_date", "DATE"),
        Column("incident_date", "DATE"),
        Column("location_country", "TEXT"),
        Column("location_region", "TEXT"),
        Column("crime_type", "TEXT"),
        Column("victim_count", "INTEGER"),
        Column("victim_nationality", "TEXT"),
        Column("perpetrator_nationality", "TEXT"),
        Column("summary", "TEXT"),
        Column("confidence", "TEXT"),
    ]
    incidents = Table(name="incidents", columns=columns)
    return DBSchema(tables={"incidents": incidents})