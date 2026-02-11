# BLE People Tracker API

AWS API for a **people tracker** app: **readers** are static locations (lat/long on a map); **each reader can have multiple child MAC addresses** (one-to-many). Each reader is editable; each MAC is tracked in/out at that reader; readers and events are editable via the API.

## App logic

- **Readers** – Static locations with **latitude/longitude** for the map. Each reader can be **edited** (displayName, description, lat/long) via the API. Use readers as fixed points (rooms, zones, gates). **A reader has many child MAC addresses**: each event links one MAC to one reader.
- **MAC addresses (children of a reader)** – Each person is a MAC. **Readers can have multiple child MAC addresses**; each event is one MAC at one reader with a **direction** (`in` or `out`). The app tracks **in** (arrived at reader) and **out** (left reader). Events are **editable** (update or delete via API).
- **Map** – Use `GET /readers` for static reader positions (lat/long). Use `GET /events?readerName=X` (optionally `&direction=in` or `&direction=out`) to show who is in/out at each reader.

## Real-time editing (all values editable)

**Every field is editable in real time.** Use **PUT** or **PATCH** with a **partial body**: send only the field(s) that changed so your application can update a single value without resending the whole object.

- **Reader** – `PATCH /readers/{readerName}` or `PUT /readers/{readerName}` with body e.g. `{"latitude": 40.72}` or `{"displayName": "Lobby A"}`. Editable: `displayName`, `description`, `latitude`, `longitude`.
- **Child (event)** – `PATCH /events/{id}` or `PUT /events/{id}` with body e.g. `{"distance": 1.5}` or `{"peakRSSI": -68}`. Editable: all payload fields (mac, name, qrCode, distance, data, antenna, peakRSSI, dateTime, readerName, startEvent, count, tagEvent, uuid, major, minor, namespace, instance, voltage, temperature, url, direction). At least one field required in the body.

## Data model

| Concept | Description |
|--------|-------------|
| **Reader** | Static location; unique `readerName`; **latitude**, **longitude** for map; **editable**. **One reader has many child MAC addresses** (via events). |
| **Person (MAC)** | Identified by **MAC**. Each event links one MAC to one reader (child of that reader). Tracked **in/out**; events are **editable**. |

### Exposed fields (external API)

**Readers (static, editable)**

- `readerName` (unique id)
- `displayName`, `description` (optional)
- `latitude`, `longitude`

**Events (MAC in/out at reader; editable)**

- **Tracked payload** (all accepted on POST/PUT and returned on GET):

| Payload field | API JSON key   | Type     |
|---------------|----------------|----------|
| MAC           | `mac`          | string   |
| Name          | `name`         | string   |
| QR code       | `qrCode`       | string   |
| Distance      | `distance`     | number   |
| Data          | `data`         | string   |
| Antenna       | `antenna`      | integer  |
| PeakRSSI      | `peakRSSI`     | integer  |
| DateTime      | `dateTime`     | ISO8601  |
| ReaderName    | `readerName`   | string   |
| StartEvent    | `startEvent`   | boolean  |
| Count         | `count`        | integer  |
| TagEvent      | `tagEvent`     | string   |
| UUID          | `uuid`         | string   |
| Major         | `major`        | integer  |
| Minor         | `minor`        | integer  |
| Namespace     | `namespace`    | string   |
| Instance      | `instance`     | string   |
| Voltage       | `voltage`      | number   |
| Temperature   | `temperature`  | number   |
| URL           | `url`          | string   |

- **`direction`** – `"in"` or `"out"` (for app in/out at reader); optional, default `"in"`.
- **`id`**, **`createdAt`** – set by system.

## PostgreSQL setup

1. Create a PostgreSQL database (e.g. AWS RDS, Aurora, or local).
2. Run the schema:

```bash
psql -h <host> -U <user> -d <dbname> -f database/schema.sql
```

Or from your DB client, execute the contents of `database/schema.sql`.

**Tables**

