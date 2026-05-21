"""Bootstrap initial : création du compte admin et seed des CERFAs."""
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..config import settings
from ..models import User, UserRole, UserPlan, Cerfa
from ..core.security import hash_password


# Migrations lightweight au démarrage (PostgreSQL).
# Idempotent — peut tourner à chaque boot sans casse.
MIGRATIONS_SQL = [
    # documents.category : passer de enum à varchar (pour pouvoir ajouter
    # de nouvelles catégories sans ALTER TYPE)
    "ALTER TABLE documents ALTER COLUMN category TYPE varchar(50) USING category::text",
    # Nouvelles colonnes du Document (Phase sécurité renforcée)
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS integrity_hash varchar(64)",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS crypto_version integer DEFAULT 1",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS download_count integer DEFAULT 0",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS last_accessed_at timestamptz",
    "ALTER TABLE documents ADD COLUMN IF NOT EXISTS deleted_at timestamptz",
]


async def run_safe_migrations(db: AsyncSession) -> None:
    """Applique les migrations idempotentes (silencieuse sur erreur connue)."""
    for sql in MIGRATIONS_SQL:
        try:
            await db.execute(text(sql))
            await db.commit()
            logger.debug(f"✓ Migration OK: {sql[:80]}")
        except Exception as e:
            # Erreurs attendues : colonne déjà existante, type déjà varchar, table absente
            msg = str(e).lower()
            if any(k in msg for k in ["already exists", "does not exist", "cannot cast", "already of"]):
                logger.debug(f"↪ migration skip ({sql[:50]}): {str(e)[:80]}")
            else:
                logger.warning(f"⚠ migration failed ({sql[:50]}): {e}")
            await db.rollback()


REAL_CERFAS = [
    # DGFiP
    ("10330*28", "Déclaration de revenus 2042", "DGFiP", "impots", True),
    ("11222*25", "Déclaration complémentaire 2042-C", "DGFiP", "impots", True),
    ("10334*25", "Revenus fonciers 2044", "DGFiP", "impots", True),
    ("11423*25", "Réductions et crédits d'impôt 2042-RICI", "DGFiP", "impots", True),
    ("2735-SD", "Déclaration de don manuel", "DGFiP", "impots", False),
    ("3310-CA3", "Déclaration de TVA", "DGFiP", "impots", False),
    ("1447-M-SD", "Cotisation foncière des entreprises (CFE)", "DGFiP", "impots", False),
    # ANTS
    ("12100*02", "Carte nationale d'identité (majeur)", "ANTS / mairie", "identite", True),
    ("12101*02", "Carte nationale d'identité (mineur)", "ANTS / mairie", "identite", True),
    ("12434*04", "Passeport biométrique (majeur)", "ANTS / mairie", "identite", True),
    ("12411*05", "Passeport biométrique (mineur)", "ANTS / mairie", "identite", True),
    # Véhicule
    ("13754*04", "Duplicata de certificat d'immatriculation", "ANTS", "vehicule", True),
    ("15776*02", "Déclaration de cession d'un véhicule", "ANTS", "vehicule", True),
    ("13750*05", "Mandat à un professionnel (carte grise)", "ANTS", "vehicule", False),
    # Justice
    ("16146*03", "Demande d'aide juridictionnelle", "Bureau d'aide juridictionnelle", "justice", True),
    ("10071*15", "Demande de bulletin n°3 du casier judiciaire", "CJN", "justice", True),
    # Santé
    ("12485*04", "Déclaration de médecin traitant", "CNAM · Ameli", "sante", True),
    ("12504*09", "Demande de complémentaire santé solidaire (C2S)", "CNAM", "sante", True),
    ("11580*06", "Demande de carte Vitale", "CNAM · Ameli", "sante", True),
    ("11383*02", "Avis d'arrêt de travail (volet salarié)", "CNAM", "sante", False),
    # Handicap
    ("15692*01", "Formulaire unique de demande à la MDPH", "MDPH", "handicap", True),
    ("15695*01", "Certificat médical accompagnant la demande MDPH", "MDPH (médecin)", "handicap", False),
    # Logement
    ("14069*04", "Demande de logement social (SNE)", "Préfecture · SNE", "logement", True),
    ("15183*02", "Recours DALO", "Commission de médiation départementale", "logement", True),
    # Famille
    ("12668*04", "Reconnaissance d'enfant", "Mairie · état civil", "famille", True),
    ("15725*03", "Déclaration conjointe de PACS (sous-seing privé)", "Mairie / notaire", "famille", True),
    # Travail
    ("14086*04", "Attestation employeur destinée à France Travail", "Employeur", "travail", False),
    # Étranger
    ("15614*02", "Demande de titre de séjour", "Préfecture · ANEF", "etranger", True),
    ("12753*04", "Attestation d'accueil", "Mairie", "etranger", True),
]


async def bootstrap_admin(db: AsyncSession) -> None:
    """Applique les migrations + crée le compte admin et seed des CERFAs."""
    # 1. Migrations idempotentes (colonnes manquantes, type enum→varchar…)
    await run_safe_migrations(db)

    if not settings.ADMIN_PASSWORD:
        logger.warning("ADMIN_PASSWORD vide, skip bootstrap admin.")
        return

    result = await db.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
    existing = result.scalar_one_or_none()
    if not existing:
        admin = User(
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            first_name=settings.ADMIN_FIRST_NAME,
            last_name=settings.ADMIN_LAST_NAME,
            role=UserRole.SUPERADMIN,
            plan=UserPlan.PRO,
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        await db.commit()
        logger.info(f"✅ Compte admin créé : {settings.ADMIN_EMAIL}")

    # Seed CERFAs
    result = await db.execute(select(Cerfa).limit(1))
    if result.scalar_one_or_none() is None:
        for number, name, organism, category, prefilled in REAL_CERFAS:
            db.add(Cerfa(
                number=number, name=name, organism=organism,
                category=category, is_prefilled_supported=prefilled,
                service_public_url=f"https://www.service-public.fr/particuliers/recherche?keyword=cerfa+{number.split('*')[0]}",
            ))
        await db.commit()
        logger.info(f"✅ {len(REAL_CERFAS)} CERFAs seedés")
