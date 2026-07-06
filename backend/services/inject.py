from sqlalchemy import Engine, create_engine
import json

from backend.services.geo_tables import GEO, REGION_TO_IDS


# def inject_data(spec:dict, engine:Engine):
#     with engine.connect() as conn:
#         for chart in spec["vis_spec"]["charts"]:
#             result = conn.exec_driver_sql(str(chart["sql"]))
#             rows = [dict(row._mapping) for row in result]
#             chart["vega_lite"]["data"] = {"values":rows}
#     return spec


def inject_chart(chart:dict, data):
    chart["vega_lite"]["data"] = {"values":data}
    return chart


def inject_choropleth_data(chart, rows, country_key="location_country"):
    vl = chart["vega_lite"]
    granularity = vl.pop("geo_granularity", None)        # strip: not real Vega-Lite
    if granularity not in ("country", "region"):
        raise ValueError(f"geo_granularity must be 'country'/'region', got {granularity!r}")
 
    value_key = next((k for k in rows[0] if k != country_key), None) if rows else None
 
    totals, labels, dropped = {}, {}, {}   # totals keyed by id (country) or region (region)
    for row in rows:
        name = row[country_key]
        v = row[value_key] or 0
        entry = GEO.get(name)
        if entry is None:                  # closed-world assumption broken — log, don't crash
            dropped[name] = dropped.get(name, 0) + v
            continue
        key = entry["id"] if granularity == "country" else entry["region"]
        if key is None:                    # no country shape, or no region
            dropped[name] = dropped.get(name, 0) + v
            continue
        totals[key] = totals.get(key, 0) + v
        if granularity == "country":
            labels.setdefault(key, name)   # first DB spelling seen for this id
 
    if granularity == "country":
        geo_rows = [{"id": cid, "value": v, "label": labels[cid]}
                    for cid, v in totals.items()]
    else:  # region -> broadcast each region's total onto all its member country ids
        geo_rows = [{"id": cid, "value": v, "label": region}
                    for region, v in totals.items()
                    for cid in REGION_TO_IDS[region]]
 
    vl["transform"][0]["from"]["data"]["values"] = geo_rows
    return chart



def inject_data(spec:dict, engine:Engine):
    with engine.connect() as conn:
        for chart in spec["vis_spec"]["charts"]:
            result = conn.exec_driver_sql(str(chart["sql"]))
            rows = [dict(row._mapping) for row in result]

            mark = chart["vega_lite"]["mark"]
            mark_type = mark["type"] if isinstance(mark, dict) else mark
            if mark_type == "geoshape":
                chart = inject_choropleth_data(chart, rows)
            else:
                chart = inject_chart(chart, rows)

    return spec
    

if __name__ == "__main__":
    TEST_SPEC = {
    "answerable": "True",
    "vis_spec": {
        "title": "Global Distribution of Reported Trafficking Incidents",
        "description": "A dashboard built to explore where reported exploitation incidents occur and which crime types are most common.",
        "layout_mode": "informative",
        "charts": [
        {
            "role": "primary",
            "title": "Reported incidents by region",
            "summary": "Read the shading to see which world regions report incidents most often; hover a region for its value.",
            "sql": "SELECT location_country, COUNT(*) AS incident_count FROM incidents WHERE location_country IS NOT NULL GROUP BY location_country ORDER BY incident_count DESC LIMIT 1000",
            "vega_lite": {
            "$schema": "https://vega-lite.github.io/schema/vega-lite/v5.json",
            "width": 720,
            "height": 400,
            "projection": {"type": "equalEarth"},
            "data": {
                "url": "https://cdn.jsdelivr.net/npm/vega-datasets@2/data/world-110m.json",
                "format": {"type": "topojson", "feature": "countries"}
            },
            "geo_granularity": "region",
            "transform": [
                {
                "lookup": "id",
                "from": {
                    "data": {"values": []},
                    "key": "id",
                    "fields": ["value"]
                }
                }
            ],
            "mark": {"type": "geoshape", "stroke": "white", "strokeWidth": 0.4},
            "encoding": {
                "color": {
                "field": "value",
                "type": "quantitative",
                "scale": {"scheme": "yelloworangered"},
                "legend": {"title": "Reported incidents"}
                },
                "tooltip": [
                {"field": "value", "type": "quantitative", "title": "Reported incidents"}
                ]
            },
            "config": {"view": {"stroke": None}, "mark": {"invalid": None}}
            }
        },
        {
            "role": "supporting",
            "title": "Incidents by crime type",
            "summary": "Compare the bar heights to see which crime types are most frequently reported.",
            "sql": "SELECT crime_type, COUNT(*) AS incident_count FROM incidents WHERE crime_type IS NOT NULL GROUP BY crime_type ORDER BY incident_count DESC LIMIT 1000",
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
        }
        ]
    }
    }
    DATABASE_URL = "postgresql+psycopg2://postgres:devpassword@localhost:5544/thesis"
    if DATABASE_URL:
        engine = create_engine("postgresql+psycopg2://postgres:devpassword@localhost:5544/thesis")
    else:
        raise ValueError("Could not build engine")


    spec = inject_data(TEST_SPEC, engine)
    print(json.dumps(spec, indent=1, default=str))