- **readers** – `reader_name` (PK), `display_name`, `description`, `latitude`, `longitude` (static, editable)
- **events** – `mac`, `name`, `qr_code`, **`direction`** ('in'|'out'), other BLE fields; `reader_name` references `readers` (editable)

**Existing databases:** run migrations in order:

```bash
psql ... -f database/migrations/001_add_reader_display_and_description.sql
psql ... -f database/migrations/002_add_events_direction.sql
psql ... -f database/migrations/003_add_events_name_qr_code.sql
```

## API key

All requests require an **API key**. Send it in the **`x-api-key`** header:

```bash
curl -H "x-api-key: YOUR_API_KEY" "https://<api-id>.execute-api.<region>.amazonaws.com/Prod/readers"
```

Deploy creates a usage plan (**BLEPeopleTrackerUsagePlan**) and one API key. After deploy:

- **Get the key value:** In **API Gateway → API keys**, find the key by the **ApiKeyId** stack output (or by name). Use "Show" to reveal the key value. Or use the AWS CLI: `aws apigateway get-api-key --api-key <ApiKeyId> --include-value`.
- **Create more keys:** In API Gateway, create a new API key and add it to the **BLEPeopleTrackerUsagePlan** (or use the **UsagePlanId** stack output).

## Performance (high call volume)

The API is tuned for being called frequently:

- **Connection reuse** – Each Lambda container reuses a single PostgreSQL connection across invocations instead of opening a new one per request. Connections are re-established automatically if the server closed them (e.g. idle timeout).
- **Lambda** – Functions use 512 MB memory for better CPU and lower latency.
- **Usage plan** – Throttle is set to 500 requests/second steady, 1000 burst so high call rates are allowed without 429s. Adjust in `template.yaml` under `Globals.Api.Auth.UsagePlan.Throttle` if needed.

For very high throughput or many concurrent Lambdas, consider **RDS Proxy** in front of PostgreSQL to pool database connections.

## API (AWS API Gateway + Lambda)

Base URL after deploy: `https://<api-id>.execute-api.<region>.amazonaws.com/Prod/`

### Readers (reader / lat/long linked to children) – API for this use case

Each **reader** has **latitude**, **longitude** and is linked to **children** (MAC events). Each child payload: **MAC, Name, QR code (qrCode), Distance, Data, Antenna, PeakRSSI, DateTime, ReaderName, StartEvent, Count, TagEvent, UUID, Major, Minor, Namespace, Instance, Voltage, Temperature, URL** (plus `id`, `direction`, `createdAt` for API use).

| Method | Path | Description |
|--------|------|-------------|
| GET | `/readers` | List all readers (readerName, displayName, description, latitude, longitude). |
| GET | `/readers/{readerName}` | Get one reader (lat/long). **?include=children** returns reader **linked to its child MACs** (each child has the full payload above). Query: `limit` (default 100, max 1000) when include=children. |
| **GET** | **`/readers/{readerName}/events`** | **List children for this reader only.** Same child shape. Query: `direction` (in\|out), `limit`. |
| POST | `/readers` | Create reader. Body: `{"readerName","latitude","longitude"}` and optionally `displayName`, `description`. |
| PUT / PATCH | `/readers/{readerName}` | **Real-time edit reader.** Partial body: any of `displayName`, `description`, `latitude`, `longitude` (only changed fields). |
| DELETE | `/readers/{readerName}` | Delete reader (and its child events). |

### Events (MAC in/out at each reader – all editable)

