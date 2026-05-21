"""API AdminSettings · key-value store pour configs admin (remplace localStorage)."""
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_db
from ..models import AdminSetting

router = APIRouter()


class SettingIn(BaseModel):
    key: str
    value: Any = None


@router.get("/{key}")
async def get_setting(key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdminSetting).where(AdminSetting.key == key))
    s = result.scalar_one_or_none()
    if not s:
        return {"key": key, "value": None}
    return s.to_dict()


@router.put("/{key}")
async def set_setting(key: str, payload: SettingIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdminSetting).where(AdminSetting.key == key))
    s = result.scalar_one_or_none()
    if s:
        s.value = payload.value
    else:
        s = AdminSetting(key=key, value=payload.value)
        db.add(s)
    await db.flush()
    return s.to_dict()


@router.delete("/{key}", status_code=204)
async def delete_setting(key: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdminSetting).where(AdminSetting.key == key))
    s = result.scalar_one_or_none()
    if s:
        await db.delete(s)
        await db.flush()


@router.get("")
async def list_settings(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AdminSetting).order_by(AdminSetting.key))
    return {"settings": [s.to_dict() for s in result.scalars().all()]}
