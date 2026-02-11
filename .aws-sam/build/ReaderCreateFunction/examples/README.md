# BLE People Tracker – Example Application

A small web app that uses the BLE People Tracker API: manage **readers** (static locations with lat/long) and **events** (MAC in/out per reader with the full payload).

## What it does

- **Readers** – List, add, edit, and delete readers. Each has `readerName`, optional `displayName`/`description`, and `latitude`/`longitude` for map placement. **A reader can have multiple child MAC addresses** (one-to-many).
- **Events** – Each event is one MAC (child) at one reader. List events filtered by reader and direction (in/out). Add and edit events with the full payload. Readers can have multiple child MAC addresses; each event is tied to one reader via `readerName`.

## How to run

1. Deploy the BLE API (see project root README) and note the API base URL (e.g. `https://xxxx.execute-api.us-east-2.amazonaws.com/Prod`).

2. Open the example app:
   - **Option A:** Open `app/index.html` in a browser (file://). Set the **API base URL** at the top and click Save. If the browser blocks cross-origin requests to the API, use Option B.
   - **Option B:** Serve the folder over HTTP, then open the URL in the browser:
     ```bash
     cd examples/app
     python3 -m http.server 8080
     ```
     Open http://localhost:8080 . Set the API base URL and click Save.

3. Use **Readers** to add/edit static readers (e.g. Lobby, Room 101) with lat/long. Use **Events** to add/edit MAC in/out at a reader with the full payload.

## Files

- `app/index.html` – Markup and modals for readers and events.
- `app/styles.css` – Layout and theme.
- `app/app.js` – API calls (fetch), list/add/edit/delete for readers and events.

The app stores the API base URL in `localStorage` so you only set it once per browser.

**Real-time editing:** All values are editable in real time. For single-field updates (e.g. user changes only distance), call **PATCH** instead of PUT with a partial body: `PATCH /readers/{readerName}` with `{"latitude": 40.72}` or `PATCH /events/{id}` with `{"distance": 1.5}`. The API accepts only the fields that changed.
