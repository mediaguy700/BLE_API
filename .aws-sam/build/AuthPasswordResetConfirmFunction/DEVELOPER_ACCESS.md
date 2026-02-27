# BLE People Tracker API – Developer Access

**Hand this page to developers.** They only need a **URL** and a **key**—no AWS or CLI.

---

## Static URL and API key (2 weeks, full access)

You can get a **static URL and API key** that work for **2 weeks** and have **full access** to the API (all readers and events endpoints). Your admin will give you a file (e.g. `static-2week-api-access.env`) or a paste with:

| What you need | Description |
|---------------|-------------|
| **URL** | Base URL of the API (does not change for 2 weeks) |
| **Key** | **Static API key** – same value every time; send in the **`x-api-key`** header on every request |

**Static key:** The API key value does not change between handouts; developers always get the same key until the admin refreshes it. **Full functionality:** Same key works for all endpoints (readers and events: list, get, create, update, patch, delete, filters). Valid for 2 weeks; after that request a new key from your admin.

---

## Using your URL and key

Developers need **two values**:

| What you need | Example |
|---------------|--------|
| **URL** | `https://xxxx.execute-api.us-east-2.amazonaws.com/Prod` |
| **Key** | A long string (API key) |

**How to use:** Send the key in the **`x-api-key`** header on every request to the URL above.

---

## For developers: using your URL and key

Your admin will give you either:

- A **file** (e.g. `developer-credentials.env`) with `BASE_URL` and `API_KEY`, or  
- A **paste** with the URL and the key.

### Option 1: You have a credentials file (including static 2-week)

If you received a file like `static-2week-api-access.env` or `developer-credentials.env`:

```bash
# Contents look like:
# BASE_URL=https://xxxx.execute-api.us-east-2.amazonaws.com/Prod
# API_KEY=your_key_here
```

**In your app:** Load this file as environment variables (e.g. `dotenv` in Node, `python-dotenv` in Python, or your framework’s env loader). Then:

- Use **BASE_URL** as the base for all API calls (e.g. `BASE_URL/readers`, `BASE_URL/events`).
- On every HTTP request, add the header: **`x-api-key: <value of API_KEY>`**.

**Quick test (curl):**

```bash
# After loading BASE_URL and API_KEY from the file:
curl -s -H "x-api-key: $API_KEY" "$BASE_URL/readers"
```

### Option 2: You were given a URL and key (paste or message)

Use the **URL** as the base (e.g. `https://xxxx.execute-api.us-east-2.amazonaws.com/Prod`).  
Use the **key** as the value for the **`x-api-key`** header.

**Example:**

```bash
curl -s -H "x-api-key: YOUR_KEY_HERE" "https://YOUR_URL_HERE/readers"
```

**Example (create a reader):**

```bash
curl -s -X POST -H "x-api-key: YOUR_KEY_HERE" -H "Content-Type: application/json" \
  -d '{"readerName":"Room1","latitude":40.7,"longitude":-74.0,"displayName":"Lobby"}' \
  "https://YOUR_URL_HERE/readers"
```

---

## Summary for developers

- You only need a **URL** and a **key**.
- Send the key in the **`x-api-key`** header on **every** request.
- Use **Content-Type: application/json** for POST/PUT/PATCH with a JSON body.
- No AWS CLI or AWS console access is required.

---

## For admins: generating static URL + API key (2 weeks, full access)

To create a **static URL and API key** that developers can use for **2 weeks** with **full API access**, run:

```bash
./scripts/generate-developer-credentials.sh --static-2weeks
```

This creates **`static-2week-api-access.env`** with:
- **BASE_URL** – API base URL (static)
- **API_KEY** – API key (static for 2 weeks)
- **VALID_UNTIL** – date when the key should be rotated (2 weeks from generation)

Share this file (or its contents) with developers over a **secure channel**. They use the same **static** URL and key for all endpoints; no CLI or AWS access needed. The API key is cached so it stays the same every time you run the script. After 2 weeks, run with **`--refresh-key`** to get a new key and share the new file:

```bash
./scripts/generate-developer-credentials.sh --static-2weeks --refresh-key
```

**Standard credentials (no 2-week label):**

```bash
./scripts/generate-developer-credentials.sh
```
Creates **`developer-credentials.env`** with `BASE_URL` and `API_KEY`.

**Custom output path:**

```bash
./scripts/generate-developer-credentials.sh --static-2weeks path/to/static-2week.env
```

**3rd party applications (URL + token):** To give an external application a URL and token to test the API:

```bash
./scripts/generate-developer-credentials.sh --third-party
```

This creates **`third_party_api_access.env`** with **URL** and **TOKEN**. Share that file with the 3rd party; they send the token in the **`x-api-key`** header on every request. You can also share **THIRD_PARTY_ACCESS.md** as the one-page instructions for them.

Do not commit these files to git.
