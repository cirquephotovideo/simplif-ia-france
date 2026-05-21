"""API Mails · CRUD boîte de réception unifiée."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from datetime import datetime

from ..database import get_db
from ..models import Mail, MailTag, MailPriority

router = APIRouter()


class MailIn(BaseModel):
    external_id: Optional[str] = None
    from_name: str = Field(default="")
    from_email: str = Field(default="")
    initials: str = Field(default="")
    avatar_var: int = Field(default=1)
    subject: str = Field(default="")
    preview: str = Field(default="")
    body: str = Field(default="")
    tag: Optional[str] = "contact"
    priority: Optional[str] = "medium"
    is_urgent: bool = False
    is_follow_up: bool = False
    unread: bool = True
    starred: bool = False
    archived: bool = False
    thread_of: Optional[str] = None
    thread: list = Field(default_factory=list)
    ai_suggest: Optional[str] = None


class MailPatch(BaseModel):
    unread: Optional[bool] = None
    starred: Optional[bool] = None
    archived: Optional[bool] = None
    removed: Optional[bool] = None
    admin_reply_text: Optional[str] = None
    lea_took_over: Optional[bool] = None
    demarche_launched: Optional[str] = None
    thread: Optional[list] = None


@router.get("")
async def list_mails(
    filter: str = Query("all", description="all | unread | urgent | starred | archived | tag:contact"),
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Liste les mails avec filtre."""
    stmt = select(Mail).where(Mail.removed == False).order_by(Mail.received_at.desc())

    if filter == "unread":
        stmt = stmt.where(Mail.unread == True, Mail.archived == False)
    elif filter == "urgent":
        stmt = stmt.where(Mail.is_urgent == True, Mail.archived == False)
    elif filter == "starred":
        stmt = stmt.where(Mail.starred == True, Mail.archived == False)
    elif filter == "archived":
        stmt = stmt.where(Mail.archived == True)
    elif filter.startswith("tag:"):
        tag = filter.split(":", 1)[1]
        stmt = stmt.where(Mail.tag == tag, Mail.archived == False)
    elif filter == "all":
        stmt = stmt.where(Mail.archived == False)

    if search:
        s = f"%{search.lower()}%"
        stmt = stmt.where(
            func.lower(Mail.from_name).like(s) |
            func.lower(Mail.subject).like(s) |
            func.lower(Mail.preview).like(s)
        )

    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    mails = result.scalars().all()
    return {
        "mails": [m.to_dict() for m in mails],
        "total": len(mails),
        "filter": filter,
    }


@router.get("/counts")
async def get_counts(db: AsyncSession = Depends(get_db)):
    """Compteurs par catégorie."""
    base = select(func.count(Mail.id)).where(Mail.removed == False)
    total = (await db.execute(base.where(Mail.archived == False))).scalar()
    unread = (await db.execute(base.where(Mail.unread == True, Mail.archived == False))).scalar()
    urgent = (await db.execute(base.where(Mail.is_urgent == True, Mail.archived == False))).scalar()
    starred = (await db.execute(base.where(Mail.starred == True, Mail.archived == False))).scalar()
    archived = (await db.execute(base.where(Mail.archived == True))).scalar()
    return {
        "total": total or 0,
        "unread": unread or 0,
        "urgent": urgent or 0,
        "starred": starred or 0,
        "archived": archived or 0,
    }


@router.post("", status_code=201)
async def create_mail(payload: MailIn, db: AsyncSession = Depends(get_db)):
    m = Mail(
        external_id=payload.external_id,
        from_name=payload.from_name,
        from_email=payload.from_email,
        initials=payload.initials or "".join(p[0] for p in payload.from_name.split()[:2]).upper()[:2],
        avatar_var=payload.avatar_var,
        subject=payload.subject,
        preview=payload.preview or payload.body[:140],
        body=payload.body,
        tag=MailTag(payload.tag) if payload.tag in [t.value for t in MailTag] else MailTag.CONTACT,
        priority=MailPriority(payload.priority) if payload.priority in [p.value for p in MailPriority] else MailPriority.MEDIUM,
        is_urgent=payload.is_urgent,
        is_follow_up=payload.is_follow_up,
        unread=payload.unread,
        starred=payload.starred,
        archived=payload.archived,
        thread_of=payload.thread_of,
        thread=payload.thread,
        ai_suggest=payload.ai_suggest,
    )
    db.add(m)
    await db.flush()
    return m.to_dict()


@router.patch("/{mail_id}")
async def update_mail(mail_id: str, patch: MailPatch, db: AsyncSession = Depends(get_db)):
    """Met à jour partiellement un mail (par external_id ou UUID)."""
    stmt = select(Mail).where((Mail.external_id == mail_id) | (Mail.id == mail_id) if _is_uuid(mail_id) else (Mail.external_id == mail_id))
    result = await db.execute(stmt)
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(404, "Mail introuvable")
    updates = patch.model_dump(exclude_unset=True)
    if "admin_reply_text" in updates:
        m.admin_reply_at = datetime.utcnow()
    for k, v in updates.items():
        setattr(m, k, v)
    await db.flush()
    return m.to_dict()


@router.delete("/{mail_id}", status_code=204)
async def remove_mail(mail_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Mail).where((Mail.external_id == mail_id) | (Mail.id == mail_id) if _is_uuid(mail_id) else (Mail.external_id == mail_id))
    result = await db.execute(stmt)
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(404, "Mail introuvable")
    m.removed = True
    await db.flush()


@router.post("/bulk-import")
async def bulk_import(mails: list[MailIn], db: AsyncSession = Depends(get_db)):
    """Import en masse · pour migration depuis localStorage."""
    count = 0
    for payload in mails:
        # Skip si external_id existe déjà
        if payload.external_id:
            existing = await db.execute(select(Mail).where(Mail.external_id == payload.external_id))
            if existing.scalar_one_or_none():
                continue
        m = Mail(
            external_id=payload.external_id,
            from_name=payload.from_name,
            from_email=payload.from_email,
            initials=payload.initials,
            avatar_var=payload.avatar_var,
            subject=payload.subject,
            preview=payload.preview,
            body=payload.body,
            tag=MailTag(payload.tag) if payload.tag in [t.value for t in MailTag] else MailTag.CONTACT,
            priority=MailPriority(payload.priority) if payload.priority in [p.value for p in MailPriority] else MailPriority.MEDIUM,
            is_urgent=payload.is_urgent,
            is_follow_up=payload.is_follow_up,
            unread=payload.unread,
            starred=payload.starred,
            archived=payload.archived,
            thread_of=payload.thread_of,
            thread=payload.thread,
            ai_suggest=payload.ai_suggest,
        )
        db.add(m)
        count += 1
    await db.flush()
    return {"imported": count, "skipped": len(mails) - count}


def _is_uuid(s: str) -> bool:
    try:
        from uuid import UUID
        UUID(s)
        return True
    except Exception:
        return False
