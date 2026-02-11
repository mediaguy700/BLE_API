"""One-off Lambda to run database/schema.sql and migrations. Invoke after deploy when UseStackPostgres=true."""
import os
import sys

# Lambda package root is the project root (CodeUri: .)
PACKAGE_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _get_password():
    """Resolve password from env or Secrets Manager (DB_SECRET_ARN). Matches src.db logic."""
    secret_arn = os.environ.get("DB_SECRET_ARN", "").strip()
    if secret_arn:
        try:
            import boto3
            import json
            client = boto3.client("secretsmanager")
            resp = client.get_secret_value(SecretId=secret_arn)
            data = json.loads(resp.get("SecretString", "{}"))
            return data.get("password", "")
        except Exception as e:
            raise RuntimeError(f"Failed to get DB password from Secrets Manager: {e}") from e
    return os.environ.get("DB_PASSWORD", "")


def _split_sql(content):
    """Split SQL file into single statements (by ;), drop comments and empty."""
    statements = []
    current = []
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") or not stripped:
            continue
        current.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(current).strip()
            if stmt and stmt != ";":
                statements.append(stmt)
            current = []
    if current:
        stmt = "\n".join(current).strip()
        if stmt:
            statements.append(stmt)
    return statements


def run_schema(event, context):
    """Run schema and migrations. Call once after stack deploy with stack PostgreSQL."""
    try:
        import psycopg2
    except ImportError:
        return {"statusCode": 500, "body": "psycopg2 not available"}

    host = os.environ.get("DB_HOST")
    dbname = os.environ.get("DB_NAME")
    user = os.environ.get("DB_USER")
    port = int(os.environ.get("DB_PORT", "5432"))
    password = _get_password()
    if not all([host, dbname, user, password]):
        return {"statusCode": 400, "body": "DB_HOST, DB_NAME, DB_USER, and password (DB_PASSWORD or DB_SECRET_ARN) required"}

    conn = psycopg2.connect(
        host=host, port=port, dbname=dbname, user=user, password=password
    )
    conn.autocommit = True
    cur = conn.cursor()

    try:
        schema_path = os.path.join(PACKAGE_ROOT, "database", "schema.sql")
        with open(schema_path) as f:
            for stmt in _split_sql(f.read()):
                cur.execute(stmt)

        migrations_dir = os.path.join(PACKAGE_ROOT, "database", "migrations")
        if os.path.isdir(migrations_dir):
            for name in sorted(os.listdir(migrations_dir)):
                if name.endswith(".sql"):
                    path = os.path.join(migrations_dir, name)
                    with open(path) as f:
                        for stmt in _split_sql(f.read()):
                            cur.execute(stmt)

        cur.close()
        conn.close()
        return {"statusCode": 200, "body": "Schema and migrations applied."}
    except Exception as e:
        cur.close()
        conn.close()
        return {"statusCode": 500, "body": str(e)}
