"""Service de chiffrement AES-256 (Fernet) pour les documents et profils."""
from cryptography.fernet import Fernet, InvalidToken
from ..config import settings


_fernet: Fernet | None = None


def get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(settings.MASTER_ENCRYPTION_KEY.encode())
    return _fernet


def encrypt_bytes(data: bytes) -> bytes:
    return get_fernet().encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    try:
        return get_fernet().decrypt(token)
    except InvalidToken:
        raise ValueError("Document corrompu ou clé invalide")


def encrypt_text(text: str) -> str:
    return get_fernet().encrypt(text.encode("utf-8")).decode("ascii")


def decrypt_text(token: str) -> str:
    return get_fernet().decrypt(token.encode("ascii")).decode("utf-8")
