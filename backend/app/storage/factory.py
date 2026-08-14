from app.config.settings import get_settings
from app.storage.interface import StorageInterface
from app.storage.local import LocalStorage
from app.storage.s3_storage import S3CompatibleStorage

_instance: StorageInterface | None = None


def get_storage() -> StorageInterface:
    """Runtime-selected storage backend — never hardcoded per environment."""
    global _instance
    if _instance is not None:
        return _instance

    settings = get_settings()
    if settings.storage_provider == "s3":
        _instance = S3CompatibleStorage(
            bucket=settings.storage_bucket,
            endpoint_url=settings.storage_endpoint,
            access_key=settings.storage_access_key,
            secret_key=settings.storage_secret_key,
        )
    else:
        _instance = LocalStorage(base_dir=settings.local_storage_dir)
    return _instance
