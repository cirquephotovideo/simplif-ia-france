"""Modèle ApiCredential · stockage chiffré (Fernet) des clés d'API gouvernementales et tiers.

Toutes les valeurs sensibles (api_key, client_secret, token...) sont chiffrées au repos
avec MASTER_ENCRYPTION_KEY. Le frontend ne reçoit jamais la valeur en clair, seulement un
booléen `configured` et un aperçu masqué (4 derniers caractères).
"""
import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Boolean, Enum, JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from ..database import Base


class ApiProvider(str, enum.Enum):
    """Catalogue de tous les fournisseurs d'API supportés."""
    # === Identité & SSO ===
    FRANCECONNECT = "franceconnect"
    FRANCECONNECT_PLUS = "franceconnect_plus"
    LAPOSTE_IDN = "laposte_idn"

    # === API gouvernementales (DINUM / api.gouv.fr) ===
    API_PARTICULIER = "api_particulier"            # particulier.api.gouv.fr
    API_ENTREPRISE = "api_entreprise"              # entreprise.api.gouv.fr
    API_SIV = "api_siv"                            # carte grise / immatriculation
    API_POINTS_PERMIS = "api_points_permis"
    API_HISTOVEC = "api_histovec"
    API_IMPOTS = "api_impots"                      # DGFiP
    API_AMELI = "api_ameli"                        # CNAM
    API_FRANCE_TRAVAIL = "api_france_travail"      # ex-Pôle Emploi
    API_CPF = "api_cpf"                            # Mon Compte Formation
    API_ANTS = "api_ants"                          # passeport, CNI
    API_COMEDEC = "api_comedec"                    # actes d'état civil
    API_MES_AIDES = "api_mes_aides"                # 30+ aides sociales
    API_ENEDIS = "api_enedis"                      # data connect (chèque énergie)
    API_DPE_ADEME = "api_dpe_ademe"                # diagnostic énergétique
    API_ANEF = "api_anef"                          # étrangers en France
    API_PARCOURSUP = "api_parcoursup"
    API_EDUCONNECT = "api_educonnect"
    API_PHAROS = "api_pharos"                      # signalement contenus illicites

    # === Open data (clé optionnelle) ===
    LEGIFRANCE = "legifrance"                      # PISTE OAuth2
    JUDILIBRE = "judilibre"                        # PISTE OAuth2
    DATA_GOUV = "data_gouv"                        # API key optionnelle
    INSEE = "insee"                                # SIRENE v3 (OAuth2)
    SERVICE_PUBLIC = "service_public"              # Fiches démarches
    DATAPASS = "datapass"                          # habilitations

    # === Courrier & signature ===
    AR24 = "ar24"                                  # LRE eIDAS
    DOCAPOSTE = "docaposte"                        # LRE La Poste
    UNIVERSIGN = "universign"                      # signature qualifiée
    YOUSIGN = "yousign"
    DOCUSIGN_EU = "docusign_eu"

    # === IA & TTS ===
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MISTRAL = "mistral"
    ELEVENLABS = "elevenlabs"

    # === Paiement ===
    STRIPE = "stripe"
    LYDIA = "lydia"

    # === Sécurité ===
    HCAPTCHA = "hcaptcha"
    SENTRY = "sentry"


class ApiCredential(Base):
    """Stockage clé/valeur chiffré pour un fournisseur d'API."""
    __tablename__ = "api_credentials"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[ApiProvider] = mapped_column(Enum(ApiProvider, name="api_provider"), unique=True, index=True, nullable=False)

    # Valeurs chiffrées (Fernet)
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_id_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    client_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON chiffré (autres champs)

    # Métadonnées en clair
    label: Mapped[str | None] = mapped_column(String(120), nullable=True)
    environment: Mapped[str] = mapped_column(String(20), default="production")  # sandbox / production
    base_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scopes: Mapped[list | None] = mapped_column(JSON, default=list, nullable=True)

    # État
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_test_status: Mapped[str | None] = mapped_column(String(20), nullable=True)  # "ok" | "error" | "untested"
    last_test_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_safe_dict(self) -> dict:
        """Représentation safe pour le frontend : pas de valeurs en clair."""
        from ..services.crypto import decrypt_text

        def _preview(enc: str | None) -> str | None:
            if not enc:
                return None
            try:
                clear = decrypt_text(enc)
                if len(clear) <= 8:
                    return "•" * len(clear)
                return "•" * (len(clear) - 4) + clear[-4:]
            except Exception:
                return "••••"

        return {
            "id": str(self.id),
            "provider": self.provider.value,
            "label": self.label,
            "environment": self.environment,
            "base_url": self.base_url,
            "scopes": self.scopes or [],
            "is_enabled": self.is_enabled,
            "configured": bool(self.api_key_encrypted or self.client_secret_encrypted),
            "api_key_preview": _preview(self.api_key_encrypted),
            "client_id_preview": _preview(self.client_id_encrypted),
            "client_secret_preview": _preview(self.client_secret_encrypted),
            "has_extra": bool(self.extra_encrypted),
            "last_tested_at": self.last_tested_at.isoformat() if self.last_tested_at else None,
            "last_test_status": self.last_test_status,
            "last_test_message": self.last_test_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
