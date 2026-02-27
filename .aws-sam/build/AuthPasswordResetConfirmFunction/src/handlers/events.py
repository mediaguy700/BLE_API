"""Events API: MAC (person) per reader, with payload fields."""
import json
from datetime import datetime
import psycopg2
from src.db import get_conn, api_response

# Events table schema may vary; we use SELECT * for compatibility.


def _event_row(row):
    if not row:
        return None
    return dict(row)


def _parse_body(event):
    try:
        return json.loads(event.get("body") or "{}")
    except Exception:
        return None


def _direction_filter(event):
    """Return 'in' or 'out' if query param direction is set and valid, else None."""
    q = event.get("queryStringParameters") or {}
    d = (q.get("direction") or "").strip().lower()
    return d if d in ("in", "out") else None


def list_events(event, context):
    direction = _direction_filter(event)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if direction:
                cur.execute("SELECT * FROM events WHERE direction = %s ORDER BY id", (direction,))
            else:
                cur.execute("SELECT * FROM events ORDER BY id")
            rows = cur.fetchall()
        return api_response({"events": [_event_row(r) for r in rows]})
    finally:
        conn.close()


def get_event(event, context):
    eid = (event.get("pathParameters") or {}).get("id")
    if not eid:
        return api_response({"error": "id required"}, 400)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM events WHERE id = %s", (eid,))
            row = cur.fetchone()
        if not row:
            return api_response({"error": "Not found"}, 404)
        return api_response(_event_row(row))
    finally:
        conn.close()


def list_reader_events(event, context):
    name = (event.get("pathParameters") or {}).get("readerName")
    if not name:
        return api_response({"error": "readerName required"}, 400)
    direction = _direction_filter(event)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if direction:
                cur.execute(
                    "SELECT * FROM events WHERE reader_name = %s AND direction = %s ORDER BY id",
                    (name, direction),
                )
            else:
                cur.execute("SELECT * FROM events WHERE reader_name = %s ORDER BY id", (name,))
            rows = cur.fetchall()
        return api_response({"events": [_event_row(r) for r in rows]})
    finally:
        conn.close()


def list_events_by_mac(event, context):
    mac = (event.get("pathParameters") or {}).get("mac")
    if not mac:
        return api_response({"error": "mac required"}, 400)
    direction = _direction_filter(event)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if direction:
                cur.execute(
                    "SELECT * FROM events WHERE mac = %s AND direction = %s ORDER BY id",
                    (mac, direction),
                )
            else:
                cur.execute("SELECT * FROM events WHERE mac = %s ORDER BY id", (mac,))
            rows = cur.fetchall()
        return api_response({"events": [_event_row(r) for r in rows]})
    finally:
        conn.close()


def _event_from_body(body):
    return {
        "reader_name": (body.get("reader_name") or "").strip(),
        "mac": (body.get("mac") or "").strip(),
        "direction": (body.get("direction") or "").strip().lower() or None,
        "name": body.get("name"),
        "qr_code": body.get("qr_code"),
        "distance": body.get("distance"),
        "data": body.get("data"),
        "antenna": body.get("antenna"),
        "peak_rssi": body.get("peak_rssi"),
        "date_time": body.get("date_time") or datetime.utcnow(),
        "start_event": body.get("start_event"),
        "count": body.get("count"),
        "tag_event": body.get("tag_event"),
        "uuid": body.get("uuid"),
        "major": body.get("major"),
        "minor": body.get("minor"),
        "namespace": body.get("namespace"),
        "instance": body.get("instance"),
        "voltage": body.get("voltage"),
        "temperature": body.get("temperature"),
        "url": body.get("url"),
    }


def create_event(event, context):
    body = _parse_body(event)
    if body is None:
        return api_response({"error": "Invalid JSON"}, 400)
    ev = _event_from_body(body)
    if not ev["reader_name"] or not ev["mac"]:
        return api_response({"error": "reader_name and mac required"}, 400)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO events (reader_name, mac, direction, name, qr_code,
                    distance, data, antenna, peak_rssi, date_time, start_event, count,
                    tag_event, uuid, major, minor, namespace, instance, voltage, temperature, url)
                VALUES (%(reader_name)s, %(mac)s, %(direction)s, %(name)s, %(qr_code)s,
                    %(distance)s, %(data)s, %(antenna)s, %(peak_rssi)s, %(date_time)s, %(start_event)s, %(count)s,
                    %(tag_event)s, %(uuid)s, %(major)s, %(minor)s, %(namespace)s, %(instance)s, %(voltage)s, %(temperature)s, %(url)s)
                RETURNING *
                """,
                ev,
            )
            row = cur.fetchone()
        conn.commit()
        return api_response(_event_row(row), 201)
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if "foreign key" in str(e).lower():
            return api_response({"error": "reader_name not found"}, 404)
        return api_response({"error": str(e)}, 400)
    finally:
        conn.close()


def update_event(event, context):
    eid = (event.get("pathParameters") or {}).get("id")
    if not eid:
        return api_response({"error": "id required"}, 400)
    body = _parse_body(event)
    if body is None:
        return api_response({"error": "Invalid JSON"}, 400)
    allowed = set(_event_from_body({}).keys())
    updates = []
    params = []
    for k in allowed:
        if k in body:
            v = body.get(k)
            if k == "direction" and v:
                v = str(v).strip().lower() or None
            if k == "reader_name" and v is not None:
                v = str(v).strip()
            if k == "mac" and v is not None:
                v = str(v).strip()
            if k == "count" and v is not None:
                try:
                    v = int(v)
                except (TypeError, ValueError):
                    v = None
            updates.append(k + " = %s")
            params.append(v)
    if not updates:
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM events WHERE id = %s", (eid,))
                row = cur.fetchone()
            if not row:
                return api_response({"error": "Not found"}, 404)
            return api_response(_event_row(row))
        finally:
            conn.close()
    params.append(eid)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute("UPDATE events SET " + ", ".join(updates) + ", updated_at = NOW() WHERE id = %s RETURNING *", params)
            except psycopg2.ProgrammingError:
                conn.rollback()
                cur.execute("UPDATE events SET " + ", ".join(updates) + " WHERE id = %s RETURNING *", params)
            row = cur.fetchone()
        conn.commit()
        if not row:
            return api_response({"error": "Not found"}, 404)
        return api_response(_event_row(row))
    finally:
        conn.close()


def delete_event(event, context):
    eid = (event.get("pathParameters") or {}).get("id")
    if not eid:
        return api_response({"error": "id required"}, 400)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM events WHERE id = %s RETURNING id", (eid,))
            row = cur.fetchone()
        conn.commit()
        if not row:
            return api_response({"error": "Not found"}, 404)
        return api_response({"ok": True}, 200)
    finally:
        conn.close()
