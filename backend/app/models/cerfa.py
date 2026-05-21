"""Modèle catalogue CERFA."""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class Cerfa(Base):
    __tablename__ = "cerfas"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    number: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    # ex: "12100*02"
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    organism: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True, default="autre")

    description: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    service_public_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    field_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    # mapping champs CERFA -> profil utilisateur

    is_prefilled_supported: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    version_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
