import asyncio, os, json
from nats.aio.client import Client as NATS
from nats.js.client import JetStreamContext

_nats = None
_js: JetStreamContext | None = None

STREAM = os.getenv("NATS_STREAM","EVENTS")
SUBJECT = os.getenv("NATS_SUBJECT","events.rrweb")
URL = os.getenv("NATS_URL","nats://nats:4222")

async def get_js():
    global _nats, _js
    if _js:
        return _js
    _nats = await NATS.connect(URL)
    _js = _nats.jetstream()
    # Ensure stream exists
    try:
        await _js.stream_info(STREAM)
    except:
        await _js.add_stream(name=STREAM, subjects=[SUBJECT], storage="file")
    return _js

async def publish_event(batch: dict):
    js = await get_js()
    data = json.dumps(batch).encode("utf-8")
    await js.publish(SUBJECT, data)
