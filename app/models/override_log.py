# app/models/override_log.py

import uuid
from datetime import datetime, timezone
from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class OverrideLog(Base):
    pass
