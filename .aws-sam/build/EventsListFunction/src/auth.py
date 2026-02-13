"""Static API key check. When STATIC_API_KEY env is set, requests must send it in x-api-key header."""
import os
from src.db import api_response


def get_api_key_from_event(event):
    """Extract x-api-key from request (case-insensitive header keys)."""
    headers = event.get("headers") or {}
    # API Gateway may normalize to lowercase
    for k, v in headers.items():
        if k.lower() == "x-api-key" and v:
            return v.strip() if isinstance(v, str) else v
    return None


def require_static_api_key(event):
    """
    If STATIC_API_KEY is set in env, require x-api-key header to match.
    Returns None if allowed, or a 403 response dict if not.
    """
    static_key = (os.environ.get("STATIC_API_KEY") or "").strip()
    if not static_key:
        return None  # no static key configured; rely on API Gateway key
    provided = get_api_key_from_event(event)
    if provided and provided == static_key:
        return None
    return api_response({"error": "Forbidden"}, 403)
