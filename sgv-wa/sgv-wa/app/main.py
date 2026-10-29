import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401  (registra as tabelas no metadata)
from app.database import Base, engine
from app.routers import pedidos, prdutos, webhook

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas se não existirem. (Mais tarde: trocar por migrações com Alembic.)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="SGV-WA", version="0.1.0", lifespan=lifespan)
app.include_router(webhook.router)
app.include_router(pedidos.router)
app.include_router(produtos.router)


@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok"}
