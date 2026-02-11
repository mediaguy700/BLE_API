"""PostgreSQL connection helper for Lambda. Reuses one connection per container for speed."""
import os
import json
from contextlib import contextmanager

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None
    RealDictCursor = None

# Reused across warm invocations to avoid new TCP + auth per request
_conn = None
# Cached password from Secrets Manager (one fetch per container)
_password_from_secret = None


def _get_password():
    """Resolve password from env or Secrets Manager (DB_SECRET_ARN)."""
    global _password_from_secret
    secret_arn = os.environ.get("DB_SECRET_ARN", "").strip()
    if secret_arn:
        if _password_from_secret is not None:
            return _password_from_secret
        try:
            import boto3
            client = boto3.client("secretsmanager")
            resp = client.get_secret_value(SecretId=secret_arn)
            data = json.loads(resp.get("SecretString", "{}"))
            _password_from_secret = data.get("password", "")
            return _password_from_secret
        except Exception as e:
            raise RuntimeError(f"Failed to get DB password from Secrets Manager: {e}") from e
    return os.environ.get("DB_PASSWORD", "")


def get_connection_params():
    return {
        "host": os.environ.get("DB_HOST"),
        "port": int(os.environ.get("DB_PORT", "5432")),
        "dbname": os.environ.get("DB_NAME"),
        "user": os.environ.get("DB_USER"),
        "password": _get_password(),
    }


def _is_usable(conn):
    if conn is None:
        return False
    try:
        if getattr(conn, "closed", True):
            return False
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return True
    except Exception:
        return False


def _get_or_create_conn():
    global _conn
    if _is_usable(_conn):
        return _conn
    if _conn is not None:
        try:
            _conn.close()
        except Exception:
            pass
        _conn = None
    if not psycopg2:
        raise RuntimeError("psycopg2 not installed")
    params = get_connection_params()
    if not all([params["host"], params["dbname"], params["user"], params["password"]]):
        raise ValueError("DB_HOST, DB_NAME, DB_USER, DB_PASSWORD must be set")
    _conn = psycopg2.connect(**params, cursor_factory=RealDictCursor)
    return _conn


@contextmanager
def get_conn():
    conn = _get_or_create_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    # Do not close: reuse on next invocation


def api_response(body, status_code=200, headers=None):
    origin = os.environ.get("ALLOWED_ORIGIN", "*")
    h = {"Content-Type": "application/json", "Access-Control-Allow-Origin": origin}
    if headers:
        h.update(headers)
    return {
        "statusCode": status_code,
        "headers": h,
        "body": json.dumps(body) if isinstance(body, (dict, list)) else body,
    }


def api_error(message, status_code=400):
    return api_response({"error": message}, status_code=status_code)
