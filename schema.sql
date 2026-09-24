CREATE TABLE IF NOT EXISTS detection_events (
 id BIGSERIAL PRIMARY KEY, video_name TEXT, frame_number INTEGER,
 timestamp_seconds DOUBLE PRECISION, class_name TEXT, confidence DOUBLE PRECISION,
 track_id INTEGER, created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS challans (
 id BIGSERIAL PRIMARY KEY, challan_no TEXT UNIQUE NOT NULL, created_at TIMESTAMPTZ DEFAULT NOW(),
 video_name TEXT, frame_number INTEGER, timestamp_seconds DOUBLE PRECISION,
 vehicle_number TEXT, violation TEXT, fine_amount NUMERIC(10,2),
 signal_status TEXT, confidence DOUBLE PRECISION, message_status TEXT,
 payment_status TEXT, notes TEXT
);
