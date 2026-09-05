import ssl
from typing import AsyncIterator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import get_settings

settings = get_settings()


def get_clean_database_url_and_connect_args():
    """Normalize DATABASE_URL to the asyncpg driver and translate
    sslmode into connect_args it actually understands.

    asyncpg's low-level connect() does not accept a "sslmode" keyword
    argument the way psycopg2 does — SQLAlchemy's asyncpg dialect passes
    unrecognized URL query params straight through as DBAPI kwargs,
    which crashes with "unexpected keyword argument 'sslmode'". This
    strips it from the URL and instead builds the connect_args asyncpg
    expects (a bool or an ssl.SSLContext).

    It also follows real libpq sslmode semantics: "require"/"prefer"/
    "allow" mean "encrypt the connection" only — they explicitly do NOT
    verify the server's certificate against a trusted CA (that's what
    "verify-ca"/"verify-full" are for). Supabase's Postgres uses a
    publicly-trusted certificate, so verify-full works out of the box;
    "require" is kept available for any provider using a private/
    self-signed CA, matching the same fix already applied for MySQL.
    """
    url = make_url(settings.database_url)
    if url.get_backend_name() == "postgresql":
        url = url.set(drivername="postgresql+asyncpg")

    query = dict(url.query)
    ssl_mode = query.pop("sslmode", None) or query.pop("ssl-mode", None)
    url = url.set(query=query)

    connect_args = {}
    if url.drivername == "postgresql+asyncpg" and ssl_mode and ssl_mode.lower() != "disable":
        if ssl_mode.lower() in ("verify-ca", "verify-full"):
            connect_args["ssl"] = ssl.create_default_context()
        else:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            connect_args["ssl"] = ctx

    return url, connect_args


_url, _connect_args = get_clean_database_url_and_connect_args()
engine = create_async_engine(_url, pool_pre_ping=True, future=True, connect_args=_connect_args)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a scoped async session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()