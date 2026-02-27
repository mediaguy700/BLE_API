"""Login: register, login, logout, me (session token auth)."""
import json
import os
import secrets
import hashlib
from datetime import datetime, timezone, timedelta

from src.db import get_conn, api_response


def _parse_body(event):
    try:
        return json.loads(event.get("body") or "{}")
    except Exception:
        return None


def _hash_password(password: str, salt: bytes = None):
    if salt is None:
        salt = secrets.token_bytes(32)
    h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return salt.hex() + ":" + h.hex()


def _verify_password(password: str, stored: str) -> bool:
    try:
        salt_hex, hash_hex = stored.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        h = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
        return h.hex() == hash_hex
    except Exception:
        return False


def _bearer_token(event):
    auth = (event.get("headers") or {}).get("Authorization") or (event.get("headers") or {}).get("authorization")
    if not auth or not auth.startswith("Bearer "):
        return None
    return auth[7:].strip()


def _session_days():
    return int(os.environ.get("SESSION_DAYS", "7"))


def _reset_expiry_hours():
    return int(os.environ.get("RESET_EXPIRY_HOURS", "1"))


def register(event, context):
    """POST /auth/register - Create user. Body: username, password, email (optional)."""
    body = _parse_body(event)
    if not body:
        return api_response({"error": "Invalid JSON"}, 400)
    username = (body.get("username") or "").strip()
    password = body.get("password")
    email = (body.get("email") or "").strip() or None
    if not username:
        return api_response({"error": "username required"}, 400)
    if not password:
        return api_response({"error": "password required"}, 400)
    if len(username) > 50:
        return api_response({"error": "username too long"}, 400)
    password_hash = _hash_password(password)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO users (username, password_hash, email)
                   VALUES (%s, %s, %s)
                   RETURNING id, username, email, created_at""",
                (username, password_hash, email),
            )
            row = cur.fetchone()
        conn.commit()
        user = dict(row) if row else None
        if not user:
            return api_response({"error": "Insert failed"}, 500)
        # omit password_hash from response
        out = {k: (str(v) if hasattr(v, "hex") else v) for k, v in user.items() if k != "password_hash"}
        return api_response({"user": out}, 201)
    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower() or "duplicate" in str(e).lower():
            return api_response({"error": "username already exists"}, 409)
        return api_response({"error": str(e)}, 400)
    finally:
        conn.close()


def login(event, context):
    """POST /auth/login - Body: username, password. Returns user + token."""
    body = _parse_body(event)
    if not body:
        return api_response({"error": "Invalid JSON"}, 400)
    username = (body.get("username") or "").strip()
    password = body.get("password")
    if not username or not password:
        return api_response({"error": "username and password required"}, 400)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, username, email, password_hash, created_at FROM users WHERE username = %s",
                (username,),
            )
            row = cur.fetchone()
        if not row:
            return api_response({"error": "Invalid username or password"}, 401)
        user = dict(row)
        if not _verify_password(password, user["password_hash"]):
            return api_response({"error": "Invalid username or password"}, 401)
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(days=_session_days())
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO sessions (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (str(user["id"]), token, expires_at),
            )
        conn.commit()
        out = {"id": str(user["id"]), "username": user["username"], "email": user.get("email"), "created_at": str(user.get("created_at"))}
        return api_response({"user": out, "token": token, "expires_at": expires_at.isoformat()})
    finally:
        conn.close()


def logout(event, context):
    """POST /auth/logout - Requires Authorization: Bearer <token>. Deletes session."""
    token = _bearer_token(event)
    if not token:
        return api_response({"error": "Authorization: Bearer <token> required"}, 401)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM sessions WHERE token = %s", (token,))
        conn.commit()
        return api_response({"ok": True, "message": "Logged out"})
    finally:
        conn.close()


def me(event, context):
    """GET /auth/me - Requires Authorization: Bearer <token>. Returns current user."""
    token = _bearer_token(event)
    if not token:
        return api_response({"error": "Authorization: Bearer <token> required"}, 401)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT u.id, u.username, u.email, u.created_at
                   FROM users u
                   JOIN sessions s ON s.user_id = u.id
                   WHERE s.token = %s AND s.expires_at > CURRENT_TIMESTAMP""",
                (token,),
            )
            row = cur.fetchone()
        if not row:
            return api_response({"error": "Invalid or expired token"}, 401)
        user = {k: (str(v) if hasattr(v, "hex") else v) for k, v in dict(row).items()}
        return api_response({"user": user})
    finally:
        conn.close()


def password_reset_request(event, context):
    """POST /auth/password-reset/request - Body: email or username. Creates reset token.
    Returns message; optionally returns token for testing (no email sent)."""
    body = _parse_body(event)
    if not body:
        return api_response({"error": "Invalid JSON"}, 400)
    email = (body.get("email") or "").strip() or None
    username = (body.get("username") or "").strip() or None
    if not email and not username:
        return api_response({"error": "email or username required"}, 400)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if email:
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            else:
                cur.execute("SELECT id FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
        if not row:
            return api_response({"message": "If an account exists, a reset link has been sent."}, 200)
        user_id = str(row["id"])
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=_reset_expiry_hours())
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO password_resets (user_id, token, expires_at) VALUES (%s, %s, %s)",
                (user_id, token, expires_at),
            )
        conn.commit()
        out = {"message": "If an account exists, a reset link has been sent.", "expires_at": expires_at.isoformat()}
        if os.environ.get("RETURN_RESET_TOKEN_FOR_TESTING", "").lower() in ("1", "true", "yes"):
            out["token"] = token
        return api_response(out, 200)
    finally:
        conn.close()


def password_reset_confirm(event, context):
    """POST /auth/password-reset/confirm - Body: token, new_password. Sets new password and invalidates reset."""
    body = _parse_body(event)
    if not body:
        return api_response({"error": "Invalid JSON"}, 400)
    token = (body.get("token") or "").strip()
    new_password = body.get("new_password")
    if not token:
        return api_response({"error": "token required"}, 400)
    if not new_password:
        return api_response({"error": "new_password required"}, 400)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT pr.user_id FROM password_resets pr
                   WHERE pr.token = %s AND pr.expires_at > CURRENT_TIMESTAMP""",
                (token,),
            )
            row = cur.fetchone()
        if not row:
            return api_response({"error": "Invalid or expired reset token"}, 400)
        user_id = row["user_id"]
        password_hash = _hash_password(new_password)
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (password_hash, user_id),
            )
            cur.execute("DELETE FROM password_resets WHERE token = %s", (token,))
        conn.commit()
        return api_response({"ok": True, "message": "Password has been reset."}, 200)
    except Exception as e:
        conn.rollback()
        return api_response({"error": str(e)}, 500)
    finally:
        conn.close()
