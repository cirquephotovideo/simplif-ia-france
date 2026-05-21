"""Clients pour toutes les APIs gouvernementales + tests de connectivité.

Chaque fonction `call_*` lit les credentials depuis la base (chiffrés Fernet),
les déchiffre à la volée et exécute l'appel HTTP avec l'authentification idoine
(Bearer, X-Api-Key, OAuth2 client_credentials, etc.).

Toutes les erreurs sont remontées comme `httpx.HTTPStatusError` ou `RuntimeError`
pour traitement explicite par les routes appelantes.
"""
import json
import httpx
from typing import Any, Optional, Tuple
from datetime import datetime, timedelta

from ..models import ApiCredential, ApiProvider
from .crypto import decrypt_text


# ============ Cache des tokens OAuth2 (mémoire processus) ============
_oauth_tokens: dict[str, dict[str, Any]] = {}


def _decrypt(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    try:
        return decrypt_text(value)
    except Exception:
        return None


async def _get_oauth_token(provider: ApiProvider, cred: ApiCredential, token_url: str, scope: str = "") -> str:
    """OAuth2 client_credentials grant + cache mémoire avec expiry."""
    cache_key = provider.value
    cached = _oauth_tokens.get(cache_key)
    if cached and cached["expires_at"] > datetime.utcnow():
        return cached["token"]

    client_id = _decrypt(cred.client_id_encrypted)
    client_secret = _decrypt(cred.client_secret_encrypted)
    if not (client_id and client_secret):
        raise RuntimeError(f"OAuth2 impossible : client_id/secret manquants pour {provider.value}")

    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": scope,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        data = r.json()
        token = data["access_token"]
        expires_in = int(data.get("expires_in", 3600))
        _oauth_tokens[cache_key] = {
            "token": token,
            "expires_at": datetime.utcnow() + timedelta(seconds=expires_in - 60),
        }
        return token


# ============ Helpers d'appel par provider ============

async def call_api_particulier(cred: ApiCredential, path: str, params: dict | None = None) -> dict:
    """API Particulier · header X-Api-Key."""
    api_key = _decrypt(cred.api_key_encrypted)
    base = cred.base_url or "https://particulier.api.gouv.fr/api"
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{base}{path}", params=params or {}, headers={"X-Api-Key": api_key})
        r.raise_for_status()
        return r.json()


async def call_api_entreprise(cred: ApiCredential, path: str, params: dict | None = None) -> dict:
    """API Entreprise · Bearer token."""
    api_key = _decrypt(cred.api_key_encrypted)
    base = cred.base_url or "https://entreprise.api.gouv.fr/v3"
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(
            f"{base}{path}",
            params=params or {},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        r.raise_for_status()
        return r.json()


async def call_france_travail(cred: ApiCredential, path: str, params: dict | None = None) -> dict:
    """France Travail · OAuth2 client_credentials."""
    token = await _get_oauth_token(
        ApiProvider.API_FRANCE_TRAVAIL,
        cred,
        token_url="https://entreprise.francetravail.fr/connexion/oauth2/access_token?realm=%2Fpartenaire",
        scope=" ".join(cred.scopes or ["api_offresdemploiv2", "o2dsoffre"]),
    )
    base = cred.base_url or "https://api.francetravail.io/partenaire"
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{base}{path}", params=params or {}, headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        return r.json()


async def call_legifrance(cred: ApiCredential, path: str, body: dict | None = None) -> dict:
    """Légifrance via PISTE · OAuth2 client_credentials."""
    token = await _get_oauth_token(
        ApiProvider.LEGIFRANCE,
        cred,
        token_url="https://oauth.piste.gouv.fr/api/oauth/token",
        scope="openid",
    )
    base = cred.base_url or "https://api.piste.gouv.fr/dila/legifrance/lf-engine-app"
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(f"{base}{path}", json=body or {}, headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        return r.json()


async def call_judilibre(cred: ApiCredential, path: str, params: dict | None = None) -> dict:
    """Judilibre via PISTE · OAuth2 client_credentials."""
    token = await _get_oauth_token(
        ApiProvider.JUDILIBRE,
        cred,
        token_url="https://oauth.piste.gouv.fr/api/oauth/token",
        scope="openid",
    )
    base = cred.base_url or "https://api.piste.gouv.fr/cassation/judilibre/v1.0"
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{base}{path}", params=params or {}, headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        return r.json()


async def call_insee_sirene(cred: ApiCredential, siret: str) -> dict:
    """INSEE Sirene v3 · OAuth2."""
    token = await _get_oauth_token(
        ApiProvider.INSEE,
        cred,
        token_url="https://api.insee.fr/token",
    )
    base = cred.base_url or "https://api.insee.fr/entreprises/sirene/V3"
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{base}/siret/{siret}", headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        return r.json()


async def call_mes_aides(cred: ApiCredential, profile: dict) -> dict:
    """API Mes Aides · simulation aides sociales."""
    api_key = _decrypt(cred.api_key_encrypted)
    base = cred.base_url or "https://mes-aides.gouv.fr/api"
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{base}/simulate",
            json=profile,
            headers={"X-Api-Key": api_key} if api_key else {},
        )
        r.raise_for_status()
        return r.json()


async def call_ar24(cred: ApiCredential, path: str, body: dict | None = None) -> dict:
    """AR24 LRE · token header."""
    api_key = _decrypt(cred.api_key_encrypted)
    base = cred.base_url or "https://app.ar24.fr/api"
    async with httpx.AsyncClient(timeout=30.0) as client:
        method = "POST" if body else "GET"
        r = await client.request(
            method,
            f"{base}{path}",
            json=body,
            headers={"X-Auth-Token": api_key} if api_key else {},
        )
        r.raise_for_status()
        return r.json()


async def call_yousign(cred: ApiCredential, path: str, body: dict | None = None) -> dict:
    """Yousign API v3."""
    api_key = _decrypt(cred.api_key_encrypted)
    base = cred.base_url or "https://api.yousign.app/v3"
    async with httpx.AsyncClient(timeout=30.0) as client:
        method = "POST" if body else "GET"
        r = await client.request(
            method,
            f"{base}{path}",
            json=body,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
        )
        r.raise_for_status()
        return r.json()


async def call_enedis(cred: ApiCredential, path: str, params: dict | None = None) -> dict:
    """Enedis Data Connect · OAuth2."""
    token = await _get_oauth_token(
        ApiProvider.API_ENEDIS,
        cred,
        token_url="https://gw.ext.prod.api.enedis.fr/oauth2/v3/token",
    )
    base = cred.base_url or "https://gw.ext.prod.api.enedis.fr"
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(f"{base}{path}", params=params or {}, headers={"Authorization": f"Bearer {token}"})
        r.raise_for_status()
        return r.json()


async def call_dpe_ademe(cred: ApiCredential, params: dict | None = None) -> dict:
    """API DPE ADEME · clé optionnelle (open data)."""
    api_key = _decrypt(cred.api_key_encrypted)
    base = cred.base_url or "https://data.ademe.fr/data-fair/api/v1/datasets/dpe-v2-logements-existants"
    headers = {"X-Api-Key": api_key} if api_key else {}
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(f"{base}/lines", params=params or {}, headers=headers)
        r.raise_for_status()
        return r.json()


# ============ Test de connectivité ============

async def test_provider(provider: ApiProvider, cred: ApiCredential) -> Tuple[bool, str]:
    """Tente un appel ping minimal pour vérifier que la clé est valide.

    Retourne (ok, message). Capturé par la route /test qui persiste le résultat.
    """
    try:
        if provider == ApiProvider.API_PARTICULIER:
            # Ping sur un endpoint qui exige juste un header valide
            await call_api_particulier(cred, "/v2/statut-etudiant", params={"ine": "0000000000A"})
            return True, "Clé API Particulier valide"

        if provider == ApiProvider.API_ENTREPRISE:
            await call_api_entreprise(cred, "/insee/sirene/etablissements/12000101100010")
            return True, "Clé API Entreprise valide"

        if provider == ApiProvider.API_FRANCE_TRAVAIL:
            data = await call_france_travail(cred, "/offresdemploi/v2/offres/search", params={"range": "0-0"})
            return True, "OAuth France Travail OK"

        if provider == ApiProvider.LEGIFRANCE:
            # Récupère juste un token (ping OAuth)
            await _get_oauth_token(
                ApiProvider.LEGIFRANCE,
                cred,
                token_url="https://oauth.piste.gouv.fr/api/oauth/token",
                scope="openid",
            )
            return True, "OAuth Légifrance/PISTE OK"

        if provider == ApiProvider.JUDILIBRE:
            await _get_oauth_token(
                ApiProvider.JUDILIBRE,
                cred,
                token_url="https://oauth.piste.gouv.fr/api/oauth/token",
                scope="openid",
            )
            return True, "OAuth Judilibre/PISTE OK"

        if provider == ApiProvider.INSEE:
            await _get_oauth_token(ApiProvider.INSEE, cred, token_url="https://api.insee.fr/token")
            return True, "OAuth INSEE OK"

        if provider == ApiProvider.API_MES_AIDES:
            api_key = _decrypt(cred.api_key_encrypted)
            if not api_key:
                return False, "Aucune clé"
            return True, "Clé Mes Aides présente (test live nécessite profil utilisateur)"

        if provider == ApiProvider.AR24:
            data = await call_ar24(cred, "/user/me")
            return True, f"AR24 OK · utilisateur: {data.get('email', '?')}"

        if provider == ApiProvider.YOUSIGN:
            data = await call_yousign(cred, "/users")
            return True, "Yousign OK"

        if provider == ApiProvider.GEMINI:
            api_key = _decrypt(cred.api_key_encrypted)
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}")
                r.raise_for_status()
            return True, "Clé Gemini valide"

        if provider == ApiProvider.OPENAI:
            api_key = _decrypt(cred.api_key_encrypted)
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    "https://api.openai.com/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                r.raise_for_status()
            return True, "Clé OpenAI valide"

        if provider == ApiProvider.ANTHROPIC:
            api_key = _decrypt(cred.api_key_encrypted)
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    json={"model": "claude-haiku-4-5-20251001", "max_tokens": 1, "messages": [{"role": "user", "content": "ping"}]},
                    headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
                )
                # 200 ou 400 (bad request mais auth OK) = clé valide
                if r.status_code in (200, 400):
                    return True, "Clé Anthropic valide"
                r.raise_for_status()
            return True, "Clé Anthropic valide"

        if provider == ApiProvider.MISTRAL:
            api_key = _decrypt(cred.api_key_encrypted)
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    "https://api.mistral.ai/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                r.raise_for_status()
            return True, "Clé Mistral valide"

        if provider == ApiProvider.ELEVENLABS:
            api_key = _decrypt(cred.api_key_encrypted)
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    "https://api.elevenlabs.io/v1/user",
                    headers={"xi-api-key": api_key},
                )
                r.raise_for_status()
            return True, "Clé ElevenLabs valide"

        if provider == ApiProvider.STRIPE:
            api_key = _decrypt(cred.api_key_encrypted)
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    "https://api.stripe.com/v1/balance",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                r.raise_for_status()
            return True, "Clé Stripe valide"

        if provider == ApiProvider.HCAPTCHA:
            return True, "hCaptcha configuré (validation à la 1ère requête)"

        if provider == ApiProvider.SENTRY:
            api_key = _decrypt(cred.api_key_encrypted)
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(
                    "https://sentry.io/api/0/projects/",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                r.raise_for_status()
            return True, "Token Sentry valide"

        # Fallback : pas de ping spécifique, on valide juste la présence
        if cred.api_key_encrypted or cred.client_secret_encrypted:
            return True, f"Credentials enregistrés pour {provider.value} (test live non implémenté)"
        return False, "Aucune clé"

    except httpx.HTTPStatusError as e:
        return False, f"HTTP {e.response.status_code} · {e.response.text[:200]}"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:200]}"
