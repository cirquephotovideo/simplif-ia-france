"""API admin · gestion des clés d'API gouvernementales et tiers.

Tous les endpoints nécessitent le rôle admin. Les valeurs sensibles sont chiffrées
au repos (Fernet AES-256) et ne sont JAMAIS renvoyées en clair au frontend, sauf
sur l'endpoint /reveal qui exige une re-authentification (mot de passe admin).
"""
import json
from datetime import datetime
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import ApiCredential, ApiProvider, User
from ..core.security import require_admin, verify_password
from ..services.crypto import encrypt_text, decrypt_text

router = APIRouter()


# ===== Catalogue (statique, sert au frontend pour générer les formulaires) =====

PROVIDER_CATALOG: dict[str, dict[str, Any]] = {
    # === Identité & SSO ===
    "franceconnect": {
        "name": "FranceConnect",
        "category": "identity",
        "description": "SSO citoyen vers 1 400+ services publics. Niveau eIDAS substantiel.",
        "fields": ["client_id", "client_secret"],
        "register_url": "https://partenaires.franceconnect.gouv.fr/",
        "docs_url": "https://partenaires.franceconnect.gouv.fr/fcp/fournisseur-service",
        "default_base_url": "https://app.franceconnect.gouv.fr",
        "scopes": ["openid", "profile", "email", "address", "phone"],
    },
    "franceconnect_plus": {
        "name": "FranceConnect+",
        "category": "identity",
        "description": "FranceConnect niveau substantiel renforcé (eIDAS+).",
        "fields": ["client_id", "client_secret"],
        "register_url": "https://partenaires.franceconnect.gouv.fr/monprojet/inscription",
        "default_base_url": "https://app-plus.franceconnect.gouv.fr",
        "scopes": ["openid", "profile", "identite_pivot"],
    },
    "laposte_idn": {
        "name": "La Poste Identité Numérique",
        "category": "identity",
        "description": "Identité numérique niveau substantiel via La Poste.",
        "fields": ["client_id", "client_secret"],
        "register_url": "https://www.idn.laposte.fr/",
        "default_base_url": "https://idn.laposte.fr/api",
    },

    # === API gouvernementales DINUM ===
    "api_particulier": {
        "name": "API Particulier (DINUM)",
        "category": "gouv_data",
        "description": "État civil, situation familiale, quotient familial, statut étudiant, MDPH.",
        "fields": ["api_key"],
        "register_url": "https://datapass.api.gouv.fr/api-particulier",
        "docs_url": "https://api.gouv.fr/les-api/api-particulier",
        "default_base_url": "https://particulier.api.gouv.fr/api",
        "header_format": "X-Api-Key: {api_key}",
    },
    "api_entreprise": {
        "name": "API Entreprise",
        "category": "gouv_data",
        "description": "KBis, URSSAF, fiscale, sociale, certifications. Réservé administrations.",
        "fields": ["api_key"],
        "register_url": "https://datapass.api.gouv.fr/api-entreprise",
        "docs_url": "https://entreprise.api.gouv.fr/developpeurs",
        "default_base_url": "https://entreprise.api.gouv.fr/v3",
        "header_format": "Authorization: Bearer {api_key}",
    },
    "api_siv": {
        "name": "API SIV (carte grise)",
        "category": "gouv_data",
        "description": "Immatriculation : déclaration cession, changement adresse, carte grise.",
        "fields": ["api_key", "client_id"],
        "register_url": "https://datapass.api.gouv.fr/api-siv",
        "docs_url": "https://api.gouv.fr/les-api/api-siv",
    },
    "api_points_permis": {
        "name": "API Mes Points Permis",
        "category": "gouv_data",
        "description": "Solde de points permis en temps réel.",
        "fields": ["api_key"],
        "register_url": "https://datapass.api.gouv.fr/",
        "docs_url": "https://api.gouv.fr/les-api/api-points-permis",
    },
    "api_histovec": {
        "name": "API HistoVec",
        "category": "gouv_data",
        "description": "Historique complet d'un véhicule (utile rachat occasion).",
        "fields": ["api_key"],
        "register_url": "https://histovec.interieur.gouv.fr/",
        "docs_url": "https://api.gouv.fr/les-api/api-histovec",
    },
    "api_impots": {
        "name": "API Impôts Particuliers (DGFiP)",
        "category": "gouv_data",
        "description": "Avis d'imposition, déclaration pré-remplie, attestations.",
        "fields": ["api_key", "client_secret"],
        "register_url": "https://www.impots.gouv.fr/api-particuliers",
        "docs_url": "https://api.gouv.fr/les-api/dgfip_quotient_familial",
    },
    "api_ameli": {
        "name": "API Ameli (CNAM)",
        "category": "gouv_data",
        "description": "Carte Vitale, attestations droits, IJ.",
        "fields": ["client_id", "client_secret"],
        "register_url": "https://assure.ameli.fr/PortailAS/appmanager/PortailAS/assure",
        "docs_url": "https://api.gouv.fr/les-api/api-ameli",
    },
    "api_france_travail": {
        "name": "API France Travail (ex-Pôle Emploi)",
        "category": "gouv_data",
        "description": "Inscription, actualisation, offres emploi (250 000+), formations.",
        "fields": ["client_id", "client_secret"],
        "register_url": "https://francetravail.io/inscription",
        "docs_url": "https://francetravail.io/data/api",
        "default_base_url": "https://api.francetravail.io/partenaire",
        "scopes": ["api_offresdemploiv2", "o2dsoffre", "application_PARTNER_ID"],
    },
    "api_cpf": {
        "name": "API Mon Compte Formation (CPF)",
        "category": "gouv_data",
        "description": "Droits CPF, catalogue formations, inscription.",
        "fields": ["client_id", "client_secret"],
        "register_url": "https://www.moncompteformation.gouv.fr/espace-public/",
        "docs_url": "https://api.gouv.fr/les-api/api-mon-compte-formation",
    },
    "api_ants": {
        "name": "API ANTS",
        "category": "gouv_data",
        "description": "Pré-demande passeport, CNI, permis.",
        "fields": ["api_key"],
        "register_url": "https://ants.gouv.fr/",
        "docs_url": "https://api.gouv.fr/les-api/api-ants",
    },
    "api_comedec": {
        "name": "API COMEDEC (état civil)",
        "category": "gouv_data",
        "description": "Demande dématérialisée d'actes d'état civil aux mairies raccordées.",
        "fields": ["api_key", "client_id"],
        "register_url": "https://ants.gouv.fr/Les-solutions/COMEDEC",
        "docs_url": "https://api.gouv.fr/les-api/api-comedec",
    },
    "api_mes_aides": {
        "name": "API Mes Aides",
        "category": "gouv_data",
        "description": "Simulateur 30+ aides sociales (CAF, CSS, AAH, RSA, prime activité...).",
        "fields": ["api_key"],
        "register_url": "https://mes-aides.gouv.fr/",
        "docs_url": "https://api.gouv.fr/les-api/api-mes-aides",
    },
    "api_enedis": {
        "name": "Enedis Data Connect",
        "category": "gouv_data",
        "description": "Consommation électrique (chèque énergie, MaPrimeRénov).",
        "fields": ["client_id", "client_secret"],
        "register_url": "https://mon-compte-particulier.enedis.fr/data-connect/",
        "docs_url": "https://datahub-enedis.fr/data-connect/",
        "default_base_url": "https://gw.ext.prod.api.enedis.fr",
    },
    "api_dpe_ademe": {
        "name": "API DPE ADEME",
        "category": "gouv_data",
        "description": "Diagnostic de performance énergétique d'un logement.",
        "fields": ["api_key"],
        "register_url": "https://data.ademe.fr/",
        "docs_url": "https://data.ademe.fr/datasets/dpe-v2-logements-existants",
        "default_base_url": "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants",
    },
    "api_anef": {
        "name": "API ANEF (étrangers en France)",
        "category": "gouv_data",
        "description": "Démarches titres de séjour 100% dématérialisés.",
        "fields": ["api_key"],
        "register_url": "https://administration-etrangers-en-france.interieur.gouv.fr/",
    },
    "api_parcoursup": {
        "name": "API Parcoursup",
        "category": "gouv_data",
        "description": "Consultation des formations Parcoursup.",
        "fields": ["api_key"],
        "register_url": "https://www.parcoursup.fr/",
    },
    "api_educonnect": {
        "name": "API EduConnect",
        "category": "gouv_data",
        "description": "SSO famille / élève / enseignant Éducation nationale.",
        "fields": ["client_id", "client_secret"],
        "register_url": "https://educonnect.education.gouv.fr/",
    },
    "api_pharos": {
        "name": "API PHAROS",
        "category": "gouv_data",
        "description": "Signalement contenus illicites en ligne (Ministère Intérieur).",
        "fields": ["api_key"],
        "register_url": "https://www.internet-signalement.gouv.fr/",
    },

    # === Open data ===
    "legifrance": {
        "name": "Légifrance (PISTE)",
        "category": "opendata",
        "description": "Tout le droit français : codes, lois, décrets, JO.",
        "fields": ["client_id", "client_secret"],
        "register_url": "https://piste.gouv.fr/",
        "docs_url": "https://developer.aife.economie.gouv.fr/",
        "default_base_url": "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app",
    },
    "judilibre": {
        "name": "Judilibre (jurisprudence)",
        "category": "opendata",
        "description": "Décisions de justice anonymisées (Cour de cassation).",
        "fields": ["client_id", "client_secret"],
        "register_url": "https://piste.gouv.fr/",
        "docs_url": "https://api.gouv.fr/les-api/api-judilibre",
        "default_base_url": "https://api.piste.gouv.fr/cassation/judilibre/v1.0",
    },
    "data_gouv": {
        "name": "data.gouv.fr",
        "category": "opendata",
        "description": "40 000+ jeux de données publics.",
        "fields": ["api_key"],
        "register_url": "https://www.data.gouv.fr/fr/admin/me/",
        "docs_url": "https://doc.data.gouv.fr/api/reference/",
        "default_base_url": "https://www.data.gouv.fr/api/1",
    },
    "insee": {
        "name": "INSEE Sirene v3",
        "category": "opendata",
        "description": "Entreprises et établissements (OAuth2).",
        "fields": ["client_id", "client_secret"],
        "register_url": "https://api.insee.fr/catalogue/",
        "default_base_url": "https://api.insee.fr/entreprises/sirene/V3",
    },
    "service_public": {
        "name": "Service-Public.fr",
        "category": "opendata",
        "description": "Fiches démarches + CERFAs officiels.",
        "fields": ["api_key"],
        "register_url": "https://www.data.gouv.fr/fr/datasets/service-public-fr-annuaire-de-ladministration/",
        "default_base_url": "https://api-lannuaire.service-public.gouv.fr",
    },
    "datapass": {
        "name": "DataPass",
        "category": "opendata",
        "description": "Plateforme d'habilitations CNIL/RGPD pour APIs gouv.",
        "fields": ["api_key"],
        "register_url": "https://datapass.api.gouv.fr/",
    },

    # === Courrier & signature ===
    "ar24": {
        "name": "AR24 (LRE Docaposte)",
        "category": "courrier",
        "description": "Lettre Recommandée Électronique eIDAS qualifiée (~4,68 €).",
        "fields": ["api_key"],
        "register_url": "https://www.ar24.fr/inscription-pro/",
        "docs_url": "https://www.ar24.fr/api-documentation/",
        "default_base_url": "https://app.ar24.fr/api",
    },
    "docaposte": {
        "name": "Docaposte",
        "category": "courrier",
        "description": "LRE La Poste, signature, identité numérique.",
        "fields": ["client_id", "client_secret"],
        "register_url": "https://www.docaposte.com/",
    },
    "universign": {
        "name": "Universign",
        "category": "signature",
        "description": "Signature électronique qualifiée eIDAS (PSCE).",
        "fields": ["api_key"],
        "register_url": "https://www.universign.com/fr/inscription/",
        "default_base_url": "https://ws.universign.eu/sign/rpc",
    },
    "yousign": {
        "name": "Yousign",
        "category": "signature",
        "description": "Signature électronique simple/avancée/qualifiée.",
        "fields": ["api_key"],
        "register_url": "https://yousign.com/fr/inscription",
        "docs_url": "https://developers.yousign.com/",
        "default_base_url": "https://api.yousign.app/v3",
    },
    "docusign_eu": {
        "name": "DocuSign (EU)",
        "category": "signature",
        "description": "Signature électronique, hébergement européen.",
        "fields": ["client_id", "client_secret"],
        "register_url": "https://www.docusign.fr/",
    },

    # === IA & TTS ===
    "gemini": {
        "name": "Google Gemini",
        "category": "ai",
        "description": "LLM Google (multimodal, long contexte).",
        "fields": ["api_key"],
        "register_url": "https://aistudio.google.com/apikey",
    },
    "openai": {
        "name": "OpenAI",
        "category": "ai",
        "description": "GPT-4o, embeddings, Whisper.",
        "fields": ["api_key"],
        "register_url": "https://platform.openai.com/api-keys",
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "category": "ai",
        "description": "Claude Opus/Sonnet/Haiku.",
        "fields": ["api_key"],
        "register_url": "https://console.anthropic.com/settings/keys",
    },
    "mistral": {
        "name": "Mistral AI",
        "category": "ai",
        "description": "LLM français (Mistral Large, Codestral).",
        "fields": ["api_key"],
        "register_url": "https://console.mistral.ai/api-keys/",
    },
    "elevenlabs": {
        "name": "ElevenLabs (TTS)",
        "category": "ai",
        "description": "Synthèse vocale multilingue pour Maître Léa.",
        "fields": ["api_key"],
        "register_url": "https://elevenlabs.io/app/settings/api-keys",
    },

    # === Paiement ===
    "stripe": {
        "name": "Stripe",
        "category": "payment",
        "description": "Paiements + abonnements Premium.",
        "fields": ["api_key", "client_secret"],  # secret_key + webhook_secret
        "register_url": "https://dashboard.stripe.com/apikeys",
    },
    "lydia": {
        "name": "Lydia Pro",
        "category": "payment",
        "description": "Paiements instantanés.",
        "fields": ["api_key"],
        "register_url": "https://lydia-app.com/pros/",
    },

    # === Sécurité ===
    "hcaptcha": {
        "name": "hCaptcha",
        "category": "security",
        "description": "Anti-bot (alternative reCAPTCHA, RGPD-friendly).",
        "fields": ["api_key", "client_id"],  # secret + sitekey
        "register_url": "https://dashboard.hcaptcha.com/sites",
    },
    "sentry": {
        "name": "Sentry",
        "category": "security",
        "description": "Monitoring d'erreurs.",
        "fields": ["api_key"],
        "register_url": "https://sentry.io/settings/account/api/auth-tokens/",
    },
}


