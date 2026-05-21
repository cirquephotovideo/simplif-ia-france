"""Modèle VaultAccessRequest · demandes d'accès au coffre par employés."""
import enum
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SQLEnum, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class RequestStatus(str, enum.Enum):
    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    REVOKED = "revoked"


class RequestPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VaultAccessRequest(Base):
    """Demande d'accès au coffre par un employé + thread de conversation."""
    __tablename__ = "vault_access_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    external_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)

    # Employé demandeur
    employee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    employee_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    employee_role: Mapped[str] = mapped_column(String(120), default="")
    employee_dept: Mapped[str] = mapped_column(String(120), default="")
    employee_avatar: Mapped[str] = mapped_column(String(8), default="")
    employee_color: Mapped[str] = mapped_column(String(20), default="#6A6AF4")

    # Demande
    reason: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[RequestPriority] = mapped_column(SQLEnum(RequestPriority), default=RequestPriority.MEDIUM, index=True)
    status: Mapped[RequestStatus] = mapped_column(SQLEnum(RequestStatus), default=RequestStatus.PENDING, index=True)
    initiated_by_admin: Mapped[bool] = mapped_column(default=False)

    # Thread de conversation (chat)
    # Format : [{ "from": "...", "text": "...", "at": "...", "mine": false }]
    thread: Mapped[list] = mapped_column(JSON, default=list)

    # Liens
    admin_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Timestamps
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    granted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    denied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_vault_req_status_requested", "status", "requested_at"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.external_id or str(self.id),
            "name": self.employee_name,
            "email": self.employee_email,
            "role": self.employee_role,
            "dept": self.employee_dept,
            "avatar": self.employee_avatar,
            "color": self.employee_color,
            "reason": self.reason,
            "priority": self.priority.value if hasattr(self.priority, "value") else str(self.priority),
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "initiatedByAdmin": self.initiated_by_admin,
            "thread": self.thread or [],
            "time": self._humanize_time(),
            "requestedAt": self.requested_at.isoformat() if self.requested_at else None,
            "grantedAt": self.granted_at.isoformat() if self.granted_at else None,
            "deniedAt": self.denied_at.isoformat() if self.denied_at else None,
        }

    def _humanize_time(self) -> str:
        if not self.requested_at:
            return ""
        ref = self.requested_at.replace(tzinfo=None) if self.requested_at.tzinfo else self.requested_at
        delta = (datetime.utcnow() - ref).total_seconds()
        if delta < 60: return f"il y a {int(delta)}s"
        if delta < 3600: return f"il y a {int(delta/60)} min"
        if delta < 86400: return f"il y a {int(delta/3600)} h"
        return f"il y a {int(delta/86400)}j"
