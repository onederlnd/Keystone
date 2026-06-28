# app/models/listing.py

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.mixins import TimestampMixin
from app.models.listing_status_history import ListingStatusHistory

if TYPE_CHECKING:
    from app.models.listing_status_history import ListingStatusHistory


class Listing(TimestampMixin, Base):
    __tablename__ = "listings"
    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, nullable=False
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    seller_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    address: Mapped[str] = mapped_column(nullable=False)
    city: Mapped[str] = mapped_column(nullable=False)
    state: Mapped[str] = mapped_column(nullable=False)
    zip: Mapped[str] = mapped_column(nullable=False)
    price: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(default="draft", nullable=False)
    status_history: Mapped[list["ListingStatusHistory"]] = relationship(
        "ListingStatusHistory", back_populates="listing", cascade="all, delete-orphan"
    )
    bedrooms: Mapped[int] = mapped_column(nullable=False)
    bathrooms: Mapped[int] = mapped_column(nullable=False)
    sqft: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    mls_id: Mapped[str] = mapped_column(nullable=False)
