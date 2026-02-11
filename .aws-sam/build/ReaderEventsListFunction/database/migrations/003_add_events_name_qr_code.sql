-- Add name and qr_code to child records (events)
ALTER TABLE events ADD COLUMN IF NOT EXISTS name VARCHAR(255);
ALTER TABLE events ADD COLUMN IF NOT EXISTS qr_code TEXT;
COMMENT ON COLUMN events.name IS 'Display name for the child/person record';
COMMENT ON COLUMN events.qr_code IS 'QR code value or URL for the child record';
