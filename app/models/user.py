import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Enum as SAEnum, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class UserRole(str, enum.Enum):
    # TODO: Define the four role values: admin, agent, buyer, seller
    pass


class TimestampMixin:
    # TODO: Add `created_at` mapped_column
    #       - type: DateTime(timezone=True)
    #       - default: datetime.now(timezone.utc)
    #       - nullable: False

    # TODO: Add `updated_at` mapped_column
    #       - type: DateTime(timezone=True)
    #       - default AND onupdate: datetime.now(timezone.utc)
    #       - nullable: False
    pass


class User(TimestampMixin, Base):
    __tablename__ = "users"

    # TODO: id — UUID primary key, default uuid.uuid4, as_uuid=True
    id: Mapped[uuid.UUID] = mapped_column(...)

    # TODO: email — String, unique=True, index=True, nullable=False
    email: Mapped[str] = mapped_column(...)

    # TODO: hashed_password — String, nullable=False
    hashed_password: Mapped[str] = mapped_column(...)

    # TODO: full_name — String, nullable=True
    full_name: Mapped[str | None] = mapped_column(...)

    # TODO: role — SAEnum(UserRole), nullable=False, no server default
    #       The caller must always pass this explicitly (mirrors Mise's pattern)
    role: Mapped[UserRole] = mapped_column(...)

    # TODO: is_active — Boolean, default=True, nullable=False
    is_active: Mapped[bool] = mapped_column(...)
