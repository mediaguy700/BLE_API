"""Run database/schema.sql and database/migrations/*.sql (invoke after deploy)."""
import os
from src.db import get_conn, api_response


def run_schema(event, context):
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            schema_path = os.path.join(root, "database", "schema.sql")
            if os.path.isfile(schema_path):
                cur.execute(open(schema_path).read())
            migrations_dir = os.path.join(root, "database", "migrations")
            if os.path.isdir(migrations_dir):
                for fname in sorted(os.listdir(migrations_dir)):
                    if fname.endswith(".sql"):
                        path = os.path.join(migrations_dir, fname)
                        cur.execute(open(path).read())
        conn.commit()
        return api_response({"ok": True, "message": "Schema and migrations applied"})
    except Exception as e:
        conn.rollback()
        return api_response({"error": str(e)}, 500)
    finally:
        conn.close()
