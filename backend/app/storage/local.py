"""Local filesystem storage — development only.

Do NOT use in production on Render: the container filesystem is
ephemeral and is wiped on redeploy/restart.
"""
import os
from pathlib import Path

from app.storage.interface import StorageInterface


class LocalStorage(StorageInterface):
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, key: str) -> Path:
        # Path traversal protection: resolve and ensure the result stays
        # inside base_dir.
        candidate = (self.base_dir / key).resolve()
        base = self.base_dir.resolve()
        if base not in candidate.parents and candidate != base:
            raise ValueError("Invalid storage key: path traversal detected")
        return candidate

    async def upload(self, key: str, data: bytes, content_type: str = "") -> str:
        path = self._safe_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return key

    async def download(self, key: str) -> bytes:
        path = self._safe_path(key)
        if not path.exists():
            raise FileNotFoundError(key)
        with open(path, "rb") as f:
            return f.read()

    async def delete(self, key: str) -> None:
        path = self._safe_path(key)
        if path.exists():
            os.remove(path)

    async def exists(self, key: str) -> bool:
        return self._safe_path(key).exists()
