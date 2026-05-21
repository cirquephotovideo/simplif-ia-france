"""Client pour les APIs publiques du gouvernement français."""
import httpx
from typing import Optional
from ..config import settings


_client: httpx.AsyncClient | None = None


async def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=15.0, follow_redirects=True)
    return _client


# ===== API Adresse · BAN =====
async def search_address(query: str, limit: int = 5) -> dict:
    """https://api-adresse.data.gouv.fr/search/?q=..."""
    client = await get_client()
    r = await client.get(f"{settings.API_BAN_URL}/search/", params={"q": query, "limit": limit})
    r.raise_for_status()
    return r.json()


async def reverse_address(lon: float, lat: float) -> dict:
    client = await get_client()
    r = await client.get(f"{settings.API_BAN_URL}/reverse/", params={"lon": lon, "lat": lat})
    r.raise_for_status()
    return r.json()


# ===== API Recherche d'entreprises (INSEE Sirene) =====
async def search_company(query: str, limit: int = 5) -> dict:
    """https://recherche-entreprises.api.gouv.fr/search?q=..."""
    client = await get_client()
    r = await client.get(f"{settings.API_SIRENE_URL}/search", params={"q": query, "per_page": limit})
    r.raise_for_status()
    return r.json()


async def get_company_by_siret(siret: str) -> Optional[dict]:
    client = await get_client()
    r = await client.get(f"{settings.API_SIRENE_URL}/search", params={"q": siret})
    r.raise_for_status()
    data = r.json()
    results = data.get("results", [])
    return results[0] if results else None


# ===== API Découpage Administratif (Géo) =====
async def search_communes_by_postal(postal_code: str) -> list[dict]:
    """https://geo.api.gouv.fr/communes?codePostal=..."""
    client = await get_client()
    r = await client.get(f"{settings.API_GEO_URL}/communes", params={"codePostal": postal_code})
    r.raise_for_status()
    return r.json()


async def get_commune_by_insee(code: str) -> Optional[dict]:
    client = await get_client()
    r = await client.get(f"{settings.API_GEO_URL}/communes/{code}")
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


# ===== API Annuaire de l'administration =====
async def search_admin(query: str, limit: int = 10) -> dict:
    """Annuaire des services publics (CAF, CCAS, France Services...)."""
    client = await get_client()
    url = f"{settings.API_ANNUAIRE_URL}/api/explore/v2.1/catalog/datasets/api-lannuaire-administration/records"
    r = await client.get(url, params={"where": f'search("{query}")', "limit": limit})
    r.raise_for_status()
    return r.json()


async def find_caf_by_postal(postal_code: str) -> dict:
    """Trouver la CAF compétente pour un code postal."""
    return await search_admin(f"CAF {postal_code}", limit=5)


async def close_client() -> None:
    global _client
    if _client:
        await _client.aclose()
        _client = None
