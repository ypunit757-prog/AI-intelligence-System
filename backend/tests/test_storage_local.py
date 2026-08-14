import pytest

from app.storage.local import LocalStorage


@pytest.mark.asyncio
async def test_local_storage_roundtrip(tmp_path):
    storage = LocalStorage(base_dir=str(tmp_path))
    await storage.upload("user1/file.txt", b"hello world")
    assert await storage.exists("user1/file.txt")
    data = await storage.download("user1/file.txt")
    assert data == b"hello world"
    await storage.delete("user1/file.txt")
    assert not await storage.exists("user1/file.txt")


@pytest.mark.asyncio
async def test_local_storage_path_traversal_blocked(tmp_path):
    storage = LocalStorage(base_dir=str(tmp_path))
    with pytest.raises(ValueError):
        await storage.upload("../../etc/passwd", b"malicious")
