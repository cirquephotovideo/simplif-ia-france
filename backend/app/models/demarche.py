"""Modèle démarche administrative."""
import enum
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SQLEnum, ForeignKey, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class DemarcheStatus(str, enum.Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    WAITING_USER = "waiting_user"
    WAITING_EXTERNAL = "waiting_external"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Demarche(Base):
    __tablename__ = "demarches"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)

    type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # ex: "rapo_caf", "remise_gracieuse_fiscale", "renouvellement_cni", ...
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    status: Mapped[DemarcheStatus] = mapped_column(SQLEnum(DemarcheStatus), default=DemarcheStatus.DRAFT, index=True)
    current_step: Mapped[int] = mapped_column(Integer, default=0)
    total_steps: Mapped[int] = mapped_column(Integer, default=1)

    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    data: Mapped[dict] = mapped_column(JSON, default=dict)
    # snapshot des champs collectés (chiffré par service si sensible)

    history: Mapped[list] = mapped_column(JSON, default=list)
    # liste d'événements [{ts, action, by, note}]

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
