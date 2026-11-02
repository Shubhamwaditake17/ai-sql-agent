"""Database module: connection, schema, query execution."""
import os
from sqlalchemy import create_engine, inspect, text

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///shop.db")
DIALECT = "mysql" if DATABASE_URL.startswith("mysql") else "sqlite"
engine = create_engine(DATABASE_URL)


def get_schema() -> str:
    """Return schema as compact text: table(col type, ...) + foreign keys."""
    insp = inspect(engine)
    lines = []
    for table in insp.get_table_names():
        cols = ", ".join(f"{c['name']} {c['type']}" for c in insp.get_columns(table))
        lines.append(f"{table}({cols})")
        for fk in insp.get_foreign_keys(table):
            lines.append(
                f"  FK {table}.{fk['constrained_columns'][0]} -> "
                f"{fk['referred_table']}.{fk['referred_columns'][0]}"
            )
    return "\n".join(lines)


def run_query(sql: str):
    """Execute SQL, return (columns, rows) with JSON-safe values."""
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        cols = list(result.keys())
        rows = [
            [v if isinstance(v, (int, float, str, type(None))) else str(v) for v in r]
            for r in result.fetchall()
        ]
    return cols, rows