# ===== Schémas Pydantic =====

class ApiCredentialIn(BaseModel):
    api_key: str | None = Field(default=None, description="Clé API en clair (sera chiffrée)")
    client_id: str | None = None
    client_secret: str | None = None
    extra: dict | None = None  # autres champs au format JSON
    label: str | None = None
    environment: str = "production"
    base_url: str | None = None
    scopes: list[str] | None = None
    is_enabled: bool = True


class TestResult(BaseModel):
    status: str  # ok | error
    message: str
    tested_at: str


class RevealIn(BaseModel):
    admin_password: str


# ===== Routes =====

@router.get("/catalog", dependencies=[Depends(require_admin)])
async def get_catalog():
    """Retourne le catalogue de tous les providers + leurs métadonnées."""
    return {"providers": PROVIDER_CATALOG, "count": len(PROVIDER_CATALOG)}


@router.get("", dependencies=[Depends(require_admin)])
async def list_credentials(db: AsyncSession = Depends(get_db)):
    """Liste les credentials configurés (valeurs masquées)."""
    result = await db.execute(select(ApiCredential).order_by(ApiCredential.provider))
    creds = result.scalars().all()
    by_provider = {c.provider.value: c.to_safe_dict() for c in creds}

    # Fusion avec catalogue : tous les providers, même non configurés
    full = []
    for provider_key, meta in PROVIDER_CATALOG.items():
        entry = {
            "provider": provider_key,
            "name": meta["name"],
            "category": meta["category"],
            "description": meta["description"],
            "fields": meta["fields"],
            "register_url": meta.get("register_url"),
            "docs_url": meta.get("docs_url"),
            "default_base_url": meta.get("default_base_url"),
            "default_scopes": meta.get("scopes", []),
            **(by_provider.get(provider_key) or {
                "configured": False,
                "is_enabled": False,
                "last_test_status": "untested",
            }),
        }
        full.append(entry)

    return {"credentials": full, "configured_count": len(by_provider), "total": len(PROVIDER_CATALOG)}


