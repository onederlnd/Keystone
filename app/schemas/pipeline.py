# app/schemas/pipeline.py
import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class PipelineCreate(BaseModel):
    listing_id: uuid.UUID
    contact_id: uuid.UUID
    agent_id: uuid.UUID
    stage: str = Field(max_length=50)
    offer_price: int | None = None
    next_action: str | None = Field(default=None, max_length=255)
    next_action_date: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)


class PipelineRead(BaseModel):
    id: uuid.UUID
    listing_id: uuid.UUID
    contact_id: uuid.UUID
    agent_id: uuid.UUID
    stage: str
    offer_price: int | None = None
    next_action: str | None = None
    next_action_date: datetime | None = None
    notes: str | None = None
    last_stage_change_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class PipelineUpdate(BaseModel):
    stage: str | None = Field(default=None, max_length=50)
    offer_price: int | None = None
    next_action: str | None = Field(default=None, max_length=255)
    next_action_date: datetime | None = None
    notes: str | None = Field(default=None, max_length=2000)


class PipelineFilterParams(BaseModel):
    listing_id: uuid.UUID | None = None
    contact_id: uuid.UUID | None = None
    agent_id: uuid.UUID | None = None
    stage: str | None = None
