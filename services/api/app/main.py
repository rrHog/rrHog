# services/api/app/main.py
import os
import json
import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, Request, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.status import HTTP_202_ACCEPTED

from .models import IngestPayload
from . import nats_utils, ch as chmod, db as pg, utils


app = FastAPI(title="rrHog API")

# ---- CORS (flexible + safe) ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    allow_credentials=True,
    max_age=86400,
)


@app.get("/healthz")
async def healthz():
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}


@app.post("/i", status_code=HTTP_202_ACCEPTED)
async def ingest(
    payload: IngestPayload,
    request: Request,
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_write_key: str | None = Header(default=None, alias="X-Write-Key"),
    user_agent: str | None = Header(default=None, alias="User-Agent"),
):
    # Resolve write key → project
    write_key = utils.get_write_key_from_request(
        authorization, x_write_key, payload.project_write_key
    )
    project_id = await pg.get_project_by_write_key(write_key)
    if not project_id:
        raise HTTPException(status_code=401, detail="Invalid write key")

    # Ensure session id
    session_id = str(payload.session_id or uuid.uuid4())
    now = datetime.now(timezone.utc)

    # Minimal metadata save (insert-once per session)
    await pg.ensure_session_meta(
        project_id=project_id,
        session_id=session_id,
        started_at=now,
        user_id=(payload.user.id if payload.user else None),
        user_email=(payload.user.email if payload.user else None),
        ua=user_agent or "",
    )

    # Prepare batch to queue
    batch = {
        "project_id": project_id,
        "session_id": session_id,
        "seq": payload.seq,
        "ts": now.isoformat(),
        "url": payload.url,
        "user": payload.user.model_dump() if payload.user else None,
        "events": payload.events,
    }

    # Publish to JetStream (durable, acked by worker)
    await nats_utils.publish_event(batch)

    return {"status": "accepted", "session_id": session_id}


@app.get("/sessions")
async def sessions(read_key: str = Query(...), limit: int = 50):
    project_id = await pg.validate_read_key(read_key)
    if not project_id:
        raise HTTPException(status_code=401, detail="Invalid read key")
    rows = await pg.list_sessions(project_id, limit)
    return {"sessions": rows}


@app.get("/replay")
async def replay(session_id: str = Query(...), read_key: str = Query(...)):
    project_id = await pg.validate_read_key(read_key)
    if not project_id:
        raise HTTPException(status_code=401, detail="Invalid read key")

    client = chmod.ch()
    rows = client.query(
        """
        SELECT seq, ts, payload
        FROM events_rrweb
        WHERE project_id = %(pid)s
          AND session_id = toUUID(%(sid)s)
        ORDER BY ts, seq
        """,
        parameters={"pid": project_id, "sid": session_id},
    ).result_rows

    if not rows:
        return {"session_id": session_id, "events": []}

    # Each payload is a JSON string; concat nested events for rrweb-player
    events: list = []
    for seq, ts, payload in rows:
        try:
            piece = json.loads(payload)
            if isinstance(piece, list):
                events.extend(piece)
            elif isinstance(piece, dict) and "events" in piece:
                events.extend(piece["events"])
        except Exception:
            # swallow malformed rows to avoid breaking playback
            pass

    return {"session_id": session_id, "events": events}
