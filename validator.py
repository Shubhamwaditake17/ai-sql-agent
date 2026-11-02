"""SQL validation: only a single read-only SELECT is allowed."""
import sqlglot
from sqlglot import exp
from db import DIALECT

MAX_ROWS = 100
BLOCKED = (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Create,
           exp.Alter, exp.Command, exp.Merge)


def validate(sql: str):
    """Return (True, safe_sql) or (False, error_message)."""
    try:
        statements = sqlglot.parse(sql, read=DIALECT)
    except Exception as e:
        return False, f"Syntax error: {e}"

    if len(statements) != 1 or statements[0] is None:
        return False, "Exactly one SQL statement is allowed."

    tree = statements[0]
    if not isinstance(tree, (exp.Select, exp.Union)):
        return False, "Only SELECT queries are allowed."
    if tree.find(*BLOCKED):
        return False, "Destructive operations are blocked."

    # enforce a row limit
    if not tree.args.get("limit"):
        tree = tree.limit(MAX_ROWS)
    return True, tree.sql(dialect=DIALECT)
