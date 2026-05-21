"""Modèle utilisateur."""
import enum
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SQLEnum, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class UserRole(str, enum.Enum):
    USER = "user"
    PRO = "pro"
    SUPPORT = "support"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class UserPlan(str, enum.Enum):
    FREE = "free"
    PREMIUM = "premium"
    PRO = "pro"
    PRECARITY = "precarity"  # gratuit pour bénéficiaires minima sociaux


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), default="")
    last_name: Mapped[str] = mapped_column(String(100), default="")

    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    plan: Mapped[UserPlan] = mapped_column(SQLEnum(UserPlan), default=UserPlan.FREE, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    franceconnect_sub: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)

    profile: Mapped[dict] = mapped_column(JSON, default=dict)
    # profile contient (chiffré côté service) :
    #   { birthdate, address, caf_id, fiscal_id, family, etc. }

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<User {self.email} ({self.role.value})>"
