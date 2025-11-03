# services/worker/worker.py
import os
import asyncio
import uuid
from datetime import datetime

import nats                      # core NATS subscribe (no JetStream consumer)
import orjson
import clickhouse_connect
import psycopg                   # kept for future use

# --- Env ---
NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")
SUBJECT  = os.getenv("NATS_SUBJECT", "events.rrweb")
QUEUE    = os.getenv("NATS_QUEUE", "rrhog-workers")   # queue group for load-balancing (optional)

CH_URL   = os.getenv("CH_URL", "http://clickhouse:8123")
CH_DB    = os.getenv("CH_DB", "default")

PG_DSN   = (
    f"postgresql://{os.getenv('PG_USER','rrhog')}:"
    f"{os.getenv('PG_PASSWORD','rrhog')}@{os.getenv('PG_HOST','postgres')}:5432/"
    f"{os.getenv('PG_DB','rrhog')}"
)

def ch_client():
    host = CH_URL.split("://", 1)[1].split(":", 1)[0]
    port = int(CH_URL.rsplit(":", 1)[1])
    return clickhouse_connect.get_client(host=host, port=port, database=CH_DB)

def insert_events(ch, data: dict):
    project_id = int(data["project_id"])
    session_id = uuid.UUID(data["session_id"])
    seq        = int(data.get("seq", 0))
    ts         = datetime.fromisoformat(data["ts"])     # ISO timestamp with offset from API
    payload    = orjson.dumps(data.get("events", [])).decode()

    ch.insert(
        "events_rrweb",
        [[project_id, session_id, seq, ts, payload]],
        column_names=["project_id", "session_id", "seq", "ts", "payload"],
    )

async def main():
    # Connections
    nc = await nats.connect(NATS_URL)
    ch = ch_client()
    pg_conn = await psycopg.AsyncConnection.connect(PG_DSN)  # kept for future writes/metadata  # noqa: F841

    async def handler(msg: nats.aio.msg.Msg):
        try:
            data = orjson.loads(msg.data)
            insert_events(ch, data)
            # core NATS has no ack; just return
        except Exception as e:
            print("Worker error:", e)

    # Core NATS queue subscription (no persistence/backlog)
    await nc.subscribe(SUBJECT, queue=QUEUE, cb=handler)
    print(f"Worker subscribed (core NATS). Subject={SUBJECT} queue={QUEUE}")

    # Keep the worker alive
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
