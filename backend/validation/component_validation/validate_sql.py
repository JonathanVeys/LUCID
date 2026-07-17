from sqlglot import expressions, parse_one
from sqlglot.errors import ParseError, TokenError

from backend.errors.validation_error import ValidationError

def validate_sql_syntax(sql:str, dialect:str="postgres") -> tuple[bool, list[ValidationError]]:
    '''
    A function for checking SQL syntax 
    '''
    try:
        parse_one(sql, dialect=dialect)
        return True, []
    except (ParseError,TokenError) as e:
        err = ValidationError(
            type="SQL Syntax",
            details=f"SQL could not be parsed: {e}",
            location="check_sql_syntax"
        )
        return False, [err]
    
def validate_sql_semantic(sql:str, db_schema, dialect:str="postgres") -> tuple[bool, list[ValidationError]]:
    '''
    A function for checking SQL semantics
    '''
    try:
        tree = parse_one(sql, dialect=dialect)
        aliases = [a.alias for a in tree.find_all(expressions.Alias)]
        tables = [t.name for t in tree.find_all(expressions.Table)]
    except (ParseError, TokenError) as e:
        err = ValidationError(
            type="SQL Semantic",
            details=f"SQL could not be parsed: {e}",
            location="validate_sql_semantic"
        )
        return False, [err]

    #Check that only SELECT is used in query
    if not isinstance(tree, expressions.Select):
        err = ValidationError(
            type="SQL Semantic",
            details=f'Only SELECT queries allowed; got {type(tree).__name__}',
            location="validate_sql_semantic"
        )
        return False, [err]

    for t in tables:
        if not t.lower() in ["incidents"]:
            err = ValidationError(
                type="SQL Semantic",
                details=f"SQL query should only query the Incidents table, not {t}",
                location="validate_sql_semantic"
            )
            return False, [err]
        
    missing = {
        c.name
        for c in tree.find_all(expressions.Column)
        if c.name not in aliases                      # skip query-defined names
        and not db_schema.has_column("incidents", c.name)
    }
    if missing:
        err = ValidationError(
            type="SQL Semantic",
            details=f"Chart contains column reference not present in Incidents table: {missing}",
            location="validate_sql_semantic"
        )
        return False, [err]

    return True, []
    