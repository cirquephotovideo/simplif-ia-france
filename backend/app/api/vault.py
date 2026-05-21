"""Coffre-fort numérique chiffré AES-256 (sécurité renforcée).

Améliorations :
  - HMAC-SHA256 d'intégrité (anti-tampering)
  - Rate-limit par user (anti-bulk-download)
  - PIN requis pour catégories sensibles (IDENTITE, BANQUE, SANTE, JUSTICE, PM_PRETS)
  - Audit complet : IP + UserAgent
  - Détection burst → alarme automatique
  - Soft-delete avec deleted_at (purge ultérieure possible)
"""
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Header, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from io import BytesIO

from ..database import get_db
from ..models import User, Document, DocumentCategory, AuditLog
from ..models.document import SENSITIVE_CATEGORIES
from ..core.security import get_current_user
from ..services.crypto import encrypt_bytes, decrypt_bytes
from ..services.storage import get_storage
from ..services import vault_security as vsec
from ..services import alerts as alert_svc

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────

def _client_ip(request: Request) -> str | None:
    """Récupère l'IP réelle derrière le reverse proxy."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else None


async def _audit(
    db: AsyncSession,
    *,
    action: str,
    actor: User,
    request: Request,
    target_id: str,
    success: bool = True,
    extra: dict | None = None,
):
    db.add(AuditLog(
        action=action,
        actor_id=actor.id,
        actor_email=actor.email,
        target_type="document",
        target_id=target_id,
        ip_address=_client_ip(request),
        user_agent=(request.headers.get("user-agent") or "")[:500],
        success=success,
        payload=extra or {},
    ))


def _rate_or_429(user_id: str, action: str):
    allowed, retry = vsec.check_rate_limit(user_id, action)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Trop de requêtes ({action}). Réessaie dans {retry}s.",
            headers={"Retry-After": str(retry)},
        )


# ─────────────────────────────────────────────────────────────────────
#  ROUTES
# ─────────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload(
    request: Request,
    file: UploadFile = File(...),
    name: str = Form(...),
    category: DocumentCategory = Form(DocumentCategory.AUTRE),
    expires_at: datetime | None = Form(None),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _rate_or_429(str(current.id), "upload")

    raw = await file.read()
    if len(raw) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Fichier trop gros (max 25 Mo)")

    encrypted = encrypt_bytes(raw)
    integrity = vsec.compute_integrity(raw)

    storage = get_storage()
    rel = storage.save(encrypted)

    doc = Document(
        user_id=current.id,
        name=name,
        category=category,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(raw),
        storage_path=rel,
        integrity_hash=integrity,
        expires_at=expires_at,
    )
    db.add(doc)
    await db.flush()
    await _audit(
        db, action="vault.upload", actor=current, request=request, target_id=str(doc.id),
        extra={"category": category.value, "size": len(raw)},
    )
    return {
        "id": str(doc.id),
        "name": doc.name,
        "size": doc.size_bytes,
        "category": doc.category.value,
        "integrity": integrity[:12] + "…",
    }


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
            "download_count": d.download_count,
            "last_accessed_at": d.last_accessed_at.isoformat() if d.last_accessed_at else None,
            "sensitive": d.category in SENSITIVE_CATEGORIES,
        }
        for d in docs
    ]


@router.get("/categories")
async def list_categories():
    """Toutes les catégories disponibles avec flag 'sensible'."""
    return [
        {
            "value": c.value,
            "label": c.value.replace("_", " ").title(),
            "sensitive": c in SENSITIVE_CATEGORIES,
        }
        for c in DocumentCategory
    ]


@router.get("/{doc_id}/download")
async def download(
    doc_id: UUID,
    request: Request,
    x_vault_pin: str | None = Header(None, description="PIN requis pour catégories sensibles"),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _rate_or_429(str(current.id), "download")

    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == current.id)
    )
    doc = result.scalar_one_or_none()
    if not doc or doc.is_deleted:
        raise HTTPException(status_code=404, detail="Document introuvable")

    # PIN requis si catégorie sensible ET utilisateur a configuré un PIN
    pin_hash = getattr(current, "vault_pin_hash", None)
    pin_salt = getattr(current, "vault_pin_salt", None)
    if doc.category in SENSITIVE_CATEGORIES and pin_hash:
        if not vsec.verify_pin(x_vault_pin or "", pin_hash, pin_salt or ""):
            await _audit(
                db, action="vault.pin_failed", actor=current, request=request,
                target_id=str(doc.id), success=False,
                extra={"category": doc.category.value},
            )
            await alert_svc.alert_vault_pin_failed(
                db, user_id=current.id, category_name=doc.category.value, attempts=1
            )
            raise HTTPException(
                status_code=403,
                detail="PIN incorrect ou manquant pour cette catégorie sensible.",
                headers={"X-Vault-Pin-Required": "true"},
            )

    # Détection burst avant action
    burst = vsec.burst_count(str(current.id))
    if burst >= 9:
        await alert_svc.alert_vault_bulk(
            db, user_id=current.id, count_in_10s=burst + 1, ip=_client_ip(request)
        )

    storage = get_storage()
    encrypted = storage.load(doc.storage_path)
    try:
        decrypted = decrypt_bytes(encrypted)
    except Exception:
        await _audit(
            db, action="vault.decrypt_error", actor=current, request=request,
            target_id=str(doc.id), success=False,
        )
        await alert_svc.alert_vault_tamper(db, current.id, doc.id, doc.name)
        raise HTTPException(status_code=500, detail="Erreur de déchiffrement.")

    # Vérification d'intégrité HMAC (anti-tampering)
    if not vsec.verify_integrity(decrypted, doc.integrity_hash or ""):
        await _audit(
            db, action="vault.integrity_failed", actor=current, request=request,
            target_id=str(doc.id), success=False,
        )
        await alert_svc.alert_vault_tamper(db, current.id, doc.id, doc.name)
        raise HTTPException(
            status_code=500,
            detail="🚨 Intégrité du document compromise. Une alerte a été enregistrée.",
        )

    doc.download_count += 1
    doc.last_accessed_at = datetime.utcnow()
    await _audit(
        db, action="vault.download", actor=current, request=request, target_id=str(doc.id),
        extra={"category": doc.category.value},
    )

    return StreamingResponse(
        BytesIO(decrypted),
        media_type=doc.mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{doc.name}"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store, max-age=0",
        },
    )


@router.delete("/{doc_id}", status_code=204)
async def delete_doc(
    doc_id: UUID,
    request: Request,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _rate_or_429(str(current.id), "delete")

    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.user_id == current.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document introuvable")
    doc.is_deleted = True
    doc.deleted_at = datetime.utcnow()
    storage = get_storage()
    if doc.storage_path:
        storage.delete(doc.storage_path)
    await _audit(
        db, action="vault.delete", actor=current, request=request, target_id=str(doc.id),
        extra={"category": doc.category.value},
    )
    return None
