"""Proxy APIs gouvernementales françaises."""
from fastapi import APIRouter, Query
from ..services import gouv_api

router = APIRouter()


@router.get("/address/search")
async def address_search(q: str = Query(..., min_length=3), limit: int = 5):
    """Auto-complétion d'adresse via la BAN."""
    return await gouv_api.search_address(q, limit)


@router.get("/address/reverse")
async def address_reverse(lon: float, lat: float):
    return await gouv_api.reverse_address(lon, lat)


@router.get("/company/search")
async def company_search(q: str = Query(..., min_length=2), limit: int = 5):
    """Recherche d'entreprise par nom, SIREN ou SIRET."""
    return await gouv_api.search_company(q, limit)


@router.get("/company/{siret}")
async def company_by_siret(siret: str):
    data = await gouv_api.get_company_by_siret(siret)
    if not data:
        return {"error": "Entreprise introuvable"}
    return data


@router.get("/communes")
async def communes(postal_code: str = Query(..., min_length=5, max_length=5)):
    return await gouv_api.search_communes_by_postal(postal_code)


@router.get("/admin/search")
async def admin_search(q: str, limit: int = 10):
    """Annuaire des services publics (CAF, CCAS, France Services...)."""
    return await gouv_api.search_admin(q, limit)


@router.get("/admin/caf")
async def find_caf(postal_code: str):
    return await gouv_api.find_caf_by_postal(postal_code)
