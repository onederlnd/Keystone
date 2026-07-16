# app/models/document.py

import uuid
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from app.models.mixins import TimestampMixin
from app.models.listing import Listings
from app.models.contact import Contacts
from app.models.pipeline import Pipelines
from app.models.user import Users


class Documents(TimestampMixin, Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4, nullable=False
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("listings.id"), nullable=False
    )
    contact_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("contacts.id"), nullable=True
    )
    pipeline_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pipelines.id"), nullable=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )
    type: Mapped[str] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(default="draft", nullable=False)
    file_path: Mapped[str] = mapped_column(nullable=False)
    generated_by: Mapped[str] = mapped_column(default="manual", nullable=False)

    listing: Mapped["Listings"] = relationship("Listings")
    contact: Mapped["Contacts"] = relationship("Contacts")
    pipeline: Mapped["Pipelines"] = relationship("Pipelines")
    created_by: Mapped["Users"] = relationship("Users")
