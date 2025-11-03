import os
import psycopg
from contextlib import asynccontextmanager

PG_DSN = f"postgresql://{os.getenv('PG_USER','rrhog')}:{os.getenv('PG_PASSWORD','rrhog')}@{os.getenv('PG_HOST','postgres')}:5432/{os.getenv('PG_DB','rrhog')}"

async def ensure_session_meta(project_id:int, session_id:str, started_at, user_id, user_email, ua):
    async with await psycopg.AsyncConnection.connect(PG_DSN) as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO sessions_meta (project_id, session_id, started_at, user_id, user_email, ua)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (project_id, session_id) DO NOTHING
            """, (project_id, session_id, started_at, user_id, user_email, ua))
            await conn.commit()

async def get_project_by_write_key(write_key:str):
    async with await psycopg.AsyncConnection.connect(PG_DSN) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id FROM projects WHERE write_key=%s", (write_key,))
            row = await cur.fetchone()
            return row[0] if row else None

async def validate_read_key(read_key:str):
    async with await psycopg.AsyncConnection.connect(PG_DSN) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id FROM projects WHERE read_key=%s", (read_key,))
            row = await cur.fetchone()
            return row[0] if row else None

async def list_sessions(project_id:int, limit:int=50):
    async with await psycopg.AsyncConnection.connect(PG_DSN) as conn:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT session_id::text, started_at, COALESCE(user_id,''), COALESCE(user_email,'')
                FROM sessions_meta
                WHERE project_id=%s
                ORDER BY started_at DESC
                LIMIT %s
            """, (project_id, limit))
            rows = await cur.fetchall()
            return [{"session_id":r[0], "started_at":r[1].isoformat(), "user_id":r[2], "user_email":r[3]} for r in rows]
