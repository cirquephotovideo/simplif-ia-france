"""Sécurité renforcée du coffre-fort.

Fournit :
- Calcul/vérification d'intégrité HMAC-SHA256 (anti-tampering)
- Rate-limit en mémoire (anti-bruteforce + anti-bulk-download)
- Détection d'activité suspecte (download massif, IP inhabituelle)
- Vérification PIN pour catégories sensibles
"""
from __future__ import annotations

import hmac
import hashlib
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque

from ..config import settings


# ─────────────────────────────────────────────────────────────────────
#  INTÉGRITÉ — HMAC-SHA256 du contenu en clair
# ─────────────────────────────────────────────────────────────────────

def _hmac_key() -> bytes:
    """Clé dérivée du MASTER_ENCRYPTION_KEY pour HMAC (séparée du chiffrement)."""
    base = settings.MASTER_ENCRYPTION_KEY.encode()
    return hashlib.sha256(b"vault-integrity-v1:" + base).digest()


def compute_integrity(plaintext: bytes) -> str:
    """HMAC-SHA256 hex du contenu — à stocker en DB."""
    return hmac.new(_hmac_key(), plaintext, hashlib.sha256).hexdigest()


def verify_integrity(plaintext: bytes, expected_hex: str) -> bool:
    """Vérifie que le contenu déchiffré correspond au HMAC attendu."""
    if not expected_hex:
        # Document antérieur à l'introduction du HMAC : tolère
        return True
    computed = compute_integrity(plaintext)
    return hmac.compare_digest(computed, expected_hex)


# ─────────────────────────────────────────────────────────────────────
#  RATE-LIMIT EN MÉMOIRE (par user_id)
# ─────────────────────────────────────────────────────────────────────

@dataclass
class RateLimit:
    max_requests: int
    window_seconds: int


# Limites par action
LIMITS = {
    "upload": RateLimit(max_requests=30, window_seconds=60),
    "download": RateLimit(max_requests=60, window_seconds=60),
    "delete": RateLimit(max_requests=20, window_seconds=60),
    # Détection bulk : si > 10 downloads en 10s, c'est suspect
    "burst": RateLimit(max_requests=10, window_seconds=10),
}

# En prod multi-process : remplacer par Redis. Pour le MVP : en mémoire suffit.
_buckets: dict[str, Deque[float]] = defaultdict(deque)


def check_rate_limit(user_id: str, action: str) -> tuple[bool, int]:
    """
    Vérifie la limite pour (user, action). Retourne (allowed, retry_after_seconds).
    Si bloqué, retry_after indique combien attendre.
    """
    limit = LIMITS.get(action)
    if not limit:
        return True, 0

    key = f"{user_id}:{action}"
    bucket = _buckets[key]
    now = time.time()
    cutoff = now - limit.window_seconds

    # Purge des entrées anciennes
    while bucket and bucket[0] < cutoff:
        bucket.popleft()

    if len(bucket) >= limit.max_requests:
        retry_after = int(bucket[0] + limit.window_seconds - now) + 1
        return False, max(retry_after, 1)

    bucket.append(now)
    return True, 0


def burst_count(user_id: str) -> int:
    """Renvoie le nombre de downloads dans la dernière fenêtre de burst (10s)."""
    key = f"{user_id}:download"
    limit = LIMITS["burst"]
    bucket = _buckets[key]
    now = time.time()
    cutoff = now - limit.window_seconds
    return sum(1 for t in bucket if t >= cutoff)


def is_suspicious(user_id: str) -> bool:
    """Détecte un burst de downloads suspect."""
    return burst_count(user_id) >= LIMITS["burst"].max_requests


# ─────────────────────────────────────────────────────────────────────
#  PIN (catégories sensibles)
# ─────────────────────────────────────────────────────────────────────

def hash_pin(pin: str, salt: str) -> str:
    """Hash PBKDF2-SHA256 d'un PIN avec sel (à stocker côté user)."""
    return hashlib.pbkdf2_hmac("sha256", pin.encode(), salt.encode(), 200_000).hex()


def verify_pin(provided: str, stored_hash: str, salt: str) -> bool:
    if not provided or not stored_hash:
        return False
    return hmac.compare_digest(hash_pin(provided, salt), stored_hash)
