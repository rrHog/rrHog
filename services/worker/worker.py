import os, asyncio, orjson, json, uuid
from datetime import datetime, timezone
import clickhouse_connect
import psycopg
from nats.aio.client import Client as NATS

NATS_URL = os.getenv("NATS_URL", "nats://nats:4222")
STREAM = os.getenv("NATS_STREAM", "EVENTS")
SUBJECT = os.getenv("NATS_SUBJECT", "events.rrweb")
CH_URL = os.getenv("CH_URL", "http://clickhouse:8123")
CH_DB = os.getenv("CH_DB", "default")
PG_DSN = f"postgresql://{os.getenv('PG_USER','rrhog')}:{os.getenv('PG_PASSWORD','rrhog')}@{os.getenv('PG_HOST','postgres')}:5432/{os.getenv('PG_DB','rrhog')}"


def ch_client():
    host = CH_URL.split("://")[1].split(":")[0]
    port = int(CH_URL.rsplit(":", 1)[1])
    return clickhouse_connect.get_client(host=host, port=port, database=CH_DB)


async def ensure_stream(js):
    try:
        await js.stream_info(STREAM)
    except:
        await js.add_stream(name=STREAM, subjects=[SUBJECT], storage="file")


async def handle(msg, ch, pg_conn):
    data = orjson.loads(msg.data)
    project_id = int(data["project_id"])
    session_id = uuid.UUID(data["session_id"])
    seq = int(data.get("seq", 0))
    ts = datetime.fromisoformat(data["ts"])
    payload = orjson.dumps(data.get("events", [])).decode()

    ch.insert(
        "events_rrweb",
        [[project_id, session_id, seq, ts, payload]],
        column_names=["project_id", "session_id", "seq", "ts", "payload"],
    )
    await msg.ack()


async def main():
    nc = await NATS.connect(NATS_URL)
    js = nc.jetstream()
    await ensure_stream(js)

    ch = ch_client()
    pg_conn = await psycopg.AsyncConnection.connect(PG_DSN)

    # Create durable consumer if not exists
    try:
        await js.consumer_info(STREAM, "WORKER")
    except:
        await js.add_consumer(STREAM, durable_name="WORKER", ack_policy="explicit")

    sub = await js.subscribe(SUBJECT, durable="WORKER", manual_ack=True)
    print("Worker subscribed; awaiting messages...")
    async for msg in sub.messages:
        try:
            await handle(msg, ch, pg_conn)
        except Exception as e:
            print("Worker error:", e)
            await msg.nak()


if __name__ == "__main__":
    asyncio.run(main())
