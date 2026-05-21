"""Endpoints démarches administratives."""
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import User, Demarche, DemarcheStatus
from ..core.security import get_current_user

router = APIRouter()


class DemarcheIn(BaseModel):
    type: str
    title: str
    total_steps: int = 1
    deadline: datetime | None = None
    data: dict = {}


class DemarcheUpdate(BaseModel):
    status: DemarcheStatus | None = None
    current_step: int | None = None
    data: dict | None = None
    note: str | None = None


@router.post("")
async def create(d: DemarcheIn, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    dem = Demarche(
        user_id=current.id, type=d.type, title=d.title,
        total_steps=d.total_steps, deadline=d.deadline, data=d.data,
        history=[{"ts": datetime.utcnow().isoformat(), "action": "created", "by": str(current.id)}],
    )
    db.add(dem)
    await db.flush()
    return {"id": str(dem.id), "status": dem.status.value, "title": dem.title}


@router.get("")
async def list_dem(
    status: DemarcheStatus | None = None,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Demarche).where(Demarche.user_id == current.id)
    if status:
        q = q.where(Demarche.status == status)
    result = await db.execute(q.order_by(Demarche.updated_at.desc()))
    return [
        {
            "id": str(d.id), "type": d.type, "title": d.title,
            "status": d.status.value, "current_step": d.current_step, "total_steps": d.total_steps,
            "deadline": d.deadline.isoformat() if d.deadline else None,
            "updated_at": d.updated_at.isoformat(),
        }
        for d in result.scalars().all()
    ]


@router.get("/{dem_id}")
async def get_dem(dem_id: UUID, current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Demarche).where(Demarche.id == dem_id, Demarche.user_id == current.id))
    d = r.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Démarche introuvable")
    return {
        "id": str(d.id), "type": d.type, "title": d.title, "status": d.status.value,
        "current_step": d.current_step, "total_steps": d.total_steps,
        "data": d.data, "history": d.history,
        "deadline": d.deadline.isoformat() if d.deadline else None,
    }


@router.patch("/{dem_id}")
async def update_dem(
    dem_id: UUID, payload: DemarcheUpdate,
    current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db),
):
    r = await db.execute(select(Demarche).where(Demarche.id == dem_id, Demarche.user_id == current.id))
    d = r.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Démarche introuvable")
    if payload.status:
        d.status = payload.status
        if payload.status == DemarcheStatus.COMPLETED:
            d.completed_at = datetime.utcnow()
    if payload.current_step is not None:
        d.current_step = payload.current_step
    if payload.data is not None:
        d.data = {**(d.data or {}), **payload.data}
    if payload.note:
        d.history = (d.history or []) + [{"ts": datetime.utcnow().isoformat(), "action": "note", "note": payload.note}]
    return {"id": str(d.id), "status": d.status.value}
