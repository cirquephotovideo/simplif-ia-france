"""Modèle document du coffre-fort."""
import enum
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SQLEnum, Integer, ForeignKey, LargeBinary, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class DocumentCategory(str, enum.Enum):
    IDENTITE = "identite"
    SANTE = "sante"
    LOGEMENT = "logement"
    TRAVAIL = "travail"
    FAMILLE = "famille"
    VEHICULE = "vehicule"
    BANQUE = "banque"
    JUSTICE = "justice"
    ETUDES = "etudes"
    ETRANGER = "etranger"
    ENERGIE = "energie"
    AUTRE = "autre"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[DocumentCategory] = mapped_column(SQLEnum(DocumentCategory), default=DocumentCategory.AUTRE, index=True)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)

    # Stockage chiffré : soit blob inline, soit chemin S3/disk
    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    encrypted_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    # Métadonnées (chiffrées par le service)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    # ex: { issuer, issued_date, expires_at, ocr_extracted }

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
