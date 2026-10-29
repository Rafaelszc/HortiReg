"""Fixtures: banco de teste real (Postgres) e Gemini/WhatsApp falsos."""

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app import models  # noqa: F401
from app.config import settings
from app.database import Base
from app.main import app
from app.models import Admin, Produto
from app.schemas.pedido import ItemExtraido, PedidoExtraido
from app.services import llm, security, whatsapp

LOGIN = "admin"
SENHA = "senha-de-teste-123"
TELEFONE = "5583999990000"

# Engine própria e sem pool: cada rodar() usa um loop novo, e o app usa o dele no TestClient.
_engine = create_async_engine(settings.database_url, poolclass=NullPool)
_Sessao = async_sessionmaker(_engine, expire_on_commit=False)


def rodar(fn: Callable[[Any], Awaitable[Any]]) -> Any:
    """Executa fn(session) num loop próprio e fecha as conexões ao final."""

    async def _run():
        async with _Sessao() as session:
            return await fn(session)

    return asyncio.run(_run())


async def _recriar_schema(_session) -> None:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.fixture(scope="session", autouse=True)
def schema():
    rodar(_recriar_schema)


@pytest.fixture(autouse=True)
def banco_limpo(schema):
    tabelas = ", ".join(t.name for t in Base.metadata.sorted_tables)

    async def _limpar(session):
        await session.execute(text(f"TRUNCATE {tabelas} RESTART IDENTITY CASCADE"))
        await session.commit()

    rodar(_limpar)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin():
    async def _criar(session):
        session.add(Admin(login=LOGIN, senha_hash=security.hash_senha(SENHA)))
        await session.commit()

    rodar(_criar)


@pytest.fixture
def token(client, admin):
    r = client.post("/auth/login", json={"login": LOGIN, "senha": SENHA})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture
def catalogo():
    async def _criar(session):
        session.add_all(
            [
                Produto(nome="tomate", unidade="kg", preco=Decimal("6.50")),
                Produto(nome="banana", unidade="caixa", preco=Decimal("32.00")),
                Produto(nome="macaxeira", unidade="kg", preco=Decimal("5.00"), ativo=False),
            ]
        )
        await session.commit()

    rodar(_criar)


@pytest.fixture
def whatsapp_fake(monkeypatch):
    """Guarda as mensagens enviadas em vez de chamar a Evolution API."""
    enviadas: list[tuple[str, str]] = []

    async def enviar_texto(numero: str, texto: str) -> None:
        enviadas.append((numero, texto))

    monkeypatch.setattr(whatsapp, "enviar_texto", enviar_texto)
    return enviadas


@pytest.fixture
def llm_fake(monkeypatch):
    """Gemini falso: devolve os itens configurados em `resposta`."""
    estado: dict[str, Any] = {"resposta": PedidoExtraido()}

    async def extrair_pedido(texto=None, audio=None, audio_mime="audio/ogg"):
        estado["texto"] = texto
        return estado["resposta"]

    monkeypatch.setattr(llm, "extrair_pedido", extrair_pedido)

    def responder(*itens: tuple[str, float, str]) -> None:
        estado["resposta"] = PedidoExtraido(itens=[ItemExtraido(nome=n, quantidade=q, unidade=u) for n, q, u in itens])

    estado["responder"] = responder
    return estado


def mensagem(texto: str, telefone: str = TELEFONE) -> dict:
    """Evento messages.upsert da Evolution API com uma mensagem de texto."""
    return {
        "event": "messages.upsert",
        "data": {
            "key": {"remoteJid": f"{telefone}@s.whatsapp.net", "fromMe": False, "id": "ABC"},
            "pushName": "Maria",
            "message": {"conversation": texto},
        },
    }


@pytest.fixture
def relogio(monkeypatch):
    """Relógio controlável para testar bloqueio e expiração."""
    estado = {"agora": datetime.now(UTC)}
    monkeypatch.setattr(security, "agora", lambda: estado["agora"])
    return estado
