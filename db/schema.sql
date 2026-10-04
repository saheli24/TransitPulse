CREATE TABLE events (
  id BIGSERIAL PRIMARY KEY,
  ts TIMESTAMPTZ,
  route TEXT,
  station TEXT,
  delay_min DOUBLE PRECISION,
  weather TEXT,
  event TEXT,
  zscore DOUBLE PRECISION,
  is_anomaly BOOLEAN,
  injected BOOLEAN,       -- ground-truth label (synthetic data only)
  latency_ms DOUBLE PRECISION
);
CREATE INDEX idx_events_anom ON events (is_anomaly, ts DESC);