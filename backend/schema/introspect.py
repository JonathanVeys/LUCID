from dataclasses import dataclass, field

from sqlalchemy import Engine, inspect, text


ENUMERABLE_COLUMNS = ["crime_type", "location_region", "confidence"]
ORDINAL_ORDER = {"confidence": ["high", "medium", "low"]}

@dataclass
class Column:
    name: str
    type: str  # rendered type string, e.g. "INTEGER", "VARCHAR(255)"


@dataclass
class Table:
    name: str
    columns: list[Column] = field(default_factory=list)

    @property
    def column_names(self) -> set[str]:
        return {c.name for c in self.columns}


@dataclass
class DBSchema:
    """A point-in-time snapshot of the database schema."""

    tables: dict[str, Table]

    @property
    def table_names(self) -> set[str]:
        return set(self.tables)

    def has_table(self, name: str) -> bool:
        return name in self.tables

    def has_column(self, table: str, column: str) -> bool:
        return table in self.tables and column in self.tables[table].column_names

    def to_prompt_text(self) -> str:
        """Serialise the schema into a compact, readable block for the system prompt."""
        lines: list[str] = []
        for table in self.tables.values():
            cols = ", ".join(f"{c.name} {c.type}" for c in table.columns)
            lines.append(f"{table.name}({cols})")
        return "\n".join(lines)


def load_schema(engine: Engine, schema: str = "public") -> DBSchema:
    """
    Introspect the live database and return a DBSchema snapshot.

    `schema` is the Postgres namespace to read (defaults to "public").
    """
    inspector = inspect(engine)
    tables: dict[str, Table] = {}

    for table_name in inspector.get_table_names(schema=schema):
        columns = [
            Column(name=col["name"], type=str(col["type"]))
            for col in inspector.get_columns(table_name, schema=schema)
        ]
        tables[table_name] = Table(name=table_name, columns=columns)

    return DBSchema(tables=tables)



def format_schema_for_prompt(engine, table_names=("incidents",)):
    db_schema = load_schema(engine)
    blocks = []
    for tname in table_names:
        table = db_schema.tables.get(tname)
        if table is None:
            continue

        name_w = max([len("Column")] + [len(c.name) for c in table.columns])
        type_w = max([len("Type")] + [len(c.type) for c in table.columns])

        header = f"| {'Column'.ljust(name_w)} | {'Type'.ljust(type_w)} |"
        sep    = f"| {'-' * name_w} | {'-' * type_w} |"
        rows   = "\n".join(
            f"| {c.name.ljust(name_w)} | {c.type.ljust(type_w)} |"
            for c in table.columns
        )
        blocks.append(
            f"{header}\n{sep}\n{rows}"
        )
    return "\n\n".join(blocks)



def get_column_vocab(engine, column, table="incidents"):
    with engine.connect() as conn:
        rows = conn.execute(text(
            f"SELECT DISTINCT {column} FROM {table} "
            f"WHERE {column} IS NOT NULL ORDER BY {column}"
        ))
        values = [r[0] for r in rows]
    if column in ORDINAL_ORDER:
        order = ORDINAL_ORDER[column]
        values.sort(key=lambda v: order.index(v) if v in order else len(order))
    return values

def format_vocab_for_prompt(engine):
    lines = []
    for col in ENUMERABLE_COLUMNS:
        quoted = ", ".join(f"'{v}'" for v in get_column_vocab(engine, col))
        lines.append(f"- {col}: {quoted}")
    return "\n".join(lines)