"""API VaultAccessRequests · demandes d'accès employés."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from ..database import get_db
from ..models import VaultAccessRequest, RequestStatus, RequestPriority

router = APIRouter()


class VaultRequestIn(BaseModel):
    external_id: Optional[str] = None
    employee_name: str
    employee_email: str
    employee_role: str = ""
    employee_dept: str = ""
    employee_avatar: str = ""
    employee_color: str = "#6A6AF4"
    reason: str = ""
    priority: str = "medium"
    initiated_by_admin: bool = False
    thread: list = Field(default_factory=list)


class VaultRequestPatch(BaseModel):
    status: Optional[str] = None
    thread: Optional[list] = None


class ThreadMessage(BaseModel):
    text: str
    from_: Optional[str] = Field(None, alias="from")
    mine: bool = False


@router.get("")
async def list_requests(
    status: Optional[str] = Query(None, description="pending | granted | denied | revoked"),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(VaultAccessRequest).order_by(VaultAccessRequest.requested_at.desc())
    if status:
        stmt = stmt.where(VaultAccessRequest.status == status)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return {"requests": [r.to_dict() for r in items], "total": len(items)}


@router.post("", status_code=201)
async def create_request(payload: VaultRequestIn, db: AsyncSession = Depends(get_db)):
    r = VaultAccessRequest(
        external_id=payload.external_id,
        employee_name=payload.employee_name,
        employee_email=payload.employee_email,
        employee_role=payload.employee_role,
        employee_dept=payload.employee_dept,
        employee_avatar=payload.employee_avatar or "".join(p[0] for p in payload.employee_name.split()[:2]).upper()[:2],
        employee_color=payload.employee_color,
        reason=payload.reason,
        priority=RequestPriority(payload.priority) if payload.priority in [p.value for p in RequestPriority] else RequestPriority.MEDIUM,
        initiated_by_admin=payload.initiated_by_admin,
        thread=payload.thread,
    )
    db.add(r)
    await db.flush()
    return r.to_dict()


@router.patch("/{request_id}")
async def update_request(request_id: str, patch: VaultRequestPatch, db: AsyncSession = Depends(get_db)):
    stmt = select(VaultAccessRequest).where(
        (VaultAccessRequest.external_id == request_id) | (VaultAccessRequest.id == request_id) if _is_uuid(request_id) else (VaultAccessRequest.external_id == request_id)
    )
    result = await db.execute(stmt)
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Demande introuvable")
    if patch.status:
        new_status = RequestStatus(patch.status)
        r.status = new_status
        now = datetime.utcnow()
        if new_status == RequestStatus.GRANTED:
            r.granted_at = now
            r.expires_at = now + timedelta(hours=24)
        elif new_status == RequestStatus.DENIED:
            r.denied_at = now
        elif new_status == RequestStatus.REVOKED:
            r.revoked_at = now
    if patch.thread is not None:
        r.thread = patch.thread
    await db.flush()
    return r.to_dict()


@router.post("/{request_id}/message")
async def append_message(request_id: str, msg: dict, db: AsyncSession = Depends(get_db)):
    """Ajoute un message au thread de conversation."""
    stmt = select(VaultAccessRequest).where(
        (VaultAccessRequest.external_id == request_id) | (VaultAccessRequest.id == request_id) if _is_uuid(request_id) else (VaultAccessRequest.external_id == request_id)
    )
    result = await db.execute(stmt)
    r = result.scalar_one_or_none()
    if not r:
        raise HTTPException(404, "Demande introuvable")
    thread = list(r.thread or [])
    thread.append({
        "from": msg.get("from", "Vous"),
        "text": msg.get("text", ""),
        "at": msg.get("at", "à l'instant"),
        "mine": msg.get("mine", False),
    })
    r.thread = thread
    await db.flush()
    return r.to_dict()


@router.post("/bulk-import")
async def bulk_import(requests: list[VaultRequestIn], db: AsyncSession = Depends(get_db)):
    count = 0
    for payload in requests:
        if payload.external_id:
            existing = await db.execute(select(VaultAccessRequest).where(VaultAccessRequest.external_id == payload.external_id))
            if existing.scalar_one_or_none():
                continue
        r = VaultAccessRequest(
            external_id=payload.external_id,
            employee_name=payload.employee_name,
            employee_email=payload.employee_email,
            employee_role=payload.employee_role,
            employee_dept=payload.employee_dept,
            employee_avatar=payload.employee_avatar,
            employee_color=payload.employee_color,
            reason=payload.reason,
            priority=RequestPriority(payload.priority) if payload.priority in [p.value for p in RequestPriority] else RequestPriority.MEDIUM,
            initiated_by_admin=payload.initiated_by_admin,
            thread=payload.thread,
        )
        db.add(r)
        count += 1
    await db.flush()
    return {"imported": count, "skipped": len(requests) - count}


def _is_uuid(s: str) -> bool:
    try:
        from uuid import UUID
        UUID(s)
        return True
    except Exception:
        return False
