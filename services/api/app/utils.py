import os, uuid
from fastapi import Header

DEFAULT_WRITE_KEY = os.getenv("DEFAULT_WRITE_KEY","dev_write_123")

def get_write_key_from_request(header_auth: str | None, header_key:str | None, body_key:str | None):
    # Priority: Authorization: Bearer <key> > X-Write-Key > body.project_write_key > fallback
    if header_auth and header_auth.lower().startswith("bearer "):
        return header_auth.split(" ",1)[1].strip()
    if header_key:
        return header_key.strip()
    if body_key:
        return body_key.strip()
    return DEFAULT_WRITE_KEY

def new_session_id():
    return str(uuid.uuid4())
