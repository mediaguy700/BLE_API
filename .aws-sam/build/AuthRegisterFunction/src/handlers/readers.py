"""Readers API: name (unique), latitude, longitude."""
import psycopg2
from src.db import get_conn, api_response


def _reader_row(row):
    if not row:
        return None
    return dict(row)


def list_readers(event, context):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM readers ORDER BY 1")
            rows = cur.fetchall()
        return api_response({"readers": [_reader_row(r) for r in rows]})
    finally:
        conn.close()


def get_reader(event, context):
    name = (event.get("pathParameters") or {}).get("readerName")
    if not name:
        return api_response({"error": "readerName required"}, 400)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM readers")
            rows = cur.fetchall()
        row = None
        for r in rows:
            if r.get("name") == name or r.get("reader_name") == name:
                row = r
                break
        if not row:
            return api_response({"error": "Not found"}, 404)
        return api_response(_reader_row(row))
    finally:
        conn.close()


def create_reader(event, context):
    try:
        body = __import__("json").loads(event.get("body") or "{}")
    except Exception:
        return api_response({"error": "Invalid JSON"}, 400)
    name = (body.get("name") or body.get("reader_name") or "").strip()
    lat = body.get("latitude") if "latitude" in body else body.get("lat")
    lon = body.get("longitude") if "longitude" in body else body.get("long")
    if not name:
        return api_response({"error": "name or reader_name required"}, 400)
    if lat is None or lon is None:
        return api_response({"error": "latitude/longitude or lat/long required"}, 400)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO readers (name, latitude, longitude) VALUES (%s, %s, %s)",
                    (name, float(lat), float(lon)),
                )
            except psycopg2.ProgrammingError:
                conn.rollback()
                cur.execute(
                    "INSERT INTO readers (reader_name, latitude, longitude) VALUES (%s, %s, %s)",
                    (name, float(lat), float(lon)),
                )
        conn.commit()
        return api_response({"name": name, "latitude": float(lat), "longitude": float(lon)}, 201)
    except psycopg2.IntegrityError as e:
        conn.rollback()
        if "unique" in str(e).lower():
            return api_response({"error": "Reader name already exists"}, 409)
        return api_response({"error": str(e)}, 400)
    finally:
        conn.close()


def update_reader(event, context):
    name = (event.get("pathParameters") or {}).get("readerName")
    if not name:
        return api_response({"error": "readerName required"}, 400)
    try:
        body = __import__("json").loads(event.get("body") or "{}")
    except Exception:
        return api_response({"error": "Invalid JSON"}, 400)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            if event.get("httpMethod") == "PUT":
                lat = body.get("latitude") if "latitude" in body else body.get("lat")
                lon = body.get("longitude") if "longitude" in body else body.get("long")
                if lat is None or lon is None:
                    return api_response({"error": "latitude and longitude required"}, 400)
                try:
                    cur.execute("UPDATE readers SET latitude = %s, longitude = %s WHERE name = %s", (float(lat), float(lon), name))
                except psycopg2.ProgrammingError:
                    conn.rollback()
                    cur.execute("UPDATE readers SET latitude = %s, longitude = %s WHERE reader_name = %s", (float(lat), float(lon), name))
            else:
                updates = []
                params = []
                if "latitude" in body:
                    updates.append("latitude = %s")
                    params.append(float(body["latitude"]))
                if "longitude" in body:
                    updates.append("longitude = %s")
                    params.append(float(body["longitude"]))
                if "name" in body and body["name"]:
                    updates.append("name = %s")
                    params.append((body.get("name") or "").strip())
                if not updates:
                    cur.execute("SELECT * FROM readers")
                    for r in cur.fetchall():
                        if r.get("name") == name or r.get("reader_name") == name:
                            return api_response(_reader_row(r))
                    return api_response({"error": "Not found"}, 404)
                params.append(name)
                try:
                    cur.execute("UPDATE readers SET " + ", ".join(updates) + " WHERE name = %s", params)
                except psycopg2.ProgrammingError:
                    conn.rollback()
                    cur.execute("UPDATE readers SET " + ", ".join(updates).replace("name = %s", "reader_name = %s") + " WHERE reader_name = %s", params[:-1] + [name])
            cur.execute("SELECT * FROM readers")
            row = None
            for r in cur.fetchall():
                if r.get("name") == name or r.get("reader_name") == name:
                    row = r
                    break
        conn.commit()
        if not row:
            return api_response({"error": "Not found"}, 404)
        return api_response(_reader_row(row))
    except Exception as e:
        conn.rollback()
        return api_response({"error": str(e)}, 400)
    finally:
        conn.close()


def delete_reader(event, context):
    name = (event.get("pathParameters") or {}).get("readerName")
    if not name:
        return api_response({"error": "readerName required"}, 400)
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            try:
                cur.execute("DELETE FROM readers WHERE name = %s", (name,))
            except psycopg2.ProgrammingError:
                conn.rollback()
                cur.execute("DELETE FROM readers WHERE reader_name = %s", (name,))
            deleted = cur.rowcount
        conn.commit()
        if deleted == 0:
            return api_response({"error": "Not found"}, 404)
        return api_response({"ok": True}, 200)
    finally:
        conn.close()
