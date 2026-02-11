"""Test all API handlers with a mocked DB so tests run with no external services."""
import json
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock


def make_cursor(rows):
    """Cursor that returns rows on fetchone/fetchall. fetchone returns first row then None."""
    cur = MagicMock()
    cur.__enter__ = lambda self: self
    cur.__exit__ = lambda *a: None
    _rows = list(rows)
    _idx = [0]

    def fetchone():
        if _idx[0] >= len(_rows):
            return None
        r = _rows[_idx[0]]
        _idx[0] += 1
        return r if isinstance(r, dict) else dict(r)

    def fetchall():
        return [r if isinstance(r, dict) else dict(r) for r in _rows[_idx[0]:]]

    cur.fetchone = fetchone
    cur.fetchall = fetchall
    cur.execute = MagicMock()
    return cur


def make_conn(cursor):
    """Connection that returns the given cursor from cursor()."""
    conn = MagicMock()
    conn.cursor.return_value = cursor
    conn.commit = MagicMock()
    conn.rollback = MagicMock()
    conn.closed = 0
    return conn


def mock_get_conn(rows_for_cursor):
    """Patch get_conn to yield a connection that returns the given rows."""
    cursor = make_cursor(rows_for_cursor)
    conn = make_conn(cursor)
    cm = MagicMock()
    cm.__enter__.return_value = conn
    cm.__exit__.return_value = None
    return cm


class TestReadersAPI(unittest.TestCase):
    def setUp(self):
        self.reader_row = {
            "reader_name": "Room1",
            "display_name": "Room One",
            "description": None,
            "latitude": 40.7,
            "longitude": -74.0,
            "created_at": datetime(2025, 1, 1),
            "updated_at": datetime(2025, 1, 1),
        }

    def test_list_readers_empty(self):
        from src.handlers import readers
        with patch("src.handlers.readers.get_conn", return_value=mock_get_conn([])):
            r = readers.list_readers({"queryStringParameters": None}, None)
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(json.loads(r["body"]), [])

    def test_list_readers_one(self):
        from src.handlers import readers
        with patch("src.handlers.readers.get_conn", return_value=mock_get_conn([self.reader_row])):
            r = readers.list_readers({"queryStringParameters": None}, None)
        self.assertEqual(r["statusCode"], 200)
        data = json.loads(r["body"])
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["readerName"], "Room1")
        self.assertEqual(data[0]["latitude"], 40.7)

    def test_get_reader_missing_name(self):
        from src.handlers import readers
        r = readers.get_reader({"pathParameters": {}}, None)
        self.assertEqual(r["statusCode"], 400)

    def test_get_reader_not_found(self):
        from src.handlers import readers
        with patch("src.handlers.readers.get_conn", return_value=mock_get_conn([])):
            r = readers.get_reader({"pathParameters": {"readerName": "X"}}, None)
        self.assertEqual(r["statusCode"], 404)

    def test_get_reader_ok(self):
        from src.handlers import readers
        with patch("src.handlers.readers.get_conn", return_value=mock_get_conn([self.reader_row])):
            r = readers.get_reader({"pathParameters": {"readerName": "Room1"}}, None)
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(json.loads(r["body"])["readerName"], "Room1")

    def test_create_reader_missing_body(self):
        from src.handlers import readers
        r = readers.create_reader({"body": ""}, None)
        self.assertEqual(r["statusCode"], 400)

    def test_create_reader_missing_lat_lng(self):
        from src.handlers import readers
        r = readers.create_reader({"body": json.dumps({"readerName": "R"})}, None)
        self.assertEqual(r["statusCode"], 400)

    def test_create_reader_ok(self):
        from src.handlers import readers
        body = {"readerName": "R", "latitude": 1.0, "longitude": 2.0}
        with patch("src.handlers.readers.get_conn", return_value=mock_get_conn([self.reader_row])):
            r = readers.create_reader({"body": json.dumps(body)}, None)
        self.assertEqual(r["statusCode"], 201)
        self.assertEqual(json.loads(r["body"])["readerName"], "Room1")

    def test_update_reader_ok(self):
        from src.handlers import readers
        with patch("src.handlers.readers.get_conn", return_value=mock_get_conn([self.reader_row, self.reader_row])):
            r = readers.update_reader({
                "pathParameters": {"readerName": "Room1"},
                "body": json.dumps({"latitude": 41.0}),
            }, None)
        self.assertEqual(r["statusCode"], 200)

    def test_delete_reader_not_found(self):
        from src.handlers import readers
        with patch("src.handlers.readers.get_conn", return_value=mock_get_conn([])):
            r = readers.delete_reader({"pathParameters": {"readerName": "X"}}, None)
        self.assertEqual(r["statusCode"], 404)

    def test_delete_reader_ok(self):
        from src.handlers import readers
        with patch("src.handlers.readers.get_conn", return_value=mock_get_conn([{"reader_name": "Room1"}])):
            r = readers.delete_reader({"pathParameters": {"readerName": "Room1"}}, None)
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(json.loads(r["body"])["deleted"], "Room1")


