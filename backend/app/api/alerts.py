"""Endpoints du système d'alarmes utilisateur."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, and_, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..models.alert import Alert, AlertSeverity, AlertCategory
from ..core.security import get_current_user

router = APIRouter()


@router.get("")
async def list_alerts(
    only_unread: bool = Query(False, description="Filtrer alertes non lues uniquement"),
    severity: Optional[AlertSeverity] = Query(None),
    category: Optional[AlertCategory] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Liste les alertes de l'utilisateur connecté, plus récente d'abord."""
    q = select(Alert).where(Alert.user_id == current.id)
    if only_unread:
        q = q.where(Alert.is_read == False)
    if severity:
        q = q.where(Alert.severity == severity)
    if category:
        q = q.where(Alert.category == category)
    q = q.order_by(Alert.last_seen_at.desc()).limit(limit)
    result = await db.execute(q)
    alerts = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "severity": a.severity.value,
            "category": a.category.value,
            "title": a.title,
            "message": a.message,
            "context": a.context,
            "is_read": a.is_read,
            "is_acknowledged": a.is_acknowledged,
            "occurrences": a.occurrences,
            "first_seen_at": a.first_seen_at.isoformat(),
            "last_seen_at": a.last_seen_at.isoformat(),
        }
        for a in alerts
    ]


@router.get("/summary")
async def alerts_summary(
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compteurs : total / non lus / par sévérité (pour badge UI)."""
    total = await db.scalar(
        select(func.count(Alert.id)).where(Alert.user_id == current.id)
    )
    unread = await db.scalar(
        select(func.count(Alert.id)).where(
            and_(Alert.user_id == current.id, Alert.is_read == False)
        )
    )
    by_severity_q = (
        select(Alert.severity, func.count(Alert.id))
        .where(and_(Alert.user_id == current.id, Alert.is_acknowledged == False))
        .group_by(Alert.severity)
    )
    by_severity_result = await db.execute(by_severity_q)
    by_severity = {row[0].value: row[1] for row in by_severity_result.all()}
    has_critical = (by_severity.get("critical", 0) > 0) or (by_severity.get("high", 0) > 0)
    return {
        "total": total or 0,
        "unread": unread or 0,
        "by_severity": by_severity,
        "needs_attention": has_critical,
    }


@router.post("/{alert_id}/read")
async def mark_read(
    alert_id: UUID,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Alert).where(and_(Alert.id == alert_id, Alert.user_id == current.id))
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    alert.is_read = True
    return {"ok": True}


@router.post("/{alert_id}/acknowledge")
async def acknowledge(
    alert_id: UUID,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marque l'alerte comme traitée — sort des compteurs critiques."""
    result = await db.execute(
        select(Alert).where(and_(Alert.id == alert_id, Alert.user_id == current.id))
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    alert.is_read = True
    alert.is_acknowledged = True
    alert.auto_resolved_at = datetime.utcnow()
    return {"ok": True}


@router.post("/read-all")
async def mark_all_read(
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        update(Alert)
        .where(and_(Alert.user_id == current.id, Alert.is_read == False))
        .values(is_read=True)
    )
    return {"ok": True}


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: UUID,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Supprime une alerte traitée (les alertes critiques non-ack ne peuvent pas être effacées)."""
    result = await db.execute(
        select(Alert).where(and_(Alert.id == alert_id, Alert.user_id == current.id))
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    if alert.severity in (AlertSeverity.CRITICAL, AlertSeverity.HIGH) and not alert.is_acknowledged:
        raise HTTPException(
            status_code=409,
            detail="Cette alerte doit être 'acknowledged' avant d'être supprimée.",
        )
    await db.delete(alert)
    return None
