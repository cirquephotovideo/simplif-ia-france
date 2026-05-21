"""Catalogue CERFA."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from ..database import get_db
from ..models import Cerfa

router = APIRouter()


@router.get("")
async def list_cerfas(
    q: str | None = None,
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Cerfa).where(Cerfa.is_active == True)
    if q:
        like = f"%{q}%"
        query = query.where(or_(Cerfa.number.ilike(like), Cerfa.name.ilike(like), Cerfa.organism.ilike(like)))
    if category:
        query = query.where(Cerfa.category == category)
    result = await db.execute(query.order_by(Cerfa.category, Cerfa.number))
    return [
        {
            "number": c.number, "name": c.name, "organism": c.organism,
            "category": c.category, "is_prefilled_supported": c.is_prefilled_supported,
            "service_public_url": c.service_public_url, "usage_count": c.usage_count,
        }
        for c in result.scalars().all()
    ]


@router.get("/{number}")
async def get_cerfa(number: str, db: AsyncSession = Depends(get_db)):
    r = await db.execute(select(Cerfa).where(Cerfa.number == number))
    c = r.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="CERFA introuvable")
    return {
        "number": c.number, "name": c.name, "organism": c.organism,
        "category": c.category, "description": c.description,
        "field_schema": c.field_schema, "is_prefilled_supported": c.is_prefilled_supported,
        "service_public_url": c.service_public_url, "pdf_url": c.pdf_url,
    }
