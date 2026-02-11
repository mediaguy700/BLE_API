"""Lambda handlers for Events API (BLE tag readings; MAC = unique person)."""
import json
from datetime import datetime, timezone
from src.db import get_conn, api_response, api_error


def _parse_query(event):
    qs = event.get("queryStringParameters") or {}
    if not qs:
        return {}
    return {k: (v[0] if isinstance(v, list) else v) for k, v in qs.items()}


def _row_to_event(r):
    return {
        "id": r.get("id"),
        "mac": r.get("mac"),
        "name": r.get("name"),
        "qrCode": r.get("qr_code"),
        "direction": r.get("direction") or "in",  # in = arrived at reader, out = left reader
        "distance": r.get("distance"),
        "data": r.get("data"),
        "antenna": r.get("antenna"),
        "peakRSSI": r.get("peak_rssi"),
        "dateTime": r.get("date_time").isoformat() if r.get("date_time") else None,
        "readerName": r.get("reader_name"),
        "startEvent": r.get("start_event"),
        "count": r.get("count"),
        "tagEvent": r.get("tag_event"),
        "uuid": r.get("uuid"),
        "major": r.get("major"),
        "minor": r.get("minor"),
        "namespace": r.get("namespace"),
        "instance": r.get("instance"),
        "voltage": r.get("voltage"),
        "temperature": r.get("temperature"),
        "url": r.get("url"),
        "createdAt": r.get("created_at").isoformat() if r.get("created_at") else None,
    }


def list_events(event, context):
    """GET /events - List events. Filters: mac, readerName, direction (in|out), limit, from, to."""
    params = _parse_query(event)
    mac = (params.get("mac") or "").strip()
    reader_name = (params.get("readerName") or "").strip()
    direction = (params.get("direction") or "").strip().lower()
    if direction and direction not in ("in", "out"):
        return api_error("direction must be 'in' or 'out'", 400)
    limit = min(int(params.get("limit", 100)), 1000)
    from_ts = params.get("from")
    to_ts = params.get("to")
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                sql = """
                    SELECT id, mac, name, qr_code, COALESCE(direction, 'in') AS direction, distance, data, antenna, peak_rssi, date_time,
                           reader_name, start_event, count, tag_event, uuid, major, minor,
                           namespace, instance, voltage, temperature, url, created_at
                    FROM events
                    WHERE 1=1
                """
                args = []
                if mac:
                    sql += " AND mac = %s"
                    args.append(mac)
                if reader_name:
                    sql += " AND reader_name = %s"
                    args.append(reader_name)
                if direction:
                    sql += " AND COALESCE(direction, 'in') = %s"
                    args.append(direction)
                if from_ts:
                    sql += " AND date_time >= %s"
                    args.append(from_ts)
                if to_ts:
                    sql += " AND date_time <= %s"
                    args.append(to_ts)
                sql += " ORDER BY date_time DESC LIMIT %s"
                args.append(limit)
                cur.execute(sql, args)
                rows = cur.fetchall()
        return api_response([_row_to_event(dict(r)) for r in rows])
    except Exception as e:
        return api_error(str(e), 500)


def list_reader_events(event, context):
    """GET /readers/{readerName}/events - List child MAC addresses (events) for this reader.
    Readers can have multiple child MACs; this endpoint exposes that one-to-many relationship.
    Query: direction (in|out), limit (default 100, max 1000)."""
    path = event.get("pathParameters", {}) or {}
    reader_name = (path.get("readerName") or "").strip()
    if not reader_name:
        return api_error("readerName required", 400)
    params = _parse_query(event)
    direction = (params.get("direction") or "").strip().lower()
    if direction and direction not in ("in", "out"):
        return api_error("direction must be 'in' or 'out'", 400)
    limit = min(int(params.get("limit", 100)), 1000)
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM readers WHERE reader_name = %s",
                    (reader_name,),
                )
                if not cur.fetchone():
                    return api_error("Reader not found", 404)
                sql = """
                    SELECT id, mac, name, qr_code, COALESCE(direction, 'in') AS direction, distance, data, antenna, peak_rssi, date_time,
                           reader_name, start_event, count, tag_event, uuid, major, minor,
                           namespace, instance, voltage, temperature, url, created_at
                    FROM events
                    WHERE reader_name = %s
                """
                args = [reader_name]
                if direction:
                    sql += " AND COALESCE(direction, 'in') = %s"
                    args.append(direction)
                sql += " ORDER BY date_time DESC LIMIT %s"
                args.append(limit)
                cur.execute(sql, args)
                rows = cur.fetchall()
        return api_response([_row_to_event(dict(r)) for r in rows])
    except Exception as e:
        return api_error(str(e), 500)


