-- Add in/out direction for app: track MAC arriving at reader (in) or leaving (out)
ALTER TABLE events ADD COLUMN IF NOT EXISTS direction VARCHAR(10) DEFAULT 'in';
UPDATE events SET direction = 'in' WHERE direction IS NULL;
CREATE INDEX IF NOT EXISTS idx_events_direction ON events (direction);
CREATE INDEX IF NOT EXISTS idx_events_reader_direction ON events (reader_name, direction);
COMMENT ON COLUMN events.direction IS 'in = person arrived at reader, out = person left reader';