class TestEventsAPI(unittest.TestCase):
    def setUp(self):
        self.event_row = {
            "id": 1,
            "mac": "AA:BB:CC:DD:EE:FF",
            "name": "Child1",
            "qr_code": "QR1",
            "direction": "in",
            "distance": 1.5,
            "data": None,
            "antenna": 1,
            "peak_rssi": -70,
            "date_time": datetime(2025, 1, 1, 12, 0),
            "reader_name": "Room1",
            "start_event": None,
            "count": None,
            "tag_event": None,
            "uuid": None,
            "major": None,
            "minor": None,
            "namespace": None,
            "instance": None,
            "voltage": None,
            "temperature": None,
            "url": None,
            "created_at": datetime(2025, 1, 1),
        }

    def test_list_events_empty(self):
        from src.handlers import events
        with patch("src.handlers.events.get_conn", return_value=mock_get_conn([])):
            r = events.list_events({"queryStringParameters": None}, None)
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(json.loads(r["body"]), [])

    def test_list_events_direction_invalid(self):
        from src.handlers import events
        r = events.list_events({"queryStringParameters": {"direction": "bad"}}, None)
        self.assertEqual(r["statusCode"], 400)

    def test_list_events_ok(self):
        from src.handlers import events
        with patch("src.handlers.events.get_conn", return_value=mock_get_conn([self.event_row])):
            r = events.list_events({"queryStringParameters": {}}, None)
        self.assertEqual(r["statusCode"], 200)
        data = json.loads(r["body"])
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["mac"], "AA:BB:CC:DD:EE:FF")
        self.assertEqual(data[0]["name"], "Child1")
        self.assertEqual(data[0]["qrCode"], "QR1")

    def test_get_event_not_found(self):
        from src.handlers import events
        with patch("src.handlers.events.get_conn", return_value=mock_get_conn([])):
            r = events.get_event({"pathParameters": {"id": "999"}}, None)
        self.assertEqual(r["statusCode"], 404)

    def test_get_event_ok(self):
        from src.handlers import events
        with patch("src.handlers.events.get_conn", return_value=mock_get_conn([self.event_row])):
            r = events.get_event({"pathParameters": {"id": "1"}}, None)
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(json.loads(r["body"])["id"], 1)

    def test_create_event_missing_mac(self):
        from src.handlers import events
        r = events.create_event({"body": json.dumps({"readerName": "R"})}, None)
        self.assertEqual(r["statusCode"], 400)

    def test_create_event_missing_reader(self):
        from src.handlers import events
        r = events.create_event({"body": json.dumps({"mac": "AA:BB:CC:DD:EE:FF"})}, None)
        self.assertEqual(r["statusCode"], 400)

    def test_create_event_ok(self):
        from src.handlers import events
        body = {"mac": "AA:BB:CC:DD:EE:FF", "readerName": "Room1", "name": "Test", "qrCode": "Q"}
        with patch("src.handlers.events.get_conn", return_value=mock_get_conn([self.event_row])):
            r = events.create_event({"body": json.dumps(body)}, None)
        self.assertEqual(r["statusCode"], 201)
        self.assertEqual(json.loads(r["body"])["mac"], "AA:BB:CC:DD:EE:FF")

    def test_update_event_partial_ok(self):
        from src.handlers import events
        updated = dict(self.event_row)
        updated["distance"] = 2.5
        with patch("src.handlers.events.get_conn", return_value=mock_get_conn([self.event_row, updated])):
            r = events.update_event({
                "pathParameters": {"id": "1"},
                "body": json.dumps({"distance": 2.5}),
            }, None)
        self.assertEqual(r["statusCode"], 200)

    def test_delete_event_not_found(self):
        from src.handlers import events
        with patch("src.handlers.events.get_conn", return_value=mock_get_conn([])):
            r = events.delete_event({"pathParameters": {"id": "999"}}, None)
        self.assertEqual(r["statusCode"], 404)

    def test_delete_event_ok(self):
        from src.handlers import events
        with patch("src.handlers.events.get_conn", return_value=mock_get_conn([{"id": 1, "mac": "AA:BB:CC:DD:EE:FF", "reader_name": "Room1"}])):
            r = events.delete_event({"pathParameters": {"id": "1"}}, None)
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(json.loads(r["body"])["deleted"], 1)

    def test_list_reader_events_ok(self):
        from src.handlers import events
        # list_reader_events does fetchone() for reader check, then fetchall() for events
        with patch("src.handlers.events.get_conn", return_value=mock_get_conn([{"1": 1}, self.event_row])):
            r = events.list_reader_events({"pathParameters": {"readerName": "Room1"}, "queryStringParameters": {}}, None)
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(len(json.loads(r["body"])), 1)

    def test_list_events_by_person_ok(self):
        from src.handlers import events
        with patch("src.handlers.events.get_conn", return_value=mock_get_conn([self.event_row])):
            r = events.list_events_by_mac({"pathParameters": {"mac": "AA:BB:CC:DD:EE:FF"}, "queryStringParameters": {}}, None)
        self.assertEqual(r["statusCode"], 200)
        self.assertEqual(len(json.loads(r["body"])), 1)


if __name__ == "__main__":
    unittest.main()