def get_event(event, context):
    """GET /events/{id} - Get single event by id."""
    path = event.get("pathParameters", {}) or {}
    eid = path.get("id")
    if not eid:
        return api_error("id required", 400)
    try:
        eid = int(eid)
    except (TypeError, ValueError):
        return api_error("id must be integer", 400)
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, mac, name, qr_code, COALESCE(direction, 'in') AS direction, distance, data, antenna, peak_rssi, date_time,
                           reader_name, start_event, count, tag_event, uuid, major, minor,
                           namespace, instance, voltage, temperature, url, created_at
                    FROM events WHERE id = %s
                    """,
                    (eid,),
                )
                row = cur.fetchone()
        if not row:
            return api_error("Event not found", 404)
        return api_response(_row_to_event(dict(row)))
    except Exception as e:
        return api_error(str(e), 500)


def list_events_by_mac(event, context):
    """GET /events/person/{mac} - List events for a person (MAC)."""
    path = event.get("pathParameters", {}) or {}
    mac = (path.get("mac") or "").strip()
    if not mac:
        return api_error("mac required", 400)
    params = _parse_query(event)
    limit = min(int(params.get("limit", 100)), 1000)
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, mac, name, qr_code, COALESCE(direction, 'in') AS direction, distance, data, antenna, peak_rssi, date_time,
                           reader_name, start_event, count, tag_event, uuid, major, minor,
                           namespace, instance, voltage, temperature, url, created_at
                    FROM events
                    WHERE mac = %s
                    ORDER BY date_time DESC
                    LIMIT %s
                    """,
                    (mac, limit),
                )
                rows = cur.fetchall()
        return api_response([_row_to_event(dict(r)) for r in rows])
    except Exception as e:
        return api_error(str(e), 500)


