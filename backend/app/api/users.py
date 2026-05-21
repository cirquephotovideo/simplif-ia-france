"""Endpoints utilisateurs."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from ..database import get_db
from ..models import User
from ..schemas.user import UserOut, UserUpdate
from ..core.security import get_current_user, require_admin

router = APIRouter()


@router.get("", response_model=list[UserOut])
async def list_users(
    skip: int = 0, limit: int = 50,
    _admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).offset(skip).limit(limit).order_by(User.created_at.desc()))
    return list(result.scalars().all())


# ⚠️ /me DOIT être déclaré AVANT /{user_id} sinon FastAPI route /me comme un UUID
@router.get("/me", response_model=UserOut)
async def get_me(current: User = Depends(get_current_user)):
    """Retourne le profil de l'utilisateur connecté."""
    return current


@router.get("/{user_id}", response_model=UserOut)
async def get_user(
    user_id: UUID,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current.role.value not in ("admin", "superadmin", "support") and current.id != user_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return user


@router.patch("/me", response_model=UserOut)
async def update_me(
    data: UserUpdate,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if data.first_name is not None:
        current.first_name = data.first_name
    if data.last_name is not None:
        current.last_name = data.last_name
    if data.profile is not None:
        # Le profil est stocké tel quel mais devrait idéalement être chiffré champ par champ
        current.profile = {**(current.profile or {}), **data.profile}
    return current


@router.delete("/me", status_code=204)
async def delete_me(current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """RGPD article 17 : droit à l'effacement."""
    current.is_active = False
    current.email = f"deleted-{current.id}@purged.local"
    return None
