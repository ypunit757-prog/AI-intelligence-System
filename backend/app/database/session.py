import ssl
from typing import AsyncIterator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config.settings import get_settings

settings = get_settings()


def get_clean_database_url_and_connect_args():
    """Strip provider-specific SSL query params from DATABASE_URL and
    translate them into connect_args asyncmy actually understands.

    asyncmy's low-level connect() does not accept the "ssl-mode" query
    parameter that managed providers like Aiven/PlanetScale append to
    their connection strings (e.g. "...?ssl-mode=REQUIRED"). SQLAlchemy
    passes unrecognized URL query params straight through as DBAPI
    kwargs, which crashes asyncmy with "unexpected keyword argument
    'ssl-mode'". This strips it from the URL and instead builds a real
    SSL context passed via connect_args, the form asyncmy expects.
    """
    url = make_url(settings.database_url)
    query = dict(url.query)
    ssl_mode = query.pop("ssl-mode", None) or query.pop("ssl_mode", None)
    url = url.set(query=query)

    connect_args = {}
    if url.drivername == "mysql+asyncmy" and ssl_mode and ssl_mode.upper() != "DISABLED":
        ctx = ssl.create_default_context()
        # "REQUIRED"/"PREFERRED" mean "encrypt the connection" only — they
        # explicitly do NOT require verifying the server's certificate
        # against a trusted CA (that's what VERIFY_CA/VERIFY_IDENTITY are
        # for). Managed providers like Aiven use a self-signed CA that
        # isn't in the system trust store, so full verification would
        # reject a legitimate connection under ssl-mode=REQUIRED.
        if ssl_mode.upper() in ("REQUIRED", "PREFERRED"):
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