Each reader has **multiple MACs** (persons); each event is one MAC **in** or **out** at that reader. Use **direction** for app in/out functionality. All events are editable.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/events` | List events. Query: `mac`, `readerName`, **`direction`** (`in` \| `out`), `from`, `to`, `limit`. e.g. `?readerName=Lobby&direction=in` = who entered Lobby. |
| GET | `/events/{id}` | Get one event by id |
| GET | `/events/person/{mac}` | List events for one person (MAC). Query: `limit` |
| POST | `/events` | Record MAC in/out at reader. Body: `mac`, `readerName`, **`direction`** (`in` \| `out`, default `in`), plus optional fields below. |
| PUT / PATCH | `/events/{id}` | **Real-time edit event.** Partial body: any of mac, name, qrCode, readerName, direction, distance, data, antenna, peakRSSI, dateTime, startEvent, count, tagEvent, uuid, major, minor, namespace, instance, voltage, temperature, url (only changed fields). |
| DELETE | `/events/{id}` | Delete an event |

**POST /events** body: **`mac`**, **`readerName`**, **`direction`** (optional, default `"in"`), `dateTime` (optional), `name`, `qrCode`, `distance`, `data`, `antenna`, `peakRSSI`, `startEvent`, `count`, `tagEvent`, `uuid`, `major`, `minor`, `namespace`, `instance`, `voltage`, `temperature`, `url`.

## Deployed stack

**API base URL:** `https://rkali63t89.execute-api.us-east-2.amazonaws.com/Prod/`

- **Stack name:** `ble-people-tracker`
- **Region:** `us-east-2`

DB parameters are not stored in the repo (no placeholders). Deploy with your real PostgreSQL connection details:

```bash
sam deploy --parameter-overrides "DBHost=your-rds.region.rds.amazonaws.com DBName=ble DBUser=youruser DBPassword=yourpassword DBPort=5432"
```

Then run `database/schema.sql` and the migrations in `database/migrations/` on your database.

---

## Deploy (AWS SAM)

1. Install [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html) and ensure AWS CLI is configured.

2. **Option A – Stack includes PostgreSQL (default, recommended)**  
   The stack creates an RDS PostgreSQL instance in a VPC. The **DB password is stored in AWS Secrets Manager** (auto-generated); you do not pass a password. Optionally set DB name/user:

```bash
sam build
sam deploy
```

   After the first deploy (RDS takes several minutes), run the schema and migrations once by invoking the schema-runner Lambda (use the **SchemaRunnerFunctionName** value from the stack outputs). The **DBSecretArn** output points to the secret containing the RDS password.

```bash
aws lambda invoke --function-name <SchemaRunnerFunctionName> --region us-east-2 out.json && cat out.json
```

   Then the API is ready to use.

3. **Option B – Use your own PostgreSQL**  
   Set `UseStackPostgres=false` and pass your DB host and credentials:

```bash
sam deploy --parameter-overrides "UseStackPostgres=false DBHost=your-rds-endpoint DBName=ble DBUser=youruser DBPassword=yourpassword DBPort=5432"
```

   If your DB is in a VPC, also pass **VpcSubnetIds** and **VpcSecurityGroupIds** (comma-separated). Run `database/schema.sql` and the files in `database/migrations/` on your database yourself.

4. Optional: **AllowedOrigin** (default `*`), **DBName** (default `ble`), **DBUser** (default `ble`). For subsequent deploys you can omit `--parameter-overrides` to keep the existing settings.

## Test all API endpoints

From the project root, run the script that hits every endpoint as an application would:

```bash
./test_api.sh
```

Optional: override base URL and API key:

```bash
./test_api.sh "https://YOUR_API_ID.execute-api.REGION.amazonaws.com/Prod" "YOUR_API_KEY"
```

The script checks that requests without an API key get 403. All other calls require a live database; deploy with real DB parameters (see Deploy section) so the API can connect.

**Unit tests (no DB, no deploy):** Run all handler logic with a mocked database so everything passes with no errors:

```bash
python -m pytest tests/test_api.py -v
# or
python -m unittest tests.test_api -v
```

## Production checklist: using this API in a production app

For the API to function correctly in a production application, ensure the following.

### 1. Database (required)

- **PostgreSQL** instance (e.g. **AWS RDS** or **Aurora**) with:
  - Schema applied: `database/schema.sql`
  - Migrations applied: `database/migrations/001_*.sql`, `002_*.sql`, `003_*.sql`
  - Backups and retention configured (e.g. RDS automated backups)
