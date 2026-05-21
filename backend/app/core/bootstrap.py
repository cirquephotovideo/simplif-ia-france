"""Bootstrap initial : création du compte admin et seed des CERFAs."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from ..config import settings
from ..models import User, UserRole, UserPlan, Cerfa
from ..core.security import hash_password


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
    """Crée le compte admin et les CERFAs si la base est vide."""
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
