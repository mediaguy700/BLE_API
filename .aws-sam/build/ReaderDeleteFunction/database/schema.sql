-- People Tracker BLE API - PostgreSQL Schema
-- Readers: unique readers with lat/long for map placement
-- Events: BLE tag readings (MAC = unique person identifier)

-- Readers: static locations for the map; each has lat/long; editable via API
CREATE TABLE IF NOT EXISTS readers (
    reader_name    VARCHAR(255) PRIMARY KEY,
    display_name   VARCHAR(255),
    description    TEXT,
    latitude       DOUBLE PRECISION NOT NULL,
    longitude      DOUBLE PRECISION NOT NULL,
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_readers_location ON readers (latitude, longitude);
COMMENT ON TABLE readers IS 'Static readers: fixed lat/long for map; editable. One reader has many child MAC addresses (via events).';
COMMENT ON COLUMN readers.display_name IS 'Optional display name (e.g. Room 101, Conference A)';
COMMENT ON COLUMN readers.description IS 'Optional room/reader description';

-- Events: each row = one MAC (child) at one reader; readers can have multiple child MAC addresses; events editable
CREATE TABLE IF NOT EXISTS events (
    id             BIGSERIAL PRIMARY KEY,
    mac            VARCHAR(17) NOT NULL,
    name           VARCHAR(255),              -- display name for child/person
    qr_code        TEXT,                     -- QR code value or URL for child record
    direction      VARCHAR(10) DEFAULT 'in',  -- 'in' = arrived at reader, 'out' = left reader
    distance       DOUBLE PRECISION,
    data           TEXT,
    antenna        INTEGER,
    peak_rssi      INTEGER,
    date_time      TIMESTAMPTZ NOT NULL,
    reader_name    VARCHAR(255) NOT NULL REFERENCES readers(reader_name) ON DELETE CASCADE,
    start_event    BOOLEAN,
    count          INTEGER,
    tag_event      VARCHAR(255),
    uuid           VARCHAR(36),
    major          INTEGER,
    minor          INTEGER,
    namespace      VARCHAR(255),
    instance       VARCHAR(255),
    voltage        DOUBLE PRECISION,
    temperature    DOUBLE PRECISION,
    url            TEXT,
    created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_mac ON events (mac);
CREATE INDEX IF NOT EXISTS idx_events_reader ON events (reader_name);
CREATE INDEX IF NOT EXISTS idx_events_direction ON events (direction);
CREATE INDEX IF NOT EXISTS idx_events_date_time ON events (date_time DESC);
CREATE INDEX IF NOT EXISTS idx_events_mac_datetime ON events (mac, date_time DESC);
CREATE INDEX IF NOT EXISTS idx_events_reader_direction ON events (reader_name, direction);

COMMENT ON COLUMN events.direction IS 'in = person arrived at reader, out = person left reader (for app in/out tracking)';
COMMENT ON TABLE events IS 'Child MAC per reader: one reader has many MACs (events); editable via API';
