import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Enum as SAEnum, DateTime
from sqlalchemy.dialects.postgresql import UUID


from app.core.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    agent = "agent"
    buyer = "buyer"
    seller = "seller"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        type=DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        type=DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    full_name: Mapped[str | None] = mapped_column(nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole), nullable=False, default=UserRole.buyer
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
