import uuid
from datetime import datetime
from pydantic import BaseModel


class ApprovalQueueRead(BaseModel):
    id: uuid.UUID
    entity_type: str
    entity_id: str
    proposed_action: str
    proposed_state: str
    context: str | None
    status: str
    created_by: str
    reviewed_by_id: str | None
    reviewed_at: datetime | None
    expired_at: datetime | None
    created_at: datetime