- **Deploy with real DB parameters** (no placeholders). Optional: VPC (if DB is in a private subnet), CORS origin:
  ```bash
  sam deploy --parameter-overrides "DBHost=your-rds-endpoint DBName=ble DBUser=... DBPassword=... DBPort=5432"
  ```
  If the DB is in a **VPC**, add subnet and security group IDs (comma-separated); Lambdas will run in the VPC:
  ```bash
  sam deploy --parameter-overrides "DBHost=... DBName=ble DBUser=... DBPassword=... VpcSubnetIds=subnet-1,subnet-2 VpcSecurityGroupIds=sg-xxx"
  ```
  Restrict CORS to your app origin (optional): `AllowedOrigin=https://your-app.com`
  Ensure the Lambda security group allows **outbound** to the DB port (5432) and the RDS security group allows **inbound** from that Lambda security group.

### 2. API key in your app (required)

- Every request must send the API key in the **`x-api-key`** header.
- **Do not** hardcode the key in frontend or mobile source. Use:
  - **Backend / server app:** environment variable or secrets manager (e.g. AWS Secrets Manager).
  - **Mobile app:** secure storage (e.g. Keychain/Keystore) or a backend that proxies requests and adds the key.
  - **Browser app:** call your own backend that adds the key, or use a short-lived token issued by your backend; avoid exposing the API key in client-side code.
- Retrieve the key value from **API Gateway → API keys** (or AWS CLI `get-api-key --include-value`) and store it securely. Create additional keys in the same usage plan if needed (e.g. per environment or per app).

### 3. Base URL and HTTPS

- Use the stack output **ApiUrl** as the base (e.g. `https://xxxx.execute-api.us-east-2.amazonaws.com/Prod/`). All traffic is HTTPS.
- In your app, configure this base URL (and the key) via config or environment, not hardcoded.

### 4. CORS (if your app is a browser app)

- **CORS is configured:** API Gateway allows `*` origin and methods GET, POST, PUT, PATCH, DELETE, OPTIONS; Lambda responses use the **AllowedOrigin** parameter (default `*`). To restrict to your frontend domain in production, deploy with `AllowedOrigin=https://your-app.com`.

### 5. Error handling in your app

- **403** – Missing or invalid API key; check header and key value.
- **400** – Invalid body or query (e.g. missing `mac`, invalid `direction`); inspect the JSON `error` in the response body.
- **404** – Resource not found (reader or event).
- **500** – Server/DB error; check Lambda and RDS logs in CloudWatch; ensure DB is reachable and schema is applied.

### 6. Optional: monitoring and scaling

- **CloudWatch:** A stack alarm **Api5xxAlarm** fires when the API returns any 5XX error (check Lambda and DB connectivity). Lambda and API Gateway logs are in the same region.
- **Throttling:** The usage plan is set to 500 req/s (1000 burst). Adjust in `template.yaml` under `Globals.Api.Auth.UsagePlan.Throttle` if needed.
- **High concurrency:** For many concurrent Lambdas, consider **RDS Proxy** in front of PostgreSQL to pool connections.

### 7. Summary for your production app

| Item | Action |
|------|--------|
| Database | Real RDS/Aurora; schema + migrations; deploy with `--parameter-overrides` for DB. |
| VPC | If DB is in VPC, pass `VpcSubnetIds` and `VpcSecurityGroupIds` (comma-separated) in `--parameter-overrides`. |
| API key | Send `x-api-key` on every request; store key in env/secrets, not in client code. |
| Base URL | Use ApiUrl from stack output over HTTPS. |
| CORS | Default `*`; set `AllowedOrigin=https://your-app.com` to restrict. |
| Monitoring | CloudWatch alarm **Api5xxAlarm** fires on 5XX; check Lambda/RDS logs. |
| Errors | Handle 403, 400, 404, 500 in your app; use CloudWatch for debugging. |

---

## Local development

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Set environment variables and run the schema against your Postgres DB, then invoke the Lambda handlers locally (e.g. with `sam local start-api` and `DB_*` env vars) or run your own HTTP server that calls the same handler code.

## License

Use as needed for your project.
