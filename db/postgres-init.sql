CREATE TABLE IF NOT EXISTS projects (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  write_key TEXT UNIQUE NOT NULL,
  read_key  TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions_meta (
  project_id INT REFERENCES projects(id),
  session_id UUID,
  started_at TIMESTAMPTZ,
  user_id TEXT,
  user_email TEXT,
  ua TEXT,
  PRIMARY KEY (project_id, session_id)
);

INSERT INTO projects (name, write_key, read_key)
VALUES ('DevProject', 'dev_write_123', 'dev_read_123')
ON CONFLICT (write_key) DO NOTHING;
