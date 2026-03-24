"""
LangChain-compatible tools for querying the SAP O2C SQLite database.
These tools can be used with any LangChain agent / LLM to interact with
the sap_o2c.db database.

Usage with LangChain:
    from tools import get_all_tools
    tools = get_all_tools()
    agent = initialize_agent(tools, llm, agent="zero-shot-react-description")
"""

import os
import json
import sqlite3
from typing import Optional
from langchain_core.tools import tool

#DB_PATH = os.path.join(os.path.dirname(__file__), "..", "sap_o2c.db")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "sap_o2c.db")


def _get_connection():
    """Return a new SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────────
# 1. Schema / Discovery Tools
# ─────────────────────────────────────────────

@tool
def list_tables() -> str:
    """List all table names in the SAP O2C database.
    Returns a JSON array of table names.
    Use this first to discover what data is available."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return json.dumps(tables)


@tool
def get_table_schema(table_name: str) -> str:
    """Get the column names and types for a specific table.
    Args:
        table_name: Name of the table to inspect.
    Returns a JSON array of objects with column info (name, type, notnull, pk)."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute(f'PRAGMA table_info("{table_name}")')
    columns = [
        {"name": row[1], "type": row[2], "notnull": bool(row[3]), "primary_key": bool(row[5])}
        for row in cursor.fetchall()
    ]
    conn.close()
    if not columns:
        return json.dumps({"error": f"Table '{table_name}' not found."})
    return json.dumps(columns)


@tool
def get_all_table_schemas() -> str:
    """Get the schema (column names) for every table in the database.
    Returns a JSON object mapping table names to their column lists.
    Useful for understanding the full database structure."""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    result = {}
    for t in tables:
        cursor.execute(f'PRAGMA table_info("{t}")')
        result[t] = [row[1] for row in cursor.fetchall()]
    conn.close()
    return json.dumps(result)


# ─────────────────────────────────────────────
# 2. Query / Read Tools
# ─────────────────────────────────────────────

@tool
def run_sql_query(query: str) -> str:
    """Execute a read-only SQL SELECT query on the SAP O2C database and return the results.
    Args:
        query: A valid SQLite SELECT query. Must start with SELECT.
    Returns JSON with 'columns' and 'rows' keys. Limited to 500 rows.
    Example: run_sql_query("SELECT * FROM sales_order_headers LIMIT 10")"""
    q = query.strip()
    if not q.upper().startswith("SELECT"):
        return json.dumps({"error": "Only SELECT queries are allowed. Use run_sql_write for modifications."})
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(q)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [list(row) for row in cursor.fetchmany(500)]
        return json.dumps({"columns": columns, "rows": rows, "row_count": len(rows)})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


@tool
def get_sample_rows(table_name: str, limit: int = 5) -> str:
    """Get sample rows from a table to understand what the data looks like.
    Args:
        table_name: Name of the table.
        limit: Number of sample rows (default 5, max 50).
    Returns JSON with columns and sample rows."""
    limit = min(max(1, limit), 50)
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT * FROM "{table_name}" LIMIT ?', (limit,))
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [list(row) for row in cursor.fetchall()]
        return json.dumps({"table": table_name, "columns": columns, "rows": rows})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


@tool
def count_rows(table_name: str) -> str:
    """Get the total number of rows in a table.
    Args:
        table_name: Name of the table.
    Returns JSON with the count."""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        count = cursor.fetchone()[0]
        return json.dumps({"table": table_name, "count": count})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


@tool
def get_distinct_values(table_name: str, column_name: str, limit: int = 50) -> str:
    """Get distinct values for a specific column in a table.
    Args:
        table_name: Name of the table.
        column_name: Name of the column.
        limit: Max number of distinct values to return (default 50).
    Returns JSON array of distinct values."""
    limit = min(max(1, limit), 200)
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT DISTINCT "{column_name}" FROM "{table_name}" LIMIT ?', (limit,))
        values = [row[0] for row in cursor.fetchall()]
        return json.dumps({"table": table_name, "column": column_name, "distinct_values": values, "count": len(values)})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


@tool
def search_table(table_name: str, column_name: str, search_value: str) -> str:
    """Search for rows where a column contains a specific value (case-insensitive LIKE search).
    Args:
        table_name: Name of the table.
        column_name: Column to search in.
        search_value: Value to search for (supports partial match).
    Returns matching rows as JSON. Limited to 100 results."""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f'SELECT * FROM "{table_name}" WHERE "{column_name}" LIKE ? LIMIT 100',
            (f"%{search_value}%",)
        )
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [list(row) for row in cursor.fetchall()]
        return json.dumps({"columns": columns, "rows": rows, "row_count": len(rows)})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


# ─────────────────────────────────────────────
# 3. Aggregation / Analytics Tools
# ─────────────────────────────────────────────

@tool
def aggregate_column(table_name: str, column_name: str, operation: str = "SUM") -> str:
    """Perform an aggregation operation on a numeric column.
    Args:
        table_name: Name of the table.
        column_name: Numeric column to aggregate.
        operation: One of SUM, AVG, MIN, MAX, COUNT (default SUM).
    Returns JSON with the result."""
    allowed_ops = {"SUM", "AVG", "MIN", "MAX", "COUNT"}
    op = operation.strip().upper()
    if op not in allowed_ops:
        return json.dumps({"error": f"Operation must be one of: {', '.join(allowed_ops)}"})
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT {op}(CAST("{column_name}" AS REAL)) FROM "{table_name}"')
        result = cursor.fetchone()[0]
        return json.dumps({"table": table_name, "column": column_name, "operation": op, "result": result})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


@tool
def group_by_count(table_name: str, column_name: str, limit: int = 20) -> str:
    """Group rows by a column and count occurrences. Useful for distribution analysis.
    Args:
        table_name: Name of the table.
        column_name: Column to group by.
        limit: Max number of groups to return (default 20).
    Returns JSON with group values and counts, sorted by count descending."""
    limit = min(max(1, limit), 100)
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f'SELECT "{column_name}", COUNT(*) as cnt FROM "{table_name}" GROUP BY "{column_name}" ORDER BY cnt DESC LIMIT ?',
            (limit,)
        )
        groups = [{"value": row[0], "count": row[1]} for row in cursor.fetchall()]
        return json.dumps({"table": table_name, "column": column_name, "groups": groups})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


# ─────────────────────────────────────────────
# 4. Write / Modify Tools
# ─────────────────────────────────────────────

@tool
def run_sql_write(query: str) -> str:
    """Execute a write SQL statement (INSERT, UPDATE, DELETE) on the database.
    Args:
        query: A valid SQLite INSERT, UPDATE, or DELETE statement.
    Returns JSON with the number of affected rows.
    WARNING: This modifies the database. Use with caution."""
    q = query.strip()
    upper = q.upper()
    if upper.startswith("SELECT"):
        return json.dumps({"error": "Use run_sql_query for SELECT statements."})
    if upper.startswith("DROP") or upper.startswith("ALTER"):
        return json.dumps({"error": "DROP and ALTER operations are not allowed for safety."})
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(q)
        conn.commit()
        return json.dumps({"success": True, "rows_affected": cursor.rowcount})
    except Exception as e:
        conn.rollback()
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


@tool
def insert_row(table_name: str, data: str) -> str:
    """Insert a single row into a table.
    Args:
        table_name: Name of the table.
        data: JSON string of key-value pairs, e.g. '{"column1": "value1", "column2": "value2"}'.
    Returns JSON with success status."""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        row_data = json.loads(data)
        columns = list(row_data.keys())
        values = list(row_data.values())
        placeholders = ", ".join(["?" for _ in columns])
        col_str = ", ".join([f'"{c}"' for c in columns])
        cursor.execute(f'INSERT INTO "{table_name}" ({col_str}) VALUES ({placeholders})', values)
        conn.commit()
        return json.dumps({"success": True, "rowid": cursor.lastrowid})
    except Exception as e:
        conn.rollback()
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


@tool
def delete_rows(table_name: str, column_name: str, value: str) -> str:
    """Delete rows from a table where a column matches a specific value.
    Args:
        table_name: Name of the table.
        column_name: Column to match.
        value: Value to match for deletion.
    Returns JSON with number of deleted rows."""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'DELETE FROM "{table_name}" WHERE "{column_name}" = ?', (value,))
        conn.commit()
        return json.dumps({"success": True, "rows_deleted": cursor.rowcount})
    except Exception as e:
        conn.rollback()
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


# ─────────────────────────────────────────────
# 5. Relationship / Join Tools
# ─────────────────────────────────────────────

@tool
def join_tables(table1: str, table2: str, join_column: str, limit: int = 20) -> str:
    """Join two tables on a common column and return results.
    Args:
        table1: First table name.
        table2: Second table name.
        join_column: Column name that exists in both tables.
        limit: Max rows to return (default 20).
    Returns JSON with columns and rows from the joined result."""
    limit = min(max(1, limit), 200)
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f'SELECT * FROM "{table1}" t1 INNER JOIN "{table2}" t2 ON t1."{join_column}" = t2."{join_column}" LIMIT ?',
            (limit,)
        )
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = [list(row) for row in cursor.fetchall()]
        return json.dumps({"columns": columns, "rows": rows, "row_count": len(rows)})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        conn.close()


# ─────────────────────────────────────────────
# Tool Registry
# ─────────────────────────────────────────────

def get_all_tools():
    """Return a list of all LangChain tools for use with an agent."""
    return [
        list_tables,
        get_table_schema,
        get_all_table_schemas,
        run_sql_query,
        get_sample_rows,
        count_rows,
        get_distinct_values,
        search_table,
        aggregate_column,
        group_by_count,
        run_sql_write,
        insert_row,
        delete_rows,
        join_tables,
    ]
