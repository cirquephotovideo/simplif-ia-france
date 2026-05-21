"""Endpoints admin (back-office)."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..database import get_db
from ..models import User, Demarche, Document, Cerfa, AuditLog, DemarcheStatus, UserPlan
from ..core.security import require_admin

router = APIRouter()


@router.get("/dashboard", dependencies=[Depends(require_admin)])
async def dashboard(db: AsyncSession = Depends(get_db)):
    week_ago = datetime.utcnow() - timedelta(days=7)
    users_total = (await db.execute(select(func.count()).select_from(User))).scalar()
    users_active = (await db.execute(select(func.count()).where(User.is_active == True).select_from(User))).scalar()
    users_premium = (await db.execute(select(func.count()).where(User.plan == UserPlan.PREMIUM).select_from(User))).scalar()
    dem_in_progress = (await db.execute(select(func.count()).where(Demarche.status == DemarcheStatus.IN_PROGRESS).select_from(Demarche))).scalar()
    dem_completed_week = (await db.execute(select(func.count()).where(Demarche.completed_at >= week_ago).select_from(Demarche))).scalar()
    docs_total = (await db.execute(select(func.count()).where(Document.is_deleted == False).select_from(Document))).scalar()
    cerfas_count = (await db.execute(select(func.count()).select_from(Cerfa))).scalar()
    recent_audit = await db.execute(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(20))

    return {
        "users": {"total": users_total, "active": users_active, "premium": users_premium},
        "demarches": {"in_progress": dem_in_progress, "completed_7d": dem_completed_week},
        "vault": {"docs": docs_total},
        "cerfas": cerfas_count,
        "recent_activity": [
            {"ts": a.timestamp.isoformat(), "action": a.action, "actor": a.actor_email, "success": a.success}
            for a in recent_audit.scalars().all()
        ],
    }


@router.get("/audit", dependencies=[Depends(require_admin)])
async def audit_logs(
    skip: int = 0, limit: int = 100,
    action: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(AuditLog)
    if action:
        q = q.where(AuditLog.action == action)
    q = q.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
    result = await db.execute(q)
    return [
        {
            "id": str(a.id), "timestamp": a.timestamp.isoformat(),
            "actor": a.actor_email, "action": a.action,
            "target_type": a.target_type, "target_id": a.target_id,
            "ip": str(a.ip_address) if a.ip_address else None,
            "success": a.success,
        }
        for a in result.scalars().all()
    ]
