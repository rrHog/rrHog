# Architecture Overview

rrHog is optimized for **reliable ingestion** and **minimal ops**. The API **acknowledges immediately**, then a worker asynchronously writes to storage.


## Diagram

```mermaid
flowchart LR
  subgraph Client
    B[Browser: rrweb]
  end
  subgraph Edge
    NG[Nginx (or Kong)]
  end
  subgraph App
    A[FastAPI (ingest & read)]
    Q[NATS JetStream]
    W[Python Worker]
  end
  subgraph Data
    CH[(ClickHouse)]
    PG[(Postgres)]
  end
  subgraph UI
    NX[Next.js UI]
  end

  B --> NG --> A
  A --> Q
  W --> CH
  W --> PG
  NX --> A
  A --> CH
  A --> PG
````

## Ingest sequence

```mermaid
sequenceDiagram
  participant Browser
  participant Edge as Nginx
  participant API as FastAPI (ingest /i)
  participant NATS as NATS JetStream
  participant Worker
  participant CH as ClickHouse

  Browser->>Edge: POST /i (batched rrweb)
  Edge->>API: proxy request
  API->>NATS: publish(batch)
  API-->>Browser: 202 Accepted
  Worker->>NATS: pull(batch)
  Worker->>CH: bulk insert (segments/events)
  Worker-->>NATS: ack
```

## Components (concise)

* **Nginx**: edge proxy, gzip/brotli, per-project rate limits, forwards to API `/i`.
* **FastAPI**:

  * **Ingest**: validate + publish to `events.rrweb` → return `202`.
  * **Read**: playback & analytics endpoints (ClickHouse/Postgres).
  * Auth: per-project **write** and **read** keys; session JWT for UI.
* **NATS JetStream**: durable streams, at-least-once delivery, back-pressure.
* **Worker (Python, asyncio)**: pull, batch, bulk insert; idempotency by hashing payload.
* **ClickHouse**: raw rrweb segments + analytics events; TTL on raw.
* **Postgres**: projects, API keys, sessions meta, dashboards.

## Storage schemas (starter)

**ClickHouse**

```sql
CREATE TABLE events_rrweb (
  project_id UInt32,
  session_id UUID,
  seq UInt32,
  ts DateTime64(3, 'UTC'),
  payload String CODEC(ZSTD(9)),
  event_id UUID,
  ingest_ts DateTime DEFAULT now()
)
ENGINE=MergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (project_id, session_id, ts, seq)
TTL ts + INTERVAL 90 DAY;

CREATE TABLE events (
  project_id UInt32,
  session_id UUID,
  user_id Nullable(String),
  event_name LowCardinality(String),
  ts DateTime64(3, 'UTC'),
  url String,
  props JSON,
  event_id UUID
)
ENGINE=MergeTree
PARTITION BY toYYYYMM(ts)
ORDER BY (project_id, event_name, ts, session_id);
```

**Postgres**

```sql
CREATE TABLE projects (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  write_key TEXT UNIQUE NOT NULL,
  read_key  TEXT UNIQUE NOT NULL
);

CREATE TABLE sessions_meta (
  project_id INT REFERENCES projects(id),
  session_id UUID,
  started_at TIMESTAMPTZ,
  user_id TEXT,
  ua TEXT,
  PRIMARY KEY (project_id, session_id)
);
```

## NATS JetStream (subjects/consumers)

* Stream: `EVENTS`

  * Subjects: `events.rrweb`, `events.analytics`
  * Storage: file, retention: limits, replicas: 1 (MVP)
* Consumer: `WORKER` (durable)

  * `max_ack_pending` tuned to worker capacity
  * `max_deliver` 10 (redelivery retries)

## Ops & Observability

* `/healthz` endpoints
* Basic Prometheus metrics (queue lag, batch size, CH latency)
* ClickHouse TTL to control disk (e.g., keep raw rrweb 60–90 days)
* PII masking on client (rrweb plugins), allowlist domains/selectors

## Trade-offs

* **NATS vs Kafka/Redpanda**: NATS is lighter → great for single host. Move to Redpanda later if you need Kafka ecosystem.
* **Single-node ClickHouse**: perfect for MVP; add replicas/keeper later for HA.
