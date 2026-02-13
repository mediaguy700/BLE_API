-- BLE People Tracker: readers (lat/long) and events (MAC per reader)
CREATE TABLE IF NOT EXISTS readers (
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  latitude DOUBLE PRECISION NOT NULL,
  longitude DOUBLE PRECISION NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS events (
  id SERIAL PRIMARY KEY,
  reader_name TEXT NOT NULL REFERENCES readers(name) ON DELETE CASCADE,
  mac TEXT NOT NULL,
  direction TEXT CHECK (direction IN ('in', 'out')),
  name TEXT,
  qr_code TEXT,
  distance TEXT,
  data TEXT,
  antenna TEXT,
  peak_rssi TEXT,
  date_time TIMESTAMPTZ,
  start_event TEXT,
  count INTEGER,
  tag_event TEXT,
  uuid TEXT,
  major TEXT,
  minor TEXT,
  namespace TEXT,
  instance TEXT,
  voltage TEXT,
  temperature TEXT,
  url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_reader_name ON events(reader_name);
CREATE INDEX IF NOT EXISTS idx_events_mac ON events(mac);
