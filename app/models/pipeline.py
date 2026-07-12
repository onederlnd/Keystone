# app/models/pipeline.py

import uuid
from datetime import datetime
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.mixins import TimestampMixin


class Pipelines(TimestampMixin, Base):
    __tablename__ = "pipelines"
    __table_args__ = (UniqueConstraint("listing_id", "contact_id"),)

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, nullable=False
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("listings.id"), nullable=False
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contacts.id"), nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    stage: Mapped[str] = mapped_column(nullable=False)
    offer_price: Mapped[int | None] = mapped_column(nullable=True)
    next_action: Mapped[str | None] = mapped_column(nullable=True)
    next_action_date: Mapped[datetime | None] = mapped_column(nullable=True)
    notes: Mapped[str | None] = mapped_column(nullable=True)
    last_stage_change_at: Mapped[datetime | None] = mapped_column(nullable=True)
