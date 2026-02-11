"""Lambda handlers for Readers API (unique readers with lat/long)."""
import json
from src.db import get_conn, api_response, api_error


def _parse_query(event):
    qs = event.get("queryStringParameters") or {}
    if not qs:
        return {}
    return {k: (v[0] if isinstance(v, list) else v) for k, v in qs.items()}


def _row_to_reader(r):
    """Convert DB row to JSON-serializable dict."""
    d = dict(r) if hasattr(r, "keys") else r
    out = {
        "readerName": d.get("reader_name"),
        "displayName": d.get("display_name"),
        "description": d.get("description"),
        "latitude": d.get("latitude"),
        "longitude": d.get("longitude"),
    }
    for key, out_key in [("created_at", "createdAt"), ("updated_at", "updatedAt")]:
        val = d.get(key)
        out[out_key] = val.isoformat() if hasattr(val, "isoformat") else val
    return out


def _row_to_child(r):
    """One child (MAC) linked to a reader – exact payload for API use case."""
    d = dict(r) if hasattr(r, "keys") else r
    return {
        "id": d.get("id"),
        "mac": d.get("mac"),
        "name": d.get("name"),
        "qrCode": d.get("qr_code"),
        "distance": d.get("distance"),
        "data": d.get("data"),
        "antenna": d.get("antenna"),
        "peakRSSI": d.get("peak_rssi"),
        "dateTime": d.get("date_time").isoformat() if d.get("date_time") and hasattr(d["date_time"], "isoformat") else d.get("date_time"),
        "readerName": d.get("reader_name"),
        "startEvent": d.get("start_event"),
        "count": d.get("count"),
        "tagEvent": d.get("tag_event"),
        "uuid": d.get("uuid"),
        "major": d.get("major"),
        "minor": d.get("minor"),
        "namespace": d.get("namespace"),
        "instance": d.get("instance"),
        "voltage": d.get("voltage"),
        "temperature": d.get("temperature"),
        "url": d.get("url"),
        "direction": d.get("direction") or "in",
        "createdAt": d.get("created_at").isoformat() if d.get("created_at") and hasattr(d["created_at"], "isoformat") else d.get("created_at"),
    }


def list_readers(event, context):
    """GET /readers - List all readers with lat/long for map placement."""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT reader_name, display_name, description, latitude, longitude, created_at, updated_at
                    FROM readers
                    ORDER BY reader_name
                    """
                )
                rows = cur.fetchall()
        return api_response([_row_to_reader(r) for r in rows])
    except Exception as e:
        return api_error(str(e), 500)


def get_reader(event, context):
    """GET /readers/{readerName} - Get one reader (lat/long). Optional ?include=children to return reader linked to its child MACs (each child: MAC, Distance, Data, Antenna, PeakRSSI, DateTime, ReaderName, StartEvent, Count, TagEvent, UUID, Major, Minor, Namespace, Instance, Voltage, Temperature, URL)."""
    name = event.get("pathParameters", {}) or {}
    reader_name = (name.get("readerName") or "").strip()
    if not reader_name:
        return api_error("readerName required", 400)
    params = _parse_query(event)
    include_children = (params.get("include") or "").strip().lower() == "children"
    limit = min(int(params.get("limit", 100)), 1000) if include_children else 0
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT reader_name, display_name, description, latitude, longitude, created_at, updated_at
                    FROM readers
                    WHERE reader_name = %s
                    """,
                    (reader_name,),
                )
                row = cur.fetchone()
                if not row:
                    return api_error("Reader not found", 404)
                out = _row_to_reader(row)
                if include_children:
                    cur.execute(
                        """
                        SELECT id, mac, name, qr_code, COALESCE(direction, 'in') AS direction, distance, data, antenna, peak_rssi, date_time,
                               reader_name, start_event, count, tag_event, uuid, major, minor,
                               namespace, instance, voltage, temperature, url, created_at
                        FROM events
                        WHERE reader_name = %s
                        ORDER BY date_time DESC
                        LIMIT %s
                        """,
                        (reader_name, limit),
                    )
                    children = cur.fetchall()
                    out["children"] = [_row_to_child(dict(r)) for r in children]
        return api_response(out)
    except Exception as e:
        return api_error(str(e), 500)


