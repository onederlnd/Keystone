import uuid
from datetime import datetime
from pydantic import BaseModel


class ContactCreate(BaseModel):
    agent_id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    email: str
    phone: str
    type: str
    source: str
    notes: str | None = None


class ContactRead(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    user_id: uuid.UUID
    full_name: str
    email: str
    phone: str
    type: str
    source: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class ContactUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    type: str | None = None
    source: str | None = None
    notes: str | None = None
