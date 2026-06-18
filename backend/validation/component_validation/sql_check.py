from sqlglot import expressions, parse_one
from sqlglot.errors import ParseError

def check_sql_syntax(sql:str, dialect:str="postgres") -> tuple[bool, str|None]:
    '''
    
    '''
    try:
        parse_one(sql, dialect=dialect)
        return True, None
    except ParseError as e:
        return False, str(e)
    
def check_sql_semantic(sql:str, schema, dialect:str="postgres") -> tuple[bool, list[str]|None]:
    '''
    
    '''
    try:
        tree = parse_one(sql, dialect=dialect)
        aliases = {a.alias for a in tree.find_all(expressions.Alias)}
    except ParseError as e:
        return False, [f'SQL failed to parse: {e}']
    errors = []

    #Check that only SELECT is used in query
    if not isinstance(tree, expressions.Select):
        return False, [f'Only SELECT queries allowed; got {type(tree).__name__}']
    
    #Check that only the incident table has been queried
    tables = [t.name for t in tree.find_all(expressions.Table)]
    for t in tables:
        if not schema.has_table(t):
            errors.append(f'Table {t} does no exist. Available: {schema.table_names}')
    
    #Check that columns in query exists in database
    for c in tree.find_all(expressions.Column):
        name, qualifier = c.name, c.table
        if name in aliases:
            continue
        if qualifier:
            if schema.has_table(qualifier) and not schema.has_column(qualifier, name):
                errors.append(f'Column {name} not in table {qualifier}')
        else:
            if not any(schema.has_column(t, name) for t in tables if schema.has_table(t)):
                errors.append(f'Column {name} not found in any referenced table') 
    
    if errors:
        return False, errors
    else:
        return True, None