# Full API reference for applications

Everything an application needs to call all endpoints.

---

## 1. Base URL and API key

| Item | Value |
|------|--------|
| **Base URL** | `https://rkali63t89.execute-api.us-east-2.amazonaws.com/Prod` |
| **API key** | `MlzzVbn4og1AN93aBra5pa9OTKZs716j35uFuV1I` |

---

## 2. Headers (every request)

| Header | Value | When |
|--------|--------|------|
| **x-api-key** | Your API key (above) | **Required on every request.** Without it → 403. |
| **Content-Type** | `application/json` | Required for POST, PUT, PATCH bodies. |
| **Authorization** | `Bearer <session-token>` | Required for `/auth/me` and `/auth/logout` (token from login). |

---

## 3. All endpoints

### Readers

| Method | Path | Description | Body / Query |
|--------|------|-------------|--------------|
| GET | `/readers` | List all readers | — |
| GET | `/readers/{readerName}` | Get one reader | — |
| POST | `/readers` | Create reader | `reader_name`, `latitude`, `longitude`; optional: `display_name` |
| PUT | `/readers/{readerName}` | Full update reader | `latitude`, `longitude`; optional: `name`, `display_name` |
| PATCH | `/readers/{readerName}` | Partial update reader | any of: `latitude`, `longitude`, `name`, `display_name` |
| DELETE | `/readers/{readerName}` | Delete reader | — |
| GET | `/readers/{readerName}/events` | List events at reader (children) | Optional query: `?direction=in` or `?direction=out` |

### Events

| Method | Path | Description | Body / Query |
|--------|------|-------------|--------------|
| GET | `/events` | List all events | Optional: `?direction=in` or `?direction=out` |
| GET | `/events/{id}` | Get one event | — |
| GET | `/events/person/{mac}` | List events for person (MAC) | Optional: `?direction=in` or `?direction=out` |
| POST | `/events` | Create event | Required: `reader_name`, `mac`. Optional: `direction`, `name`, etc. |
| PUT | `/events/{id}` | Full update event | fields to update |
| PATCH | `/events/{id}` | Partial update event | any event fields |
| DELETE | `/events/{id}` | Delete event | — |

### Auth (users & login)

| Method | Path | Description | Body | Extra headers |
|--------|------|-------------|------|----------------|
| POST | `/auth/register` | Create user | `username`, `password`; optional: `email` | — |
| POST | `/auth/login` | Log in | `username`, `password` | — |
| GET | `/auth/me` | Current user | — | **Authorization: Bearer &lt;token&gt;** |
| POST | `/auth/logout` | Log out (invalidate session) | — | **Authorization: Bearer &lt;token&gt;** |
| POST | `/auth/password-reset/request` | Request password reset | `email` or `username` | — |
| POST | `/auth/password-reset/confirm` | Set new password with reset token | `token`, `new_password` | — |

---

## 4. Request body examples (JSON)

**Readers**
- Create: `{"reader_name": "Lobby-01", "latitude": 40.71, "longitude": -74.01, "display_name": "Main Lobby"}`

**Events**
- Create: `{"mac": "AA:BB:CC:DD:EE:01", "reader_name": "Lobby-01", "direction": "in", "name": "Alice"}`

**Auth**
- Register: `{"username": "alice", "password": "YourPassword", "email": "alice@example.com"}`
- Login: `{"username": "alice", "password": "YourPassword"}`
- Password reset request: `{"email": "alice@example.com"}` or `{"username": "alice"}`
- Password reset confirm: `{"token": "<reset-token>", "new_password": "NewPassword"}`

---

## 5. Typical response shapes

- **Readers list:** `{"readers": [{ "reader_name", "latitude", "longitude", "display_name", "created_at", "updated_at" }]}`
- **Events list:** `{"events": [{ "id", "mac", "reader_name", "direction", "name", "date_time", "created_at", ... }]}`
- **Login:** `{"user": { "id", "username", "email", "created_at" }, "token": "...", "expires_at": "..."}`
- **Auth me:** `{"user": { "id", "username", "email", "created_at" }}`
- **Errors:** `{"error": "message"}` with status 4xx/5xx

---

## 6. Test user (for QA / demos)

You can use this built-in test account:

| Field | Value |
|--------|--------|
| **Username** | `testuser2` |
| **Password** | `TestPass123!` |
| **Email** | `testuser2@example.com` |

Login body:
```json
{"username": "testuser2", "password": "TestPass123!"}
```

---

## 7. App config (copy-paste)

```env
BLE_API_URL=https://rkali63t89.execute-api.us-east-2.amazonaws.com/Prod
BLE_API_KEY=MlzzVbn4og1AN93aBra5pa9OTKZs716j35uFuV1I
```

**Usage in code:**
- Every request: add header `x-api-key: <BLE_API_KEY>`.
- After login: store `token`; for `/auth/me` and `/auth/logout` add `Authorization: Bearer <token>`.
- POST/PUT/PATCH: set `Content-Type: application/json` and send JSON body.

---

## 8. Quick cURL examples

```bash
# Readers
curl -s -H "x-api-key: $BLE_API_KEY" "$BLE_API_URL/readers"
curl -s -X POST -H "x-api-key: $BLE_API_KEY" -H "Content-Type: application/json" \
  -d '{"reader_name":"Lobby-01","latitude":40.71,"longitude":-74.01}' "$BLE_API_URL/readers"

# Events
curl -s -H "x-api-key: $BLE_API_KEY" "$BLE_API_URL/events?direction=in"
curl -s -X POST -H "x-api-key: $BLE_API_KEY" -H "Content-Type: application/json" \
  -d '{"mac":"AA:BB:CC:DD:EE:01","reader_name":"Lobby-01","direction":"in","name":"Alice"}' "$BLE_API_URL/events"

# Auth
curl -s -X POST -H "x-api-key: $BLE_API_KEY" -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"secret"}' "$BLE_API_URL/auth/login"
# Then use returned token:
curl -s -H "x-api-key: $BLE_API_KEY" -H "Authorization: Bearer <TOKEN>" "$BLE_API_URL/auth/me"
```

---

This is the full info needed for an application to use all endpoints.
