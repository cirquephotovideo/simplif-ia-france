"""Modèle Mail · boîte de réception unifiée (Inbox)."""
import enum
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SQLEnum, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class MailTag(str, enum.Enum):
    CONTACT = "contact"
    SUPPORT = "support"
    PRESS = "press"
    PARTNER = "partner"
    URGENT = "urgent"
    DEMO = "demo"
    WAITLIST = "waitlist"
    INTERNAL = "internal"


class MailPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Mail(Base):
    """Mail unifié · admin inbox + urgents + follow-ups."""
    __tablename__ = "mails"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Identifiants externes (compat localStorage existant)
    external_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    thread_of: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)

    # Expéditeur
    from_name: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    from_email: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    initials: Mapped[str] = mapped_column(String(8), default="")
    avatar_var: Mapped[int] = mapped_column(default=1)

    # Contenu
    subject: Mapped[str] = mapped_column(String(500), default="")
    preview: Mapped[str] = mapped_column(String(500), default="")
    body: Mapped[str] = mapped_column(Text, default="")
    ai_suggest: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Classification
    tag: Mapped[MailTag] = mapped_column(SQLEnum(MailTag), default=MailTag.CONTACT, index=True)
    priority: Mapped[MailPriority] = mapped_column(SQLEnum(MailPriority), default=MailPriority.MEDIUM, index=True)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_follow_up: Mapped[bool] = mapped_column(Boolean, default=False)

    # États
    unread: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    starred: Mapped[bool] = mapped_column(Boolean, default=False)
    archived: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    removed: Mapped[bool] = mapped_column(Boolean, default=False, index=True)  # soft delete

    # Réponses
    admin_reply_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_reply_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    lea_took_over: Mapped[bool] = mapped_column(Boolean, default=False)
    demarche_launched: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Fil de discussion (liste de messages JSON)
    # Format : [{ "author": "them|you|lea", "from": "...", "body": "...", "time": "..." }]
    thread: Mapped[list] = mapped_column(JSON, default=list)

    # Owner (admin qui gère ce mail)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Timestamps
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Index combiné fréquent
    __table_args__ = (
        Index("ix_mails_archived_received", "archived", "received_at"),
        Index("ix_mails_urgent_unread", "is_urgent", "unread"),
    )

    def __repr__(self) -> str:
        return f"<Mail {self.subject[:40]!r} from {self.from_name}>"

    def to_dict(self) -> dict:
        """Sérialisation compatible localStorage existant."""
        return {
            "id": self.external_id or str(self.id),
            "from": self.from_name,
            "email": self.from_email,
            "initials": self.initials,
            "avatarVar": self.avatar_var,
            "subject": self.subject,
            "preview": self.preview,
            "body": self.body,
            "tag": self.tag.value if hasattr(self.tag, "value") else str(self.tag),
            "priority": self.priority.value if hasattr(self.priority, "value") else str(self.priority),
            "urgent": self.is_urgent,
            "isFollowUp": self.is_follow_up,
            "unread": self.unread,
            "starred": self.starred,
            "archived": self.archived,
            "adminReplyText": self.admin_reply_text,
            "leaTookOver": self.lea_took_over,
            "demarche": self.demarche_launched,
            "threadOf": self.thread_of,
            "thread": self.thread or [],
            "aiSuggest": self.ai_suggest,
            "time": self._humanize_time(),
            "timestamp": int(self.received_at.timestamp() * 1000) if self.received_at else None,
            "receivedAt": self.received_at.isoformat() if self.received_at else None,
        }

    def _humanize_time(self) -> str:
        """Format relatif court pour affichage UI."""
        if not self.received_at:
            return ""
        delta = datetime.utcnow() - self.received_at.replace(tzinfo=None) if self.received_at.tzinfo else datetime.utcnow() - self.received_at
        seconds = delta.total_seconds()
        if seconds < 60: return f"il y a {int(seconds)}s"
        if seconds < 3600: return f"il y a {int(seconds/60)} min"
        if seconds < 86400: return f"il y a {int(seconds/3600)} h"
        if seconds < 604800: return f"il y a {int(seconds/86400)}j"
        return self.received_at.strftime("%d %b")
