# 3rd Party API Test – URL and Token

Use this **URL** and **token** so your application can call our API for testing.

---

## What you need

| Field   | Description |
|--------|-------------|
| **URL**   | Base URL of the API (e.g. `https://xxxx.execute-api.us-east-2.amazonaws.com/Prod`) |
| **Token** | Secret token – send it on **every** request |

Your contact will give you a file (e.g. `third_party_api_access.env`) or a secure message with the exact **URL** and **Token** values.

---

## How to use in your application

1. **Base URL** – Use the **URL** as the root for all API calls.  
   Example: `GET {URL}/readers`, `POST {URL}/events`, `GET {URL}/readers/{readerName}/events`.

2. **Token** – On **every** HTTP request, send the token in the header:
   ```http
   x-api-key: <your token value>
   ```

**Example (curl):**
```bash
curl -s -H "x-api-key: YOUR_TOKEN_HERE" "https://YOUR_URL_HERE/readers"
```

**Example (create a reader):**
```bash
curl -s -X POST -H "x-api-key: YOUR_TOKEN_HERE" -H "Content-Type: application/json" \
  -d '{"readerName":"Room1","latitude":40.7,"longitude":-74.0,"displayName":"Lobby"}' \
  "https://YOUR_URL_HERE/readers"
```

---

## Endpoints (full access)

- **Readers:** `GET/POST /readers`, `GET/PUT/PATCH/DELETE /readers/{readerName}`, `GET /readers/{readerName}/events`
- **Events:** `GET/POST /events`, `GET/PUT/PATCH/DELETE /events/{id}`, `GET /events/person/{mac}`

Use **Content-Type: application/json** for POST, PUT, and PATCH with a JSON body.

---

## Summary

- **URL** = API base URL  
- **Token** = send as header **`x-api-key`** on every request  
- No AWS or CLI required – only the URL and token.
