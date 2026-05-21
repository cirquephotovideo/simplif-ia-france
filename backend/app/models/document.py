"""Modèle document du coffre-fort."""
import enum
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SQLEnum, Integer, ForeignKey, LargeBinary, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class DocumentCategory(str, enum.Enum):
    # ── Catégories de base (vie personnelle)
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

    # ── Pense-Maison (Premium) : modules du foyer
    PM_FOYER = "pm_foyer"               # Adresse, bail, gardien
    PM_ABONNEMENTS = "pm_abonnements"   # Contrats fournisseurs
    PM_GARANTIES = "pm_garanties"       # Achats, factures, garanties
    PM_PRETS = "pm_prets"               # Prêts immo/conso, échéanciers
    PM_ANIMAUX = "pm_animaux"           # Vétérinaire, vaccins
    PM_ENTRETIEN = "pm_entretien"       # Chaudière, VMC, ramonage
    PM_INVENTAIRE = "pm_inventaire"     # Inventaire assurance habitation

    # ── Suite Pro (auto-entrepreneur / TPE)
    PRO_FACTURE = "pro_facture"
    PRO_DEVIS = "pro_devis"
    PRO_NOTE_FRAIS = "pro_note_frais"
    PRO_URSSAF = "pro_urssaf"
    PRO_TVA = "pro_tva"
    PRO_BILAN = "pro_bilan"
    PRO_RELANCE = "pro_relance"

    AUTRE = "autre"


# Catégories nécessitant une vérification PIN supplémentaire avant download
# (stockées comme strings pour matcher Document.category qui est str)
SENSITIVE_CATEGORIES = {
    DocumentCategory.IDENTITE.value,
    DocumentCategory.BANQUE.value,
    DocumentCategory.SANTE.value,
    DocumentCategory.JUSTICE.value,
    DocumentCategory.PM_PRETS.value,
}


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # ⚠️ Stocké en String (pas SQLEnum) pour permettre d'ajouter de nouvelles catégories
    # sans migration ALTER TYPE en prod. Validation côté code via DocumentCategory(...)
    category: Mapped[str] = mapped_column(String(50), default=DocumentCategory.AUTRE.value, index=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), default="application/octet-stream")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)

    # Stockage chiffré : soit blob inline, soit chemin S3/disk
    storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    encrypted_blob: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    # ── Sécurité renforcée ──
    # HMAC-SHA256 du contenu en clair (hex) — vérifie l'intégrité au téléchargement
    integrity_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # Version du schéma de chiffrement (permet rotation de clé future)
    crypto_version: Mapped[int] = mapped_column(Integer, default=1)
    # Compteur de téléchargements (pour détection d'activité suspecte)
    download_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Métadonnées (chiffrées par le service)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    # ex: { issuer, issued_date, expires_at, ocr_extracted }

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    # Soft-delete : purge définitive après X jours
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