@router.get("/{provider}", dependencies=[Depends(require_admin)])
async def get_credential(provider: str, db: AsyncSession = Depends(get_db)):
    if provider not in PROVIDER_CATALOG:
        raise HTTPException(404, "Provider inconnu")
    try:
        prov_enum = ApiProvider(provider)
    except ValueError:
        raise HTTPException(400, "Provider invalide")
    result = await db.execute(select(ApiCredential).where(ApiCredential.provider == prov_enum))
    cred = result.scalar_one_or_none()
    meta = PROVIDER_CATALOG[provider]
    if not cred:
        return {"provider": provider, "configured": False, "meta": meta}
    return {**cred.to_safe_dict(), "meta": meta}


@router.put("/{provider}", dependencies=[Depends(require_admin)])
async def upsert_credential(provider: str, payload: ApiCredentialIn, db: AsyncSession = Depends(get_db)):
    """Crée ou met à jour les credentials d'un provider. Les valeurs sont chiffrées."""
    if provider not in PROVIDER_CATALOG:
        raise HTTPException(404, "Provider inconnu")
    try:
        prov_enum = ApiProvider(provider)
    except ValueError:
        raise HTTPException(400, "Provider invalide")

    result = await db.execute(select(ApiCredential).where(ApiCredential.provider == prov_enum))
    cred = result.scalar_one_or_none()
    if not cred:
        cred = ApiCredential(provider=prov_enum)
        db.add(cred)

    # Chiffrement des valeurs sensibles
    if payload.api_key is not None:
        cred.api_key_encrypted = encrypt_text(payload.api_key) if payload.api_key else None
    if payload.client_id is not None:
        cred.client_id_encrypted = encrypt_text(payload.client_id) if payload.client_id else None
    if payload.client_secret is not None:
        cred.client_secret_encrypted = encrypt_text(payload.client_secret) if payload.client_secret else None
    if payload.extra is not None:
        cred.extra_encrypted = encrypt_text(json.dumps(payload.extra)) if payload.extra else None

    cred.label = payload.label
    cred.environment = payload.environment or "production"
    cred.base_url = payload.base_url or PROVIDER_CATALOG[provider].get("default_base_url")
    cred.scopes = payload.scopes or PROVIDER_CATALOG[provider].get("scopes", [])
    cred.is_enabled = payload.is_enabled

    await db.flush()
    return cred.to_safe_dict()


