from pydantic import BaseModel, Field
from typing import Any, List, Optional
from datetime import datetime
import uuid

class UserInfo(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    anonymous: bool = True

class IngestPayload(BaseModel):
    project_write_key: Optional[str] = None  # you can pass via header instead
    session_id: Optional[uuid.UUID] = None
    seq: int = 0
    ts: datetime = Field(default_factory=datetime.utcnow)
    url: Optional[str] = None
    user: Optional[UserInfo] = None
    events: List[Any]  # rrweb events batch
