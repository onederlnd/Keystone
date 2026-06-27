# app/models/approval_queue.py

import uuid
from sqlalchemy import ForeignKey, JSON
from datetime import datetime, timezone

from app.core.database import Base


from sqlalchemy.orm import Mapped, mapped_column


class ApprovalQueue(Base):
    __tablename__ = "approval_queue"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(nullable=False)
    entity_id: Mapped[str] = mapped_column(nullable=False)
    proposed_action: Mapped[str] = mapped_column(nullable=False)
    proposed_state: Mapped[str | None] = mapped_column(nullable=True)
    context: Mapped[dict] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(default="pending")
    created_by: Mapped[str] = mapped_column(nullable=False)
    reviewed_by_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
