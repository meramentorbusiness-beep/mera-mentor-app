# Database configuration and connection for Supabase PostgreSQL
import os
import sys
from urllib.parse import urlsplit, urlunsplit
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

RAW_DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

# Fail fast with a clear message if the env var is missing on the deployed service.
if not RAW_DATABASE_URL:
    print(
        "❌ DATABASE_URL is not set. "
        "Add the Supabase pooler connection string in Render → Environment.",
        file=sys.stderr,
    )
    raise RuntimeError("DATABASE_URL environment variable is required")

# SQLAlchemy's create_async_engine requires the driver in the URL scheme
# (postgresql+asyncpg://). Supabase hands you plain postgresql:// so we normalize.
if RAW_DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = RAW_DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif RAW_DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in RAW_DATABASE_URL:
    DATABASE_URL = RAW_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    DATABASE_URL = RAW_DATABASE_URL

# asyncpg does not accept the libpq-style `?sslmode=...` query parameter.
# Strip it — SSL is enforced via connect_args["ssl"] below.
parts = urlsplit(DATABASE_URL)
if parts.query:
    kept = "&".join(
        kv for kv in parts.query.split("&")
        if kv and not kv.lower().startswith("sslmode=")
    )
    DATABASE_URL = urlunsplit((parts.scheme, parts.netloc, parts.path, kept, parts.fragment))

# Log connection target without leaking credentials.
_safe_host = urlsplit(DATABASE_URL).hostname or "<unknown>"
_safe_port = urlsplit(DATABASE_URL).port or "<default>"
print(f"🔌 Connecting to Postgres at {_safe_host}:{_safe_port}")

# Create async engine. NullPool + statement_cache_size=0 keeps us compatible with
# Supabase's PgBouncer pooler (Session on 5432, Transaction on 6543).
engine = create_async_engine(
    DATABASE_URL,
    echo=os.environ.get("NODE_ENV") == "development",
    poolclass=NullPool,
    connect_args={
        "ssl": "require",
        "statement_cache_size": 0,
        "server_settings": {"application_name": "mera_mentor"},
    },
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    """Dependency for getting database session"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database - create all tables"""
    from models.models import Base as ModelBase
    async with engine.begin() as conn:
        await conn.run_sync(ModelBase.metadata.create_all)
    print("✅ Database tables created")


async def close_db():
    """Close database connection"""
    await engine.dispose()


async def test_connection():
    """Test database connection"""
    from sqlalchemy import text
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        return result.scalar() == 1
