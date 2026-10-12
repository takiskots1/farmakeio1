-- Non-destructive upgrade from CHRYSPHARMACY v2.3 to v2.4 (PostgreSQL).
-- Backup first. Run ONCE or safely repeat with IF NOT EXISTS.
BEGIN;
CREATE TABLE IF NOT EXISTS medication_reminders (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    medication_name VARCHAR(160) NOT NULL,
    instructions VARCHAR(240),
    remind_at TIME WITHOUT TIME ZONE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    channel_portal BOOLEAN NOT NULL DEFAULT TRUE,
    channel_sms BOOLEAN NOT NULL DEFAULT FALSE,
    channel_email BOOLEAN NOT NULL DEFAULT FALSE,
    channel_push BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_medication_reminders_client_id ON medication_reminders (client_id);
CREATE TABLE IF NOT EXISTS medication_reminder_deliveries (
    id SERIAL PRIMARY KEY,
    reminder_id INTEGER NOT NULL REFERENCES medication_reminders(id) ON DELETE CASCADE,
    delivery_date DATE NOT NULL,
    channel VARCHAR(12) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'processing',
    provider_id VARCHAR(120),
    error VARCHAR(300),
    message_id INTEGER NULL REFERENCES messages(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_med_reminder_delivery UNIQUE(reminder_id, delivery_date, channel)
);
CREATE INDEX IF NOT EXISTS ix_medication_reminder_deliveries_reminder_id
    ON medication_reminder_deliveries(reminder_id);
CREATE TABLE IF NOT EXISTS health_measurements (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    measured_on DATE NOT NULL,
    kind VARCHAR(12) NOT NULL,
    bp_high_mmhg INTEGER,
    bp_low_mmhg INTEGER,
    glucose_mgdl INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_health_measurement_kind CHECK (kind IN ('bp','glucose')),
    CONSTRAINT ck_health_measurement_values CHECK (
      (kind='bp' AND bp_high_mmhg BETWEEN 50 AND 250 AND bp_low_mmhg BETWEEN 50 AND 250
       AND bp_high_mmhg > bp_low_mmhg AND bp_high_mmhg % 5 = 0 AND bp_low_mmhg % 5 = 0
       AND glucose_mgdl IS NULL)
      OR (kind='glucose' AND glucose_mgdl BETWEEN 60 AND 500
          AND bp_high_mmhg IS NULL AND bp_low_mmhg IS NULL)
    )
);
CREATE INDEX IF NOT EXISTS ix_health_measurements_client_id ON health_measurements (client_id);
CREATE INDEX IF NOT EXISTS ix_health_measurements_measured_on ON health_measurements (measured_on);
COMMIT;
