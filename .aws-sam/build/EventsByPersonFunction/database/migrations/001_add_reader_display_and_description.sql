-- Add optional room-friendly fields to existing readers (multiple readers/rooms, same functionality)
ALTER TABLE readers ADD COLUMN IF NOT EXISTS display_name VARCHAR(255);
ALTER TABLE readers ADD COLUMN IF NOT EXISTS description TEXT;
COMMENT ON COLUMN readers.display_name IS 'Optional display name (e.g. Room 101, Conference A)';
COMMENT ON COLUMN readers.description IS 'Optional room/reader description';
