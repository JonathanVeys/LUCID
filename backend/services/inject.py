from sqlalchemy import Engine, create_engine, exc, text
import json
from collections import defaultdict
from pathlib import Path

from backend.errors.validation_error import ValidationError

import os
from dotenv import load_dotenv
from backend.validation.component_validation.parse_model_response import parse_model_response

ROOT_PATH = Path(__file__)
while True:
    if Path(ROOT_PATH/"data").is_dir():
        break
    else:
        ROOT_PATH = ROOT_PATH.parent
    
with open(ROOT_PATH/"data/geo_lookup.json") as f:
    GEO = json.load(f)

def handle_countries(chart:dict, rows:list, value_field:str) -> tuple[list|None, list[ValidationError]]:
    '''
    A function that handles taking raw countries names from database, assinging ISO codes and handles duplicates by merging
    '''
    label_field = chart.get("label_field")
    totals = {}
    for row in rows:
        #Get country name from database row
        country_name = row.get(label_field)
        #Get corresponding country metdata from GEO lookup
        country_meta = GEO.get(country_name,{})
        
        #If no country metadata is present, warn and move on
        if not country_meta or country_meta.get("id") is None:
            # print(f"WARNING : {country_name} does not have metadata and has not been excluded from count")
            continue
        
        #Deconstruct and handle metadata and values
        iso_id = country_meta.get('id')
        _value = row.get(value_field)
        value  = int(_value) if _value is not None else 0
        urls = row.get("urls")

        #If country has already appeared, sum value, if not, add new instance
        if iso_id in totals:
            totals[iso_id]["value"] += value
        else:
            totals[iso_id] = {
                "id":iso_id,
                "value":value,
                "label":country_name,
                "region":country_meta.get("region"),
                "urls":urls
            }
    return list(totals.values()), []
    

def handle_regions(chart:dict, rows:list, value_field:str) -> tuple[list|None, list[ValidationError]]:
    '''
    
    '''
    label_field = chart.get("label_field")

    region_data = defaultdict(lambda: {"value": 0, "urls": []})
    unmatched = []

    for row in rows:
        name = row.get(label_field)
        meta = GEO.get(name)
        if not meta or meta.get("id") is None:
            unmatched.append(name)
            continue

        region = meta["region"]
        v = row.get(value_field)
        region_data[region]["value"] += int(v) if v is not None else 0

        urls = row.get("urls") or []       
        if urls:
            region_data[region]["urls"].extend(
                urls
            )
            # region_data[region]["url_groups"].append(
            #     [{"url": u, "country": meta.get("name", name)} for u in urls]
            # )

    # Pass 2: fan out — iterate GEO (every country we know about)
    totals = {}
    for name, meta in GEO.items():
        iso_id, region = meta.get("id"), meta.get("region")
        if iso_id is None or region not in region_data:
            continue                     
        totals[iso_id] = {
            "id": iso_id,
            "value": region_data[region]["value"],
            "label": region,
            "region": region,
            "urls":region_data[region]["urls"]
        }
    # for country in unmatched:
    #     print(f"WARNING : {country} does not have metadata and has not been excluded from count")
    return list(totals.values()), []


def handle_choropleth_inject(chart:dict, rows:list) -> tuple[dict|None, list[ValidationError]]:
    '''
    
    '''
    value_field = list(rows[0].keys())[1]
    granularity = chart.get("geo_granularity")

    if granularity == "country":
        data, errs = handle_countries(chart, rows, value_field)    
    elif granularity == "region":
        data, errs = handle_regions(chart, rows, value_field)
    if errs:
        return None, errs

    vl = chart.get("vega_lite")
    if vl:
        vl["transform"][0]["from"]["data"]["values"] = data
    return chart, []

def handle_chart_inject(chart:dict, rows:list) -> tuple[dict|None, list[ValidationError]]:
    '''
    A function for taking a non-geoshape chart, and injecting data
    '''

    vl = chart.get("vega_lite")
    label_field = chart.get("label_field")  
    for row in rows:
        try:
            row["label"] = row[label_field] 
            row["urls"] = row["urls"]
        except KeyError as e:
            err = ValidationError(
                type="SQL Execution",
                details=(f"label_field '{label_field}' is not among the query's output "
                         f"columns: {sorted(rows[0].keys())}. Either select it in the SQL "
                         f"or set label_field to one of those columns."),
                location="handle_chart_inject"
            )
            return None, [err]

    if vl:
        vl["data"] = {"values": rows}
    return chart, []



