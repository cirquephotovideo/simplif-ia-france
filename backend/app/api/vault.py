"""Coffre-fort numérique chiffré AES-256."""
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from io import BytesIO

from ..database import get_db
from ..models import User, Document, DocumentCategory, AuditLog
from ..core.security import get_current_user
from ..services.crypto import encrypt_bytes, decrypt_bytes
from ..services.storage import get_storage

router = APIRouter()


@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    name: str = Form(...),
    category: DocumentCategory = Form(DocumentCategory.AUTRE),
    expires_at: datetime | None = Form(None),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    raw = await file.read()
    if len(raw) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Fichier trop gros (max 25 Mo)")
    encrypted = encrypt_bytes(raw)
    storage = get_storage()
    rel = storage.save(encrypted)

    doc = Document(
        user_id=current.id,
        name=name,
        category=category,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(raw),
        storage_path=rel,
        expires_at=expires_at,
    )
    db.add(doc)
    await db.flush()
    db.add(AuditLog(action="vault.upload", actor_id=current.id, target_type="document", target_id=str(doc.id)))
    return {"id": str(doc.id), "name": doc.name, "size": doc.size_bytes, "category": doc.category.value}


@router.get("")
async def list_docs(
    category: DocumentCategory | None = None,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    q = select(Document).where(and_(Document.user_id == current.id, Document.is_deleted == False))
    if category:
        q = q.where(Document.category == category)
    result = await db.execute(q.order_by(Document.created_at.desc()))
    docs = result.scalars().all()
    return [
        {
            "id": str(d.id), "name": d.name, "category": d.category.value,
            "mime_type": d.mime_type, "size": d.size_bytes,
            "expires_at": d.expires_at.isoformat() if d.expires_at else None,
            "created_at": d.created_at.isoformat(),
        }
        for d in docs
    ]


@router.get("/{doc_id}/download")
async def download(
    doc_id: UUID,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == doc_id, Document.user_id == current.id))
    doc = result.scalar_one_or_none()
    if not doc or doc.is_deleted:
        raise HTTPException(status_code=404, detail="Document introuvable")
    storage = get_storage()
    encrypted = storage.load(doc.storage_path)
    decrypted = decrypt_bytes(encrypted)
    db.add(AuditLog(action="vault.download", actor_id=current.id, target_type="document", target_id=str(doc.id)))
    return StreamingResponse(
        BytesIO(decrypted),
        media_type=doc.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{doc.name}"'},
    )


@router.delete("/{doc_id}", status_code=204)
async def delete_doc(
    doc_id: UUID,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Document).where(Document.id == doc_id, Document.user_id == current.id))
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    doc.is_deleted = True
    storage = get_storage()
    if doc.storage_path:
        storage.delete(doc.storage_path)
    db.add(AuditLog(action="vault.delete", actor_id=current.id, target_type="document", target_id=str(doc.id)))
    return None
