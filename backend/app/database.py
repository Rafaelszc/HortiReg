from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# hide_parameters: erro do banco registrado em log não expõe endereço nem telefone (LGPD, US-11)
engine = create_async_engine(settings.database_url, echo=False, hide_parameters=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependência do FastAPI: uma sessão de banco por requisição."""
    async with SessionLocal() as session:
        yield session
