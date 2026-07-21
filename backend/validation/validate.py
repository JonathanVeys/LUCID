from backend.validation.component_validation.validate_sql import validate_sql_semantic, validate_sql_syntax
from backend.schema.introspect import DBSchema
from backend.errors.validation_error import ValidationError
from backend.models.spec import validate_spec, UnansweredResponse, ChartSpec, ScalarSpec
    

    
def evaluate_response(raw_spec:dict, db_schema:DBSchema) -> tuple[bool, list[ValidationError]]:
    '''
    A function that takes in a candidate vis_spec and performs an evaluation on it
    '''
    spec, err = validate_spec(raw_spec)
    if err:
        return False, err
    if isinstance(spec, UnansweredResponse):
        return True, []

    if spec:
        vis_spec = spec.vis_spec
        if isinstance(vis_spec, ScalarSpec):
            agg_sql = vis_spec.sql
            url_sql = vis_spec.url_sql

            for sql in [agg_sql, url_sql]:
                ok, err = validate_sql_syntax(sql)
                if not ok:
                    return False, err
                ok, err = validate_sql_semantic(sql, db_schema)
                if not ok:
                    return False, err
            
        if isinstance(vis_spec, ChartSpec):
            for chart in vis_spec.charts:
                sql = chart.sql
                ok, err = validate_sql_syntax(sql)
                if not ok:
                    return False, err
                ok, err = validate_sql_semantic(sql, db_schema)
                if not ok:
                    return False, err

    return True, []


    


if __name__ == "__main__":
    sample_vis_spec = '''
    {
    "answerable": true,
    "vis_spec": {
        "title": "Trafficking overview: Southeast Asia",
        "description": "A multi-angle view built to explore reported exploitation incidents across the Southeast Asia region.",
        "layout_mode": "informative",
        "charts": [
        {
            "role": "primary",
            "title": "Incidents by crime type",
            "summary": "Compare the bar heights to see which crime types are most frequently reported in the region.",
            "sql": "SELECT crime_type, COUNT(*) AS incident_count FROM incidents WHERE location_region = 'Southeast Asia' AND crime_type IS NOT NULL GROUP BY crime_type ORDER BY incident_count DESC LIMIT 15",
            "label_field":"crime_type",
            "vega_lite": {
            "$schema": "https://vega-lite.github.io/schema/vega-lite/v5.json",
            "mark": {"type": "bar", "stroke": "black"},
            "params": [
                {"name": "select", "select": "point"},
                {"name": "highlight", "select": {"type": "point", "on": "pointerover"}}
            ],
            "encoding": {
                "x": {"field": "crime_type", "type": "nominal", "axis": {"title": "Crime type"}, "sort": "-y"},
                "y": {"field": "incident_count", "type": "quantitative", "axis": {"title": "Number of incidents"}},
                "tooltip": [
                {"field": "crime_type", "type": "nominal"},
                {"field": "incident_count", "type": "quantitative"}
                ],
                "fillOpacity": {
                "condition": {"param": "select", "value": 1},
                "value": 0.3
                },
                "strokeWidth": {
                "condition": [
                    {"param": "select", "empty": false, "value": 2},
                    {"param": "highlight", "empty": false, "value": 0.5}
                ],
                "value": 0
                }
            }
            }
        },
        {
            "role": "supporting",
            "title": "Incidents over time",
            "summary": "Follow the line to see how reporting volume changes over time; pan and zoom to inspect specific periods.",
            "sql": "SELECT reported_date, COUNT(*) AS incident_count FROM incidents WHERE location_region = 'Southeast Asia' AND reported_date IS NOT NULL GROUP BY reported_date ORDER BY reported_date",
            "label_field":"reported_date",
            "vega_lite": {
            "$schema": "https://vega-lite.github.io/schema/vega-lite/v5.json",
            "mark": {"type":"line", "stroke":"black"},
            "params": [
                {"name": "view", "select": {"type": "interval", "encodings": ["x", "y"]}, "bind": "scales"},
                {"name": "select", "select": "point"},
                {"name": "highlight", "select": {"type": "point", "on": "pointerover"}}
            ],
            "encoding": {
                "x": {"field": "reported_date", "type": "temporal", "axis": {"title": "Reported date"}},
                "y": {"field": "incident_count", "type": "quantitative", "axis": {"title": "Number of incidents"}},
                "tooltip": [
                {"field": "reported_date", "type": "temporal"},
                {"field": "incident_count", "type": "quantitative"}
                ],
                "fillOpacity": {
                "condition": {"param": "select", "value": 1},
                "value": 0.3
                },
                "strokeWidth": {
                "condition": [
                    {"param": "select", "empty": false, "value": 2},
                    {"param": "highlight", "empty": false, "value": 1}
                ],
                "value": 0.5
                }
            }
            }
        },
        {
            "role": "supporting",
            "title": "Most frequently reported victim nationalities",
            "summary": "Compare the bars to see which nationalities appear most often among reported victims.",
            "sql": "SELECT victim_nationality, COUNT(*) AS incident_count FROM incidents WHERE location_region = 'Southeast Asia' AND victim_nationality IS NOT NULL GROUP BY victim_nationality ORDER BY incident_count DESC LIMIT 15",
            "label_field":"victim_nationality",
            "vega_lite": {
            "$schema": "https://vega-lite.github.io/schema/vega-lite/v5.json",
            "mark": {"type": "bar", "stroke": "black"},
            "params": [
                {"name": "select", "select": "point"},
                {"name": "highlight", "select": {"type": "point", "on": "pointerover"}}
            ],
            "encoding": {
                "x": {"field": "incident_count", "type": "quantitative", "axis": {"title": "Number of incidents"}},
                "y": {"field": "victim_nationality", "type": "nominal", "axis": {"title": "Victim nationality"}, "sort": "-x"},
                "tooltip": [
                {"field": "victim_nationality", "type": "nominal"},
                {"field": "incident_count", "type": "quantitative"}
                ],
                "fillOpacity": {
                "condition": {"param": "select", "value": 1},
                "value": 0.3
                },
                "strokeWidth": {
                "condition": [
                    {"param": "select", "empty": false, "value": 2},
                    {"param": "highlight", "empty": false, "value": 1}
                ],
                "value": 0.5
                }
            }
            }
        }
        ]
    }
    }
    '''
    # spec, err = parse_model_json(sample_vis_spec)
    # if spec:
    #     ok, errs = evaluate_response(spec, db_schema)
    #     if not ok:
    #         for err in errs:
    #             print(err)
    #     else:
    #         print("✅ Success")