@router.delete("/{provider}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_credential(provider: str, db: AsyncSession = Depends(get_db)):
    try:
        prov_enum = ApiProvider(provider)
    except ValueError:
        raise HTTPException(400, "Provider invalide")
    result = await db.execute(select(ApiCredential).where(ApiCredential.provider == prov_enum))
    cred = result.scalar_one_or_none()
    if cred:
        await db.delete(cred)
        await db.flush()


@router.post("/{provider}/test", dependencies=[Depends(require_admin)])
async def test_credential(provider: str, db: AsyncSession = Depends(get_db)) -> TestResult:
    """Effectue un appel test (ping) sur l'API pour vérifier la clé."""
    from ..services.gouv_api_extended import test_provider

    if provider not in PROVIDER_CATALOG:
        raise HTTPException(404, "Provider inconnu")
    try:
        prov_enum = ApiProvider(provider)
    except ValueError:
        raise HTTPException(400, "Provider invalide")

    result = await db.execute(select(ApiCredential).where(ApiCredential.provider == prov_enum))
    cred = result.scalar_one_or_none()
    if not cred or not (cred.api_key_encrypted or cred.client_secret_encrypted):
        return TestResult(status="error", message="Aucune clé configurée", tested_at=datetime.utcnow().isoformat())

    try:
        ok, msg = await test_provider(prov_enum, cred)
        cred.last_tested_at = datetime.utcnow()
        cred.last_test_status = "ok" if ok else "error"
        cred.last_test_message = msg[:500]
        await db.flush()
        return TestResult(status="ok" if ok else "error", message=msg, tested_at=cred.last_tested_at.isoformat())
    except Exception as e:
        cred.last_tested_at = datetime.utcnow()
        cred.last_test_status = "error"
        cred.last_test_message = str(e)[:500]
        await db.flush()
        return TestResult(status="error", message=str(e), tested_at=cred.last_tested_at.isoformat())


@router.post("/{provider}/reveal", dependencies=[Depends(require_admin)])
async def reveal_credential(
    provider: str,
    payload: RevealIn = Body(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Renvoie les valeurs en clair APRÈS re-vérification du mot de passe admin."""
    if not verify_password(payload.admin_password, admin.password_hash):
        raise HTTPException(403, "Mot de passe admin incorrect")

    try:
        prov_enum = ApiProvider(provider)
    except ValueError:
        raise HTTPException(400, "Provider invalide")

    result = await db.execute(select(ApiCredential).where(ApiCredential.provider == prov_enum))
    cred = result.scalar_one_or_none()
    if not cred:
        raise HTTPException(404, "Credential non configuré")

    out: dict[str, Any] = {"provider": provider}
    if cred.api_key_encrypted:
        out["api_key"] = decrypt_text(cred.api_key_encrypted)
    if cred.client_id_encrypted:
        out["client_id"] = decrypt_text(cred.client_id_encrypted)
    if cred.client_secret_encrypted:
        out["client_secret"] = decrypt_text(cred.client_secret_encrypted)
    if cred.extra_encrypted:
        try:
            out["extra"] = json.loads(decrypt_text(cred.extra_encrypted))
        except Exception:
            out["extra"] = {}
    return out


@router.post("/{provider}/toggle", dependencies=[Depends(require_admin)])
async def toggle_credential(provider: str, db: AsyncSession = Depends(get_db)):
    """Active/désactive un provider sans supprimer ses clés."""
    try:
        prov_enum = ApiProvider(provider)
    except ValueError:
        raise HTTPException(400, "Provider invalide")
    result = await db.execute(select(ApiCredential).where(ApiCredential.provider == prov_enum))
    cred = result.scalar_one_or_none()
    if not cred:
        raise HTTPException(404, "Credential non configuré")
    cred.is_enabled = not cred.is_enabled
    await db.flush()
    return cred.to_safe_dict()
