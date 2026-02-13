"""Run database/schema.sql (invoke once after first deploy)."""
import os
from src.db import get_conn, api_response


def run_schema(event, context):
    # From src/handlers/run_schema.py -> project root -> database/schema.sql
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    schema_path = os.path.join(root, "database", "schema.sql")
    if not os.path.isfile(schema_path):
        return api_response({"error": "schema.sql not found", "path": schema_path}, 500)
    sql = open(schema_path).read()
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        return api_response({"ok": True, "message": "Schema applied"})
    except Exception as e:
        conn.rollback()
        return api_response({"error": str(e)}, 500)
    finally:
        conn.close()