def _parse_datetime(s):
    if not s:
        return None
    if isinstance(s, datetime):
        return s
    s = str(s).strip()
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            return datetime.strptime(s.replace("Z", "").replace("+00:00", "").strip(), fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def create_event(event, context):
    """POST /events - Ingest a BLE event. MAC = person, readerName = reader (must exist)."""
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return api_error("Invalid JSON body", 400)
    mac = (body.get("mac") or "").strip()
    reader_name = (body.get("readerName") or body.get("reader_name") or "").strip()
    date_time = body.get("dateTime") or body.get("date_time")
    if not mac:
        return api_error("mac is required", 400)
    if not reader_name:
        return api_error("readerName is required", 400)
    dt = _parse_datetime(date_time) if date_time else datetime.now(timezone.utc)
    if not dt:
        return api_error("dateTime invalid or required", 400)
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                direction_val = (body.get("direction") or "in").strip().lower() or "in"
                if direction_val not in ("in", "out"):
                    direction_val = "in"
                cur.execute(
                    """
                    INSERT INTO events (
                        mac, name, qr_code, direction, distance, data, antenna, peak_rssi, date_time, reader_name,
                        start_event, count, tag_event, uuid, major, minor,
                        namespace, instance, voltage, temperature, url
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    RETURNING id, mac, name, qr_code, COALESCE(direction, 'in') AS direction, distance, data, antenna, peak_rssi, date_time,
                              reader_name, start_event, count, tag_event, uuid, major, minor,
                              namespace, instance, voltage, temperature, url, created_at
                    """,
                    (
                        mac,
                        body.get("name"),
                        body.get("qrCode") or body.get("qr_code"),
                        direction_val,
                        body.get("distance"),
                        body.get("data"),
                        body.get("antenna"),
                        body.get("peakRSSI") or body.get("peak_rssi"),
                        dt,
                        reader_name,
                        body.get("startEvent") if "startEvent" in body else body.get("start_event"),
                        body.get("count"),
                        body.get("tagEvent") or body.get("tag_event"),
                        body.get("uuid"),
                        body.get("major"),
                        body.get("minor"),
                        body.get("namespace"),
                        body.get("instance"),
                        body.get("voltage"),
                        body.get("temperature"),
                        body.get("url"),
                    ),
                )
                row = cur.fetchone()
        return api_response(_row_to_event(dict(row)), 201)
    except Exception as e:
        if "readers_reader_name_fkey" in str(e) or "foreign key" in str(e).lower():
            return api_error("readerName must exist in readers table", 400)
        return api_error(str(e), 500)


def update_event(event, context):
    """PUT /events/{id} - Update an event (person/MAC reading at a reader)."""
    path = event.get("pathParameters", {}) or {}
    eid = path.get("id")
    if not eid:
        return api_error("id required", 400)
    try:
        eid = int(eid)
    except (TypeError, ValueError):
        return api_error("id must be integer", 400)
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return api_error("Invalid JSON body", 400)
    if not any(k in body for k in ("mac", "readerName", "reader_name", "name", "qrCode", "qr_code", "direction", "distance", "data", "antenna", "peakRSSI", "dateTime", "date_time", "startEvent", "count", "tagEvent", "uuid", "major", "minor", "namespace", "instance", "voltage", "temperature", "url")):
        return api_error("Provide at least one field to update", 400)
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, mac, name, qr_code, COALESCE(direction, 'in') AS direction, distance, data, antenna, peak_rssi, date_time, reader_name,
                           start_event, count, tag_event, uuid, major, minor, namespace, instance,
                           voltage, temperature, url
                    FROM events WHERE id = %s
                    """,
                    (eid,),
                )
                row = cur.fetchone()
                if not row:
                    return api_error("Event not found", 404)
                row = dict(row)
                # Merge body into current row (only update provided fields)
                mac = (body.get("mac") or "").strip() if "mac" in body else row["mac"]
                name = body.get("name") if "name" in body else row.get("name")
                qr_code = body.get("qrCode") if "qrCode" in body else body.get("qr_code") if "qr_code" in body else row.get("qr_code")
                reader_name = (body.get("readerName") or body.get("reader_name") or "").strip() if ("readerName" in body or "reader_name" in body) else row["reader_name"]
                direction = (body.get("direction") or "in").strip().lower() if "direction" in body else (row.get("direction") or "in")
                if direction not in ("in", "out"):
                    direction = "in"
                distance = body["distance"] if "distance" in body else row["distance"]
                data = body.get("data") if "data" in body else row["data"]
                antenna = body.get("antenna") if "antenna" in body else row["antenna"]
                peak_rssi = body.get("peakRSSI") or body.get("peak_rssi") if ("peakRSSI" in body or "peak_rssi" in body) else row["peak_rssi"]
                dt_val = body.get("dateTime") or body.get("date_time") if ("dateTime" in body or "date_time" in body) else row["date_time"]
                date_time = _parse_datetime(dt_val) if dt_val is not None else row["date_time"]
                if date_time is None and ("dateTime" in body or "date_time" in body):
                    return api_error("dateTime invalid", 400)
                start_event = body.get("startEvent") if "startEvent" in body else body.get("start_event") if "start_event" in body else row["start_event"]
                count = body.get("count") if "count" in body else row["count"]
                tag_event = body.get("tagEvent") or body.get("tag_event") if ("tagEvent" in body or "tag_event" in body) else row["tag_event"]
                uuid_val = body.get("uuid") if "uuid" in body else row["uuid"]
                major = body.get("major") if "major" in body else row["major"]
                minor = body.get("minor") if "minor" in body else row["minor"]
                namespace = body.get("namespace") if "namespace" in body else row["namespace"]
                instance = body.get("instance") if "instance" in body else row["instance"]
                voltage = body.get("voltage") if "voltage" in body else row["voltage"]
                temperature = body.get("temperature") if "temperature" in body else row["temperature"]
                url = body.get("url") if "url" in body else row["url"]
                if not mac:
                    return api_error("mac cannot be empty", 400)
                if not reader_name:
                    return api_error("readerName cannot be empty", 400)
                cur.execute(
                    """
                    UPDATE events SET
                        mac = %s, name = %s, qr_code = %s, reader_name = %s, direction = %s, distance = %s, data = %s, antenna = %s,
                        peak_rssi = %s, date_time = %s, start_event = %s, count = %s, tag_event = %s,
                        uuid = %s, major = %s, minor = %s, namespace = %s, instance = %s,
                        voltage = %s, temperature = %s, url = %s
                    WHERE id = %s
                    RETURNING id, mac, name, qr_code, COALESCE(direction, 'in') AS direction, distance, data, antenna, peak_rssi, date_time,
                              reader_name, start_event, count, tag_event, uuid, major, minor,
                              namespace, instance, voltage, temperature, url, created_at
                    """,
                    (mac, name, qr_code, reader_name, direction, distance, data, antenna, peak_rssi, date_time,
                     start_event, count, tag_event, uuid_val, major, minor, namespace, instance,
                     voltage, temperature, url, eid),
                )
                updated = cur.fetchone()
        return api_response(_row_to_event(dict(updated)))
    except Exception as e:
        if "readers_reader_name_fkey" in str(e) or "foreign key" in str(e).lower():
            return api_error("readerName must exist in readers table", 400)
        return api_error(str(e), 500)


def delete_event(event, context):
    """DELETE /events/{id} - Delete an event (remove person/MAC reading)."""
    path = event.get("pathParameters", {}) or {}
    eid = path.get("id")
    if not eid:
        return api_error("id required", 400)
    try:
        eid = int(eid)
    except (TypeError, ValueError):
        return api_error("id must be integer", 400)
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM events WHERE id = %s RETURNING id, mac, reader_name", (eid,))
                row = cur.fetchone()
        if not row:
            return api_error("Event not found", 404)
        return api_response({"deleted": eid, "mac": row["mac"], "readerName": row["reader_name"]}, 200)
    except Exception as e:
        return api_error(str(e), 500)
