from backend.validation.component_validation.spec_check import validate_vis_spec
from backend.validation.component_validation.sql_check import check_sql_semantic, check_sql_syntax
from backend.schema.introspect import DBSchema

    

def validate(vis_spec:dict, db_schema:DBSchema):
    '''
    
    '''
    spec, errors = validate_vis_spec(vis_spec)
    if errors:
        return None, errors
    
    if spec is not None:
        sql_queries = [chart.sql for chart in spec.charts]
    
        for query in sql_queries:
            check, error = check_sql_syntax(query)
            if not check:
                return None, error
            check, errors = check_sql_semantic(query, db_schema)
            if not check:
                return None, errors
    
    return spec, None

    