def inject_single_chart(chart:dict, engine:Engine) -> tuple[dict|None, list[ValidationError]]:
    '''
    
    '''
    with engine.connect() as conn:
        agg_sql = chart.get("sql", "")
        url_sql = chart.get("url_sql", "")
        vega_lite = chart.get("vega_lite", {})  

        try:
            url_result = conn.execute(text(url_sql))
            url_rows = [dict(r._mapping) for r in url_result]

            agg_result = conn.execute(text(agg_sql))
            agg_rows = [dict(r._mapping) for r in agg_result]

            label_field = chart.get("label_field")
            url_map = {r[label_field]: (r.get("urls") or []) for r in url_rows}

            rows = []
            for r in agg_rows:
                r["urls"] = url_map.get(r[label_field], [])
                rows.append(r)
            print(rows)
        except (exc.ProgrammingError, exc.DataError) as e:
            msg = getattr(getattr(e.orig, "diag", None), "message_primary", None) or str(e.orig)
            err = ValidationError(
                type="SQL Execution",
                details=f"The query failed: {msg}",
                location="inject_data"
            )
            return None, [err]
        
        if not rows:
                err = ValidationError(
                    type="SQL Execution",
                    details=(f"The following SQL query returned no data from the database. "
                             f"Possibly too restrictive: {agg_sql}"),
                    location="inject_data"
                )
                return None, [err]

        mark:str = vega_lite.get("mark", {}).get("type")
        if mark.lower() in ["geoshape"]:
            injected_chart, errs = handle_choropleth_inject(chart, rows)
            if errs:
                return None, errs
        else:
            injected_chart, errs = handle_chart_inject(chart, rows)
            if errs:
                return None, errs
    return injected_chart, []


def inject_spec(spec:dict, engine:Engine) -> tuple[dict|None, list[ValidationError]]:
    '''
    
    '''
    errors = []
    vis_spec = spec.get("vis_spec", {})
    charts = vis_spec.get("charts")
    for idx, chart in enumerate(charts):
        injected_chart, errs = inject_single_chart(chart, engine)
        if errs:
            errors.extend(errs)
            continue
        charts[idx] = injected_chart
    if errors:
        return None, errors
    return spec, []
    
    

if __name__ == "__main__":
    TEST_SPEC =  '''
    {
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
                    "geo_granularity": "region",
                    "label_field":"location_country",
                    "vega_lite": {
                        "$schema": "https://vega-lite.github.io/schema/vega-lite/v5.json",
                        "width": 720,
                        "height": 400,
                        "projection": {"type": "equalEarth"},
                        "data": {
                            "url": "https://cdn.jsdelivr.net/npm/vega-datasets@2/data/world-110m.json",
                            "format": {"type": "topojson", "feature": "countries"}
                        },
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
                        "config": {"view": {"stroke": null}, "mark": {"invalid": null}}
                        }
                    },
                {
                    "role": "supporting",
                    "title": "Incidents by crime type",
                    "summary": "Compare the bar heights to see which crime types are most frequently reported.",
                    "sql": "SELECT crime_type, COUNT(*) AS incident_count FROM incidents WHERE crime_type IS NOT NULL GROUP BY crime_type ORDER BY incident_count DESC LIMIT 1000",
                    "label_field": "crime_type",
                    "vega_lite": {
                        "$schema": "https://vega-lite.github.io/schema/vega-lite/v5.json",
                        "mark": {"type": "bar", "stroke": "black"},
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
    }'''

    # load_dotenv()
    # DATABASE_URL = os.getenv("DATABASE_URL")
    # if DATABASE_URL:
    #     engine = create_engine(DATABASE_URL)

    # spec, err = parse_model_response(TEST_SPEC)
    # if spec:
    #     vis_spec = spec.get("vis_spec", {})
    # charts = vis_spec.get("charts", [])
    # for chart in charts:
    #     chart, err = inject_data(chart, engine)
    #     if err:
    #         print(err)
    #     elif not err:
    #         print("✅ Success")
    #         with open("debug_chart.json", "w") as f:
    #             json.dump(chart, f, indent=2)
    #     break



