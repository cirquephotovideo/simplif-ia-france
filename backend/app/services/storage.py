"""Stockage des documents : disque local ou S3."""
import os
import uuid
from pathlib import Path
from ..config import settings


class LocalStorage:
    def __init__(self, base: str):
        self.base = Path(base)
        self.base.mkdir(parents=True, exist_ok=True)

    def save(self, encrypted: bytes) -> str:
        rel = f"{uuid.uuid4()}.enc"
        path = self.base / rel
        with open(path, "wb") as f:
            f.write(encrypted)
        os.chmod(path, 0o600)
        return rel

    def load(self, rel: str) -> bytes:
        path = self.base / rel
        if not path.exists():
            raise FileNotFoundError(rel)
        return path.read_bytes()

    def delete(self, rel: str) -> None:
        path = self.base / rel
        if path.exists():
            path.unlink()


_storage: LocalStorage | None = None


def get_storage() -> LocalStorage:
    global _storage
    if _storage is None:
        _storage = LocalStorage(settings.STORAGE_PATH)
    return _storage
