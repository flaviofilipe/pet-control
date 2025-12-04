"""
Conexão com PostgreSQL usando SQLAlchemy async
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://pet_control_user:pet_control_pass@localhost:5432/pet_control"
)

# Detectar ambiente de teste e tipo de banco
IS_TESTING = os.getenv("ENVIRONMENT", "development").lower() == "testing"
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# Configuração de engine baseada no tipo de banco
if IS_SQLITE:
    # SQLite não suporta pool_size, max_overflow, etc.
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True,
        poolclass=NullPool,
    )
else:
    # PostgreSQL com pool configurável
    engine = create_async_engine(
        DATABASE_URL,
        echo=not IS_TESTING,  # Log SQL queries em desenvolvimento
        future=True,
        pool_size=20 if not IS_TESTING else 5,
        max_overflow=10 if not IS_TESTING else 0,
        pool_timeout=30,
        pool_recycle=3600,
        poolclass=NullPool if IS_TESTING else None,  # Sem pool em testes
    )

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency para obter sessão do banco de dados.
    
    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Inicializar banco de dados (criar tabelas)"""
    from app.database.base import Base
    # Importar todos os models para registrar no metadata
    import app.database.models  # noqa: F401
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Fechar conexões do banco de dados"""
    await engine.dispose()
