# app/schemas/document.py

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class DocumentGenerateRequest(BaseModel):
    listing_id: uuid.UUID
    contact_id: uuid.UUID
    pipeline_id: uuid.UUID
    type: str = Field(max_length=50)
    notes: str | None = Field(default=None, max_length=2000)


class DocumentRead(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    contact_id: uuid.UUID
    pipeline_id: uuid.UUID
    created_by_id: uuid.UUID
    type: str
    status: str
    file_path: str
    generated_by: str
    created_at: datetime
    updated_at: datetime


class DocumentStatusUpdate(BaseModel):
    new_status: str


class DocumentFilterParams(BaseModel):
    listing_id: uuid.UUID | None = None
    contact_id: uuid.UUID | None = None
    pipeline_id: uuid.UUID | None = None
    created_by_id: uuid.UUID | None = None
    type: str | None = None
    status: str | None = None
    generated_by: str | None = None
