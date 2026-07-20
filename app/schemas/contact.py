import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class ContactCreate(BaseModel):
    agent_id: uuid.UUID
    user_id: uuid.UUID
    full_name: str = Field(max_length=200)
    email: EmailStr
    phone: str = Field(max_length=20)
    type: str = Field(max_length=20)
    source: str = Field(max_length=100)
    notes: str | None = Field(default=None, max_length=2000)


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
    full_name: str | None = Field(default=None, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    type: str | None = Field(default=None, max_length=20)
    source: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=2000)
