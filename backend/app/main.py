import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app import models  # noqa: F401  (registra as tabelas no metadata)
from app.config import settings
from app.database import Base, engine
from app.routers import auth, pedidos, produtos, telegram, webhook
from app.services import estados, expiracao, telegram_bot

logging.basicConfig(level=logging.INFO)
# Evita spam de getUpdates nos logs e impede exposição do token do bot na URL do Telegram.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas se não existirem. (Mais tarde: trocar por migrações com Alembic.)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # create_all não altera enum já existente; status novo da US-10
        await conn.execute(text("ALTER TYPE statuspedido ADD VALUE IF NOT EXISTS 'EXPIRADO'"))
    tarefa = asyncio.create_task(expiracao.rodar_periodicamente())
    tarefa_telegram: asyncio.Task | None = None
    if settings.telegram_polling and settings.telegram_bot_token and not settings.telegram_webhook_url:
        tarefa_telegram = asyncio.create_task(telegram_bot.rodar_polling())
    yield
    tarefa.cancel()
    if tarefa_telegram is not None:
        tarefa_telegram.cancel()
    estados.limpar_todos()
    await engine.dispose()


app = FastAPI(title="SGV-WA", version="0.1.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(webhook.router)
app.include_router(telegram.router)
app.include_router(pedidos.router)
app.include_router(produtos.router)


@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok"}
