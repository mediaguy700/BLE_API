"""Database connection and helpers for BLE API."""
import os
import json
from datetime import date, datetime
import psycopg2
from psycopg2.extras import RealDictCursor


def _json_serial(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(repr(obj) + " is not JSON serializable")

try:
    import boto3
except ImportError:
    boto3 = None


def api_response(body, status_code=200):
    """Return API Gateway Lambda response with CORS."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": os.environ.get("ALLOWED_ORIGIN", "*"),
            "Access-Control-Allow-Headers": "Content-Type,X-Api-Key",
        },
        "body": json.dumps(body, default=_json_serial) if not isinstance(body, str) else body,
    }


def get_connection_params():
    """Build connection params from env (Secrets Manager or DB_*)."""
    secret_arn = os.environ.get("DB_SECRET_ARN")
    if secret_arn and boto3:
        client = boto3.client("secretsmanager")
        raw = client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(raw["SecretString"])
        return {
            "host": os.environ.get("DB_HOST"),
            "port": os.environ.get("DB_PORT", "5432"),
            "dbname": os.environ.get("DB_NAME", "ble"),
            "user": secret.get("username", os.environ.get("DB_USER", "ble")),
            "password": secret.get("password", ""),
        }
    return {
        "host": os.environ.get("DB_HOST"),
        "port": os.environ.get("DB_PORT", "5432"),
        "dbname": os.environ.get("DB_NAME", "ble"),
        "user": os.environ.get("DB_USER", "ble"),
        "password": os.environ.get("DB_PASSWORD", ""),
    }


def get_conn():
    """Return a DB connection (caller must close)."""
    params = get_connection_params()
    return psycopg2.connect(**params, cursor_factory=RealDictCursor)
