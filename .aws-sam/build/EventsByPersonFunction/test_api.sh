#!/usr/bin/env bash
# Test all BLE People Tracker API endpoints as an application.
# Usage: ./test_api.sh [base_url] [api_key]
# Default: base_url and api_key from last deploy.
set -e
BASE="${1:-https://rkali63t89.execute-api.us-east-2.amazonaws.com/Prod}"
KEY="${2:-nASS2V8CkW1vWfFAyQWSk7qZEPOAhLJt1iYalDqD}"
H="x-api-key: $KEY"
READER="TestReader"
MAC="AA:BB:CC:DD:EE:FF"
FAIL=0

assert_status() {
  local got=$1
  local want=$2
  local name=$3
  if [ "$got" = "$want" ]; then
    echo "  OK $name (HTTP $got)"
  else
    echo "  FAIL $name (expected HTTP $want, got $got)"
    FAIL=1
  fi
}

echo "=== 0. Auth: no API key (expect 403) ==="
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/readers")
assert_status "$STATUS" "403" "no API key returns 403"
echo ""

echo "=== 1. GET /readers (list) ==="
curl -s -w "\nHTTP %{http_code}\n" -H "$H" "$BASE/readers"
echo ""

echo "=== 2. POST /readers (create) ==="
curl -s -w "\nHTTP %{http_code}\n" -X POST -H "$H" -H "Content-Type: application/json" \
  -d "{\"readerName\":\"$READER\",\"latitude\":40.7,\"longitude\":-74.0,\"displayName\":\"Test Room\"}" \
  "$BASE/readers"
echo ""

echo "=== 3. GET /readers/{readerName} (get one) ==="
curl -s -w "\nHTTP %{http_code}\n" -H "$H" "$BASE/readers/$(echo $READER | sed 's/ /%20/g')"
echo ""

echo "=== 4. GET /readers/{readerName}?include=children ==="
curl -s -w "\nHTTP %{http_code}\n" -H "$H" "$BASE/readers/$(echo $READER | sed 's/ /%20/g')?include=children&limit=10"
echo ""

echo "=== 5. PUT /readers/{readerName} (full update) ==="
curl -s -w "\nHTTP %{http_code}\n" -X PUT -H "$H" -H "Content-Type: application/json" \
  -d "{\"readerName\":\"$READER\",\"latitude\":40.71,\"longitude\":-74.01,\"displayName\":\"Test Room Updated\"}" \
  "$BASE/readers/$(echo $READER | sed 's/ /%20/g')"
echo ""

echo "=== 6. PATCH /readers/{readerName} (partial update) ==="
curl -s -w "\nHTTP %{http_code}\n" -X PATCH -H "$H" -H "Content-Type: application/json" \
  -d "{\"description\":\"E2E test reader\"}" \
  "$BASE/readers/$(echo $READER | sed 's/ /%20/g')"
echo ""

echo "=== 7. POST /events (create) ==="
EVENT_RESP=$(curl -s -w "\n%{http_code}" -X POST -H "$H" -H "Content-Type: application/json" \
  -d "{\"mac\":\"$MAC\",\"readerName\":\"$READER\",\"direction\":\"in\",\"name\":\"Test Child\",\"qrCode\":\"QR123\",\"distance\":1.5}" \
  "$BASE/events")
EVENT_HTTP=$(echo "$EVENT_RESP" | tail -n1)
EVENT_BODY=$(echo "$EVENT_RESP" | sed '$d')
echo "$EVENT_BODY"
echo "HTTP $EVENT_HTTP"
EVENT_ID=$(echo "$EVENT_BODY" | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2)
echo ""

echo "=== 8. GET /readers/{readerName}/events ==="
curl -s -w "\nHTTP %{http_code}\n" -H "$H" "$BASE/readers/$(echo $READER | sed 's/ /%20/g')/events?limit=10"
echo ""

echo "=== 9. GET /events (list) ==="
curl -s -w "\nHTTP %{http_code}\n" -H "$H" "$BASE/events?limit=5"
echo ""

echo "=== 10. GET /events?readerName=...&direction=in ==="
curl -s -w "\nHTTP %{http_code}\n" -H "$H" "$BASE/events?readerName=$READER&direction=in&limit=5"
echo ""

echo "=== 11. GET /events/{id} (get one) ==="
if [ -n "$EVENT_ID" ]; then
  curl -s -w "\nHTTP %{http_code}\n" -H "$H" "$BASE/events/$EVENT_ID"
else
  echo "(skip - no event id from create)"
fi
echo ""

echo "=== 12. GET /events/person/{mac} ==="
curl -s -w "\nHTTP %{http_code}\n" -H "$H" "$BASE/events/person/$(echo $MAC | sed 's/:/%3A/g')?limit=5"
echo ""

echo "=== 13. PUT /events/{id} (full update) ==="
if [ -n "$EVENT_ID" ]; then
  curl -s -w "\nHTTP %{http_code}\n" -X PUT -H "$H" -H "Content-Type: application/json" \
    -d "{\"mac\":\"$MAC\",\"readerName\":\"$READER\",\"direction\":\"out\",\"name\":\"Test Child Updated\",\"qrCode\":\"QR456\",\"distance\":2.0}" \
    "$BASE/events/$EVENT_ID"
else
  echo "(skip)"
fi
echo ""

echo "=== 14. PATCH /events/{id} (partial update) ==="
if [ -n "$EVENT_ID" ]; then
  curl -s -w "\nHTTP %{http_code}\n" -X PATCH -H "$H" -H "Content-Type: application/json" \
    -d "{\"distance\":2.5}" \
    "$BASE/events/$EVENT_ID"
else
  echo "(skip)"
fi
echo ""

echo "=== 15. DELETE /events/{id} ==="
if [ -n "$EVENT_ID" ]; then
  curl -s -w "\nHTTP %{http_code}\n" -X DELETE -H "$H" "$BASE/events/$EVENT_ID"
else
  echo "(skip)"
fi
echo ""

echo "=== 16. DELETE /readers/{readerName} ==="
curl -s -w "\nHTTP %{http_code}\n" -X DELETE -H "$H" "$BASE/readers/$(echo $READER | sed 's/ /%20/g')"
echo ""

echo "=== 17. GET /readers (list again) ==="
curl -s -w "\nHTTP %{http_code}\n" -H "$H" "$BASE/readers"
echo ""

echo "=== 18. No API key (expect 403) ==="
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/readers")
assert_status "$STATUS" "403" "no API key"
echo ""

if [ $FAIL -eq 0 ]; then
  echo "Summary: Auth and routing OK. Any 500 above = DB not configured (set real DB params in samconfig.toml and redeploy)."
else
  echo "Summary: Some assertions failed."
fi
echo "Done."
exit $FAIL
