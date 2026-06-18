from dataclasses import dataclass, field

from sqlalchemy import Engine, inspect


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