def create_reader(event, context):
    """POST /readers - Create a reader/room (readerName unique, lat/long required)."""
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return api_error("Invalid JSON body", 400)
    reader_name = (body.get("readerName") or body.get("reader_name") or "").strip()
    display_name = (body.get("displayName") or body.get("display_name") or "").strip() or None
    description = (body.get("description") or "").strip() or None
    lat = body.get("latitude")
    lng = body.get("longitude")
    if not reader_name:
        return api_error("readerName is required", 400)
    if lat is None or lng is None:
        return api_error("latitude and longitude are required", 400)
    try:
        lat, lng = float(lat), float(lng)
    except (TypeError, ValueError):
        return api_error("latitude and longitude must be numbers", 400)
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO readers (reader_name, display_name, description, latitude, longitude)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (reader_name) DO UPDATE SET
                        display_name = COALESCE(EXCLUDED.display_name, readers.display_name),
                        description = COALESCE(EXCLUDED.description, readers.description),
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        updated_at = NOW()
                    RETURNING reader_name, display_name, description, latitude, longitude, created_at, updated_at
                    """,
                    (reader_name, display_name, description, lat, lng),
                )
                row = cur.fetchone()
        return api_response(_row_to_reader(row), 201)
    except Exception as e:
        return api_error(str(e), 500)


def update_reader(event, context):
    """PUT /readers/{readerName} - Update reader/room (displayName, description, lat/long)."""
    name = event.get("pathParameters", {}) or {}
    reader_name = (name.get("readerName") or "").strip()
    if not reader_name:
        return api_error("readerName required", 400)
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return api_error("Invalid JSON body", 400)
    has_display = "displayName" in body or "display_name" in body
    has_description = "description" in body
    has_lat = "latitude" in body
    has_lng = "longitude" in body
    if not (has_display or has_description or has_lat or has_lng):
        return api_error("Provide at least one of: displayName, description, latitude, longitude", 400)
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT reader_name, display_name, description, latitude, longitude FROM readers WHERE reader_name = %s",
                    (reader_name,),
                )
                r = cur.fetchone()
                if not r:
                    return api_error("Reader not found", 404)
                r = dict(r)
                display_name = (body.get("displayName") or body.get("display_name") or "").strip() or None if has_display else r["display_name"]
                description = (body.get("description") or "").strip() or None if has_description else r["description"]
                lat = float(body["latitude"]) if has_lat else r["latitude"]
                lng = float(body["longitude"]) if has_lng else r["longitude"]
                cur.execute(
                    """
                    UPDATE readers
                    SET display_name = %s, description = %s, latitude = %s, longitude = %s, updated_at = NOW()
                    WHERE reader_name = %s
                    RETURNING reader_name, display_name, description, latitude, longitude, created_at, updated_at
                    """,
                    (display_name, description, lat, lng, reader_name),
                )
                row = cur.fetchone()
        return api_response(_row_to_reader(row))
    except (TypeError, ValueError) as e:
        return api_error(str(e), 400)
    except Exception as e:
        return api_error(str(e), 500)


def delete_reader(event, context):
    """DELETE /readers/{readerName} - Delete a reader."""
    name = event.get("pathParameters", {}) or {}
    reader_name = (name.get("readerName") or "").strip()
    if not reader_name:
        return api_error("readerName required", 400)
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM readers WHERE reader_name = %s RETURNING reader_name",
                    (reader_name,),
                )
                row = cur.fetchone()
        if not row:
            return api_error("Reader not found", 404)
        return api_response({"deleted": reader_name}, 200)
    except Exception as e:
        return api_error(str(e), 500)
