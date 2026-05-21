"""Modèle d'alerte (système d'alarme du compte utilisateur + admin)."""
import enum
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SQLEnum, ForeignKey, JSON, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class AlertSeverity(str, enum.Enum):
    INFO = "info"          # Notification informative (ex: nouveau document)
    LOW = "low"            # Document expire bientôt (>7j)
    MEDIUM = "medium"      # Échéance dans 24-48h, login depuis nouvel appareil
    HIGH = "high"          # Échec de PIN, bulk download, document expiré
    CRITICAL = "critical"  # 5 logins échoués, tentative tampering, export massif


class AlertCategory(str, enum.Enum):
    VAULT_EXPIRY = "vault_expiry"            # Document arrive à échéance
    VAULT_TAMPER = "vault_tamper"            # HMAC invalide → fichier modifié
    VAULT_BULK = "vault_bulk"                # Bulk download détecté
    VAULT_PIN_FAILED = "vault_pin_failed"    # Mauvais PIN sur catégorie sensible
    AUTH_FAILED = "auth_failed"              # Échec de login
    AUTH_NEW_DEVICE = "auth_new_device"      # Login depuis nouvel UA/IP
    AUTH_BREACH = "auth_breach"              # Tentative brute-force
    DEMARCHE_DEADLINE = "demarche_deadline"  # Démarche admin à faire bientôt
    SYSTEM = "system"                        # Annonce système


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
        index=True, nullable=True,
    )

    severity: Mapped[AlertSeverity] = mapped_column(SQLEnum(AlertSeverity), default=AlertSeverity.INFO, index=True)
    category: Mapped[AlertCategory] = mapped_column(SQLEnum(AlertCategory), index=True)

    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(String(1000))

    # Données contextuelles : ip, ua, target_id, etc.
    context: Mapped[dict] = mapped_column(JSON, default=dict)

    # État
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Compteur d'occurrences (regroupe les alertes similaires)
    occurrences: Mapped[int] = mapped_column(Integer, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
