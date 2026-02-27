# Database configuration and connection for Supabase PostgreSQL
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Ensure we're using asyncpg driver
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Create async engine with SSL for Supabase
engine = create_async_engine(
    DATABASE_URL,
    echo=os.environ.get("NODE_ENV") == "development",
    poolclass=NullPool,  # Use NullPool for serverless/pooler connections
    connect_args={
        "ssl": "require",
        "server_settings": {"application_name": "mera_mentor"}
    }
)

async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
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
