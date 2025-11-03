CREATE TABLE IF NOT EXISTS events_rrweb (
  project_id UInt32,
  session_id UUID,
  seq UInt32,
  ts DateTime64(3, 'UTC'),
  payload String CODEC(ZSTD(9)),
  event_id UUID DEFAULT generateUUIDv4(),
  ingest_ts DateTime DEFAULT now()
)
ENGINE=MergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (project_id, session_id, ts, seq)
TTL ts + INTERVAL 90 DAY;

CREATE TABLE IF NOT EXISTS events (
  project_id UInt32,
  session_id UUID,
  user_id Nullable(String),
  event_name LowCardinality(String),
  ts DateTime64(3, 'UTC'),
  url String,
  props JSON,
  event_id UUID DEFAULT generateUUIDv4()
)
ENGINE=MergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (project_id, event_name, ts, session_id);
