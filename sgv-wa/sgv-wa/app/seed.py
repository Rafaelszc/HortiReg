"""Bootstrap idempotente: cria as tabelas e o admin do painel a partir do .env."""

import asyncio
import sys

from sqlalchemy import select

from app import models  # noqa: F401  (registra as tabelas no metadata)
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import Admin
from app.services.security import hash_senha


async def seed() -> None:
    if not settings.admin_login or not settings.admin_password:
        raise SystemExit("ADMIN_LOGIN e ADMIN_PASSWORD são obrigatórios no .env")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as session:
        if not await session.scalar(select(Admin).where(Admin.login == settings.admin_login)):
            session.add(Admin(login=settings.admin_login, senha_hash=hash_senha(settings.admin_password)))
            await session.commit()


async def _main() -> None:
    try:
        await seed()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(_main())
    sys.exit(0)
