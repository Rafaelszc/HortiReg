import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app import models  # noqa: F401  (registra as tabelas no metadata)
from app.config import settings
from app.database import Base, engine
from app.routers import auth, pedidos, produtos, webhook
from app.services import expiracao, fila

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cria as tabelas se não existirem. (Mais tarde: trocar por migrações com Alembic.)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # create_all não altera enum já existente; status novo da US-10
        await conn.execute(text("ALTER TYPE statuspedido ADD VALUE IF NOT EXISTS 'EXPIRADO'"))
    tarefas = [
        asyncio.create_task(expiracao.rodar_periodicamente()),
        asyncio.create_task(fila.rodar_periodicamente(webhook.processar_mensagem)),
    ]
    yield
    for tarefa in tarefas:
        tarefa.cancel()
    await engine.dispose()


app = FastAPI(title="SGV-WA", version="0.1.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(webhook.router)
app.include_router(pedidos.router)
app.include_router(produtos.router)


@app.get("/health", tags=["infra"])
async def health():
    # versao: tag da imagem em homologação (APP_VERSAO); o deploy confere qual versão está no ar (SCRUM-51)
    return {"status": "ok", "versao": settings.app_versao}
