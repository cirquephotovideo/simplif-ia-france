"""Système d'alarmes : création + agrégation + délivrance.

Une alerte est :
  - persistée en DB (table `alerts`)
  - regroupée si elle se répète dans la fenêtre (dedup)
  - lue par les endpoints `/api/alerts`

Règles automatiques :
  - VAULT_EXPIRY : 30j / 7j / 1j avant la date `expires_at`
  - VAULT_TAMPER : HMAC ne matche pas
  - VAULT_BULK : > 10 downloads en 10s
  - VAULT_PIN_FAILED : mauvais PIN sur catégorie sensible
  - AUTH_FAILED : login refusé
  - AUTH_NEW_DEVICE : IP + UA jamais vus pour ce user
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.alert import Alert, AlertSeverity, AlertCategory


# Fenêtre de dédup : si même catégorie sur même user dans cette fenêtre,
# on incrémente occurrences au lieu de créer une nouvelle alerte
DEDUP_WINDOW = timedelta(minutes=15)


async def raise_alert(
    db: AsyncSession,
    *,
    user_id: Optional[UUID],
    category: AlertCategory,
    severity: AlertSeverity,
    title: str,
    message: str,
    context: Optional[dict] = None,
) -> Alert:
    """Crée ou dédupe une alerte."""
    now = datetime.utcnow()
    context = context or {}

    # Cherche une alerte récente similaire pour ce user/category (dédup)
    cutoff = now - DEDUP_WINDOW
    q = select(Alert).where(
        and_(
            Alert.category == category,
            Alert.user_id == user_id,
            Alert.last_seen_at >= cutoff,
            Alert.is_acknowledged == False,
        )
    ).order_by(Alert.last_seen_at.desc())
    result = await db.execute(q)
    existing = result.scalars().first()

    if existing:
        existing.occurrences += 1
        existing.last_seen_at = now
        # Promouvoir la sévérité si la nouvelle est plus haute
        if _severity_rank(severity) > _severity_rank(existing.severity):
            existing.severity = severity
        existing.message = message
        existing.context = {**existing.context, **context}
        return existing

    alert = Alert(
        user_id=user_id,
        category=category,
        severity=severity,
        title=title,
        message=message,
        context=context,
    )
    db.add(alert)
    return alert


def _severity_rank(sev: AlertSeverity) -> int:
    return {
        AlertSeverity.INFO: 0,
        AlertSeverity.LOW: 1,
        AlertSeverity.MEDIUM: 2,
        AlertSeverity.HIGH: 3,
        AlertSeverity.CRITICAL: 4,
    }.get(sev, 0)


# ─────────────────────────────────────────────────────────────────────
#  Helpers prêts à l'emploi pour les endpoints
# ─────────────────────────────────────────────────────────────────────

async def alert_vault_tamper(
    db: AsyncSession, user_id: UUID, doc_id: UUID, doc_name: str
) -> Alert:
    return await raise_alert(
        db,
        user_id=user_id,
        category=AlertCategory.VAULT_TAMPER,
        severity=AlertSeverity.CRITICAL,
        title="🚨 Document corrompu détecté",
        message=f"Le document « {doc_name} » a un hash d'intégrité invalide. "
                f"Ne pas l'utiliser. Possible manipulation côté stockage.",
        context={"document_id": str(doc_id), "document_name": doc_name},
    )


async def alert_vault_bulk(
    db: AsyncSession, user_id: UUID, count_in_10s: int, ip: str | None = None
) -> Alert:
    return await raise_alert(
        db,
        user_id=user_id,
        category=AlertCategory.VAULT_BULK,
        severity=AlertSeverity.HIGH,
        title="⚠️ Téléchargement massif inhabituel",
        message=f"{count_in_10s} documents téléchargés en 10 secondes. "
                f"Si ce n'était pas vous, change ton mot de passe immédiatement.",
        context={"count": count_in_10s, "ip": ip},
    )


async def alert_vault_pin_failed(
    db: AsyncSession, user_id: UUID, category_name: str, attempts: int
) -> Alert:
    sev = AlertSeverity.CRITICAL if attempts >= 5 else AlertSeverity.HIGH
    return await raise_alert(
        db,
        user_id=user_id,
        category=AlertCategory.VAULT_PIN_FAILED,
        severity=sev,
        title="🔐 PIN incorrect sur catégorie sensible",
        message=f"{attempts} tentative(s) PIN ratée(s) pour {category_name}.",
        context={"failed_category": category_name, "attempts": attempts},
    )


async def alert_vault_expiry(
    db: AsyncSession, user_id: UUID, doc_name: str, days_left: int, doc_id: UUID
) -> Alert:
    if days_left <= 1:
        sev, prefix = AlertSeverity.HIGH, "🚨 Expire demain"
    elif days_left <= 7:
        sev, prefix = AlertSeverity.MEDIUM, "⏰ Expire dans la semaine"
    else:
        sev, prefix = AlertSeverity.LOW, "📅 Expire bientôt"
    return await raise_alert(
        db,
        user_id=user_id,
        category=AlertCategory.VAULT_EXPIRY,
        severity=sev,
        title=f"{prefix} : {doc_name}",
        message=f"Le document « {doc_name} » expire dans {days_left} jour(s).",
        context={"document_id": str(doc_id), "days_left": days_left},
    )


async def alert_auth_failed(
    db: AsyncSession, user_id: Optional[UUID], email: str, ip: str | None, attempts: int
) -> Alert:
    sev = AlertSeverity.CRITICAL if attempts >= 5 else AlertSeverity.MEDIUM
    return await raise_alert(
        db,
        user_id=user_id,
        category=AlertCategory.AUTH_FAILED,
        severity=sev,
        title="🔒 Échec de connexion",
        message=f"Tentative(s) ratée(s) sur le compte {email} (×{attempts}).",
        context={"email": email, "ip": ip, "attempts": attempts},
    )


async def alert_auth_new_device(
    db: AsyncSession, user_id: UUID, ip: str | None, user_agent: str | None
) -> Alert:
    return await raise_alert(
        db,
        user_id=user_id,
        category=AlertCategory.AUTH_NEW_DEVICE,
        severity=AlertSeverity.MEDIUM,
        title="💻 Nouvelle connexion détectée",
        message="Connexion depuis un appareil/IP qu'on n'avait jamais vu.",
        context={"ip": ip, "user_agent": user_agent[:200] if user_agent else None},
    )
