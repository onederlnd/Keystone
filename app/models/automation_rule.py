# app/models/automation_rule.py

import uuid
from sqlalchemy import Boolean, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.mixins import TimestampMixin


class AutomationRule(TimestampMixin, Base):
    __tablename__ = "automation_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, nullable=False
    )
    name: Mapped[str] = mapped_column(nullable=False)
    trigger_event: Mapped[str] = mapped_column(nullable=False)
    condition: Mapped[dict] = mapped_column(JSON, nullable=False)
    action: Mapped[str] = mapped_column(nullable=False)
    requires_approval: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
