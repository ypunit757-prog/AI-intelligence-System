"""StorageInterface: abstraction over where uploaded files physically live.

Render's filesystem is not durable — production MUST use an
S3-compatible implementation. LocalStorage exists for local dev only.
"""
from abc import ABC, abstractmethod


class StorageInterface(ABC):
    @abstractmethod
    async def upload(self, key: str, data: bytes, content_type: str = "") -> str:
        """Store bytes under `key`. Returns the storage key actually used."""

    @abstractmethod
    async def download(self, key: str) -> bytes:
        """Retrieve bytes for `key`. Raises FileNotFoundError if missing."""

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Delete the object at `key`. No-op if it doesn't exist."""

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Return True if an object exists at `key`."""
