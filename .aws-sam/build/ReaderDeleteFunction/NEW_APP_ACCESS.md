# New app – everything needed to access the BLE People Tracker API

## 1. Base URL
```
https://rkali63t89.execute-api.us-east-2.amazonaws.com/Prod
```
Use with or without a trailing slash.

---

## 2. API key (for this app)
```
MlzzVbn4og1AN93aBra5pa9OTKZs716j35uFuV1I
```
Store in config/env (e.g. `BLE_API_KEY`). Do not commit to source control.

---

## 3. Authentication
Send the API key on **every request** in the header:
```
x-api-key: MlzzVbn4og1AN93aBra5pa9OTKZs716j35uFuV1I
```

Without a valid key, the API returns **403 Forbidden**.

---

## 4. Content type
For POST, PUT, and PATCH: send JSON with header:
```
Content-Type: application/json
```

---

## 5. Endpoints

| What you need | Method | Path |
|---------------|--------|------|
| List all readers | GET | `/readers` |
| Get one reader | GET | `/readers/{readerName}` |
| Create reader | POST | `/readers` |
| Update reader | PATCH | `/readers/{readerName}` |
| Delete reader | DELETE | `/readers/{readerName}` |
| List all events (children) | GET | `/events` |
| List events at a reader (reader’s children) | GET | `/readers/{readerName}/events` |
| Filter events by direction | GET | `/events?direction=in` or `?direction=out` |
| Same filter at one reader | GET | `/readers/{readerName}/events?direction=in` |
| Events for one person (MAC) | GET | `/events/person/{mac}` |
| Create event | POST | `/events` |
| Get one event | GET | `/events/{id}` |
| Update event | PATCH | `/events/{id}` |
| Delete event | DELETE | `/events/{id}` |
| **Register user** | POST | `/auth/register` |
| **Login** | POST | `/auth/login` |
| **Get current user** | GET | `/auth/me` (header: `Authorization: Bearer <token>`) |
| **Logout** | POST | `/auth/logout` (header: `Authorization: Bearer <token>`) |
| **Request password reset** | POST | `/auth/password-reset/request` |
| **Confirm password reset** | POST | `/auth/password-reset/confirm` |

---

## 6. Example: list readers with children
1. **GET** `{baseUrl}/readers` → list of readers.
2. For each reader, **GET** `{baseUrl}/readers/{reader_name}/events` → that reader’s events (children).

---

## 7. Example request bodies

**Create reader (POST /readers):**
```json
{"reader_name": "Lobby-01", "latitude": 40.71, "longitude": -74.01, "display_name": "Main Lobby"}
```
Use `reader_name` or `name`; `latitude`/`longitude` required.

**Create event (POST /events):**
```json
{"mac": "AA:BB:CC:DD:EE:01", "reader_name": "Lobby-01", "direction": "in", "name": "Alice"}
```
Required: `reader_name`, `mac`. Optional: `direction` (in/out), `name`.

**Register (POST /auth/register):**
```json
{"username": "alice", "password": "YourSecurePassword", "email": "alice@example.com"}
```
`email` is optional.

**Login (POST /auth/login):**
```json
{"username": "alice", "password": "YourSecurePassword"}
```
Returns `user`, `token`, and `expires_at`. Use the `token` in the `Authorization: Bearer <token>` header for `/auth/me` and `/auth/logout`.

**Request password reset (POST /auth/password-reset/request):**
```json
{"email": "alice@example.com"}
```
or `{"username": "alice"}`. Creates a reset token (valid 1 hour). In production you would send the token by email; for testing the API can return it if configured.

**Confirm password reset (POST /auth/password-reset/confirm):**
```json
{"token": "<reset-token>", "new_password": "NewSecurePassword"}
```
Updates the user's password and invalidates the reset token.

---

## 8. Copy-paste for your app config

```env
BLE_API_URL=https://rkali63t89.execute-api.us-east-2.amazonaws.com/Prod
BLE_API_KEY=MlzzVbn4og1AN93aBra5pa9OTKZs716j35uFuV1I
```

**cURL examples:**
```bash
# List readers
curl -s -H "x-api-key: $BLE_API_KEY" "$BLE_API_URL/readers"

# List events at a reader
curl -s -H "x-api-key: $BLE_API_KEY" "$BLE_API_URL/readers/Lobby-01/events"

# List only "in" events
curl -s -H "x-api-key: $BLE_API_KEY" "$BLE_API_URL/events?direction=in"
```

---

This is everything a new app needs to access the API.
