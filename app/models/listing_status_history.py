# app/models/listing_status_history.py
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.mixins import TimestampMixin

if TYPE_CHECKING:
    from app.models.listing import Listings


class ListingStatusHistory(TimestampMixin, Base):
    __tablename__ = "listing_status_history"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    listing_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("listings.id"), nullable=False
    )
    previous_status: Mapped[str] = mapped_column(nullable=False)
    new_status: Mapped[str] = mapped_column(nullable=False)
    changed_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    notes: Mapped[str] = mapped_column(nullable=True)
    triggered_by: Mapped[str] = mapped_column(nullable=False)  # manual or automatic
    listing: Mapped["Listings"] = relationship(
        "Listings", back_populates="status_history"
    )
