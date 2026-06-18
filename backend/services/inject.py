from sqlalchemy import Engine, create_engine
import json

from backend.schema.introspect import load_schema


def inject_data(spec:dict, engine:Engine):
    with engine.connect() as conn:
        for chart in spec["vis_spec"]["charts"]:
            result = conn.exec_driver_sql(str(chart["sql"]))
            rows = [dict(row._mapping) for row in result]
            chart["vega_lite"]["data"] = {"values":rows}
    return spec

# A valid vis_spec for testing inject_data — answerable, one primary + one supporting,
# both querying the real `incidents` schema. Paste/import this as a dict.
# Note: vega_lite["data"] is deliberately ABSENT — inject_data fills it.





if __name__ == "__main__":
    TEST_SPEC = {
        "answerable":"True",
        "vis_spec":{
            "title": "Trafficking incidents in Southeast Asia",
            "description": "Crime type breakdown and reporting timeline for the Southeast Asia region",
            "layout_mode": "informative",
            "charts": [
                {
                    "role": "primary",
                    "title": "Incidents by crime type",
                    "summary": "Count of incidents for each crime type in Southeast Asia.",
                    "sql": (
                        "SELECT crime_type, COUNT(*) AS incident_count "
                        "FROM incidents "
                        "WHERE location_region = 'Southeast Asia' AND crime_type IS NOT NULL "
                        "GROUP BY crime_type ORDER BY incident_count DESC LIMIT 1000"
                    ),
                    "vega_lite": {
                        "$schema": "https://vega-lite.github.io/schema/vega-lite/v5.json",
                        "mark": "bar",
                        "encoding": {
                            "x": {"field": "crime_type", "type": "nominal", "axis": {"title": "Crime type"}, "sort": "-y"},
                            "y": {"field": "incident_count", "type": "quantitative", "axis": {"title": "Number of incidents"}},
                            "tooltip": [
                                {"field": "crime_type", "type": "nominal"},
                                {"field": "incident_count", "type": "quantitative"},
                            ],
                        },
                    },
                },
                {
                    "role": "supporting",
                    "title": "Incidents over time",
                    "summary": "Reported incidents in Southeast Asia by reported date.",
                    "sql": (
                        "SELECT reported_date, COUNT(*) AS incident_count "
                        "FROM incidents "
                        "WHERE location_region = 'Southeast Asia' AND reported_date IS NOT NULL "
                        "GROUP BY reported_date ORDER BY reported_date LIMIT 1000"
                    ),
                    "vega_lite": {
                        "$schema": "https://vega-lite.github.io/schema/vega-lite/v5.json",
                        "mark": "line",
                        "encoding": {
                            "x": {"field": "reported_date", "type": "temporal", "axis": {"title": "Reported date"}},
                            "y": {"field": "incident_count", "type": "quantitative", "axis": {"title": "Number of incidents"}},
                            "tooltip": [
                                {"field": "reported_date", "type": "temporal"},
                                {"field": "incident_count", "type": "quantitative"},
                            ],
                        },
                    },
                },
            ],
        }
    }
    DATABASE_URL = "postgresql+psycopg2://postgres:devpassword@localhost:5544/thesis"
    if DATABASE_URL:
        engine = create_engine("postgresql+psycopg2://postgres:devpassword@localhost:5544/thesis")
        db_schema = load_schema(engine)
    else:
        raise ValueError("Could not build engine")


    spec = inject_data(TEST_SPEC, engine)
    print(json.dumps(spec, indent=2, default=str))