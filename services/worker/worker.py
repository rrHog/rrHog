# services/worker/worker.py
import os
import asyncio
import uuid
from datetime import datetime, timezone

import nats
import orjson
import clickhouse_connect
import psycopg

from nats.js.api import (
    StreamConfig,
    StorageType,
    RetentionPolicy,
    ConsumerConfig,
    DeliverPolicy,
    AckPolicy,
)

# -------- Env --------
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")
STREAM   = os.getenv("NATS_STREAM", "EVENTS")
SUBJECT  = os.getenv("NATS_SUBJECT", "events.rrweb")
DURABLE  = os.getenv("NATS_CONSUMER", "WORKER")

MAX_FETCH = int(os.getenv("NATS_MAX_FETCH", "128"))         # per pull
FETCH_TIMEOUT_SEC = float(os.getenv("NATS_FETCH_TIMEOUT_SEC", "1.0"))

CH_URL   = os.getenv("CH_URL", "http://clickhouse:8123")
CH_DB    = os.getenv("CH_DB", "default")

PG_DSN   = (
    f"postgresql://{os.getenv('PG_USER','rrhog')}:"
    f"{os.getenv('PG_PASSWORD','rrhog')}@{os.getenv('PG_HOST','postgres')}:5432/"
    f"{os.getenv('PG_DB','rrhog')}"
)

# -------- ClickHouse helpers --------

def ch_client():
    """
    clickhouse-connect expects host/port, not a full URL.
    """
    host = CH_URL.split("://", 1)[1].split(":", 1)[0]
    port = int(CH_URL.rsplit(":", 1)[1])
    return clickhouse_connect.get_client(host=host, port=port, database=CH_DB)

def ensure_clickhouse_schema(ch):
    """
    Create the rrweb raw table if it doesn't exist.
    Matches API reader expectations (/replay).
    """
    ddl = """
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
    """
    ch.command(ddl)

def _parse_ts(ts_str: str) -> datetime:
    """
    Accepts ISO-8601 (with or without 'Z' / offset) and returns UTC-aware datetime.
    """
    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

def insert_events(ch, data: dict):
    """
    One message from API can represent a batch-chunk of rrweb events.
    We store it as one row (payload=JSON string of that chunk).
    """
    project_id = int(data["project_id"])
    session_id = uuid.UUID(str(data["session_id"]))
    seq        = int(data.get("seq", 0))
    ts         = _parse_ts(data["ts"])
    payload    = orjson.dumps(data.get("events", [])).decode()

    ch.insert(
        "events_rrweb",
        [[project_id, session_id, seq, ts, payload]],
        column_names=["project_id", "session_id", "seq", "ts", "payload"],
    )

# -------- Main (JetStream durable pull) --------

async def run():
    # NATS + JetStream
    nc = await nats.connect(NATS_URL)
    js = nc.jetstream()

    # Ensure stream exists (harmless if it already does)
    try:
        await js.stream_info(STREAM)
    except Exception:
        await js.add_stream(
            StreamConfig(
                name=STREAM,
                subjects=[SUBJECT],
                storage=StorageType.FILE,
                retention=RetentionPolicy.Limits,
            )
        )

    # Ensure durable consumer (harmless if it already exists)
    try:
        await js.consumer_info(STREAM, DURABLE)
    except Exception:
        await js.add_consumer(
            stream=STREAM,
            config=ConsumerConfig(
                durable_name=DURABLE,
                deliver_policy=DeliverPolicy.All,
                ack_policy=AckPolicy.Explicit,
                max_ack_pending=1000,
            ),
        )

    # Pull-subscription bound to durable
    sub = await js.pull_subscribe(SUBJECT, durable=DURABLE)
    print(f"[worker] JetStream consumer ready  stream={STREAM} subject={SUBJECT} durable={DURABLE}")

    # DBs
    ch = ch_client()
    ensure_clickhouse_schema(ch)

    # Keep PG connection handy for future use; not used in MVP
    try:
        pg_conn = await psycopg.AsyncConnection.connect(PG_DSN)  # noqa: F841
    except Exception as e:
        print("[worker] Postgres connect failed (non-fatal for MVP):", e)

    # Main loop
    while True:
        try:
            msgs = await sub.fetch(MAX_FETCH, timeout=FETCH_TIMEOUT_SEC)
        except Exception:
            # Quiet idle polling
            await asyncio.sleep(0.05)
            continue

        for msg in msgs:
            try:
                data = orjson.loads(msg.data)
                insert_events(ch, data)
                await msg.ack()
            except Exception as e:
                # NAK → redelivery; if it keeps failing, set JS policy (max_deliver) on consumer
                print("[worker] error handling message:", e)
                try:
                    await msg.nak()
                except Exception:
                    # if we can't NAK, do nothing; message will time out and redeliver
                    pass

async def main():
    try:
        await run()
    except asyncio.CancelledError:
        pass

if __name__ == "__main__":
    asyncio.run(main())
