# app/schemas/approval_queue.py

import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ApprovalQueueRead(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    entity_type: str
    entity_id: str
    proposed_action: str
    proposed_state: str | None
    context: dict | None
    status: str
    created_by: str
    reviewed_by_id: str | None
    reviewed_at: datetime | None
    expires_at: datetime | None
    created_at: datetime


class RejectRequest(BaseModel):
    reason: str = Field(max_length=500)


class ModifyRequest(BaseModel):
    modified_context: dict
