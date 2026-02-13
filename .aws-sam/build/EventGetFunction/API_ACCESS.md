# Accessing the BLE People Tracker API

You need **two values** to call the API:

1. **Base URL** – e.g. `https://rkali63t89.execute-api.us-east-2.amazonaws.com/Prod`
2. **API key** – send in the **`x-api-key`** header on every requests

---

## Get URL and API key from your deployed stack

**Base URL** (from stack output):

```bash
aws cloudformation describe-stacks --stack-name ble-people-tracker --region us-east-2 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' --output text
```

**API key value** (requires the key ID from the same stack):

```bash
# Get key ID, then key value:
KEY_ID=$(aws cloudformation describe-stacks --stack-name ble-people-tracker --region us-east-2 \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiKeyId`].OutputValue' --output text)
aws apigateway get-api-key --api-key "$KEY_ID" --include-value --region us-east-2 --query 'value' --output text
```

Or in **API Gateway console**: API keys → find the key (use **ApiKeyId** from stack outputs) → **Show** to reveal the value.

---

## Example: call the API

Replace `YOUR_BASE_URL` and `YOUR_API_KEY` with the values above.

**List readers:**

```bash
curl -s -H "x-api-key: YOUR_API_KEY" "YOUR_BASE_URL/readers"
```

**Create a reader:**

```bash
curl -s -X POST -H "x-api-key: YOUR_API_KEY" -H "Content-Type: application/json" \
  -d '{"readerName":"Room1","latitude":40.7,"longitude":-74.0,"displayName":"Lobby"}' \
  "YOUR_BASE_URL/readers"
```

**Create an event (child at reader):**

```bash
curl -s -X POST -H "x-api-key: YOUR_API_KEY" -H "Content-Type: application/json" \
  -d '{"mac":"AA:BB:CC:DD:EE:01","readerName":"Room1","direction":"in","name":"Alice"}' \
  "YOUR_BASE_URL/events"
```

**Filter events by direction (in / out):**

- All events, only "in": `GET /events?direction=in`
- All events, only "out": `GET /events?direction=out`
- Events at a reader, only "in": `GET /readers/Lobby-01/events?direction=in`
- Events at a reader, only "out": `GET /readers/Lobby-01/events?direction=out`
- Events for a MAC (person), only "in": `GET /events/person/AA:BB:CC:DD:EE:01?direction=in`

```bash
curl -s -H "x-api-key: YOUR_API_KEY" "YOUR_BASE_URL/events?direction=in"
curl -s -H "x-api-key: YOUR_API_KEY" "YOUR_BASE_URL/readers/Lobby-01/events?direction=out"
```

---

## In your application

- **Base URL:** use the **ApiUrl** from your stack (with or without trailing slash).
- **Every request:** add header **`x-api-key: <your API key value>`**.
- **JSON:** use **`Content-Type: application/json`** for POST/PUT/PATCH bodies.

Without a valid `x-api-key` header, the API returns **403 Forbidden**.
