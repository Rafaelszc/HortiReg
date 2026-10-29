import asyncio
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from sqlalchemy import func, select

from app.config import settings
from app.models import Admin
from app.seed import _main as seed_main
from app.services import security
from tests.conftest import LOGIN, SENHA, rodar

pytestmark = pytest.mark.regressao


def test_hash_e_verificacao():
    h = security.hash_senha("abc")
    assert h != "abc"
    assert security.verificar_senha(h, "abc")
    assert not security.verificar_senha(h, "abd")


def test_token_expirado_e_adulterado():
    expirado = security.criar_token("admin", datetime.now(UTC) - timedelta(hours=2))
    assert security.ler_token(expirado) is None
    assert security.ler_token("lixo") is None
    forjado = jwt.encode({"sub": "admin"}, "outro-segredo-com-32-bytes-ou-mais", algorithm="HS256")
    assert security.ler_token(forjado) is None
    assert security.ler_token(security.criar_token("admin")) == "admin"


def test_me_sem_token_ou_invalido_ou_expirado(client, admin):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer xxx"}).status_code == 401
    exp = security.criar_token(LOGIN, datetime.now(UTC) - timedelta(hours=2))
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {exp}"}).status_code == 401


def test_login_zera_contador_apos_sucesso(client, admin):
    for _ in range(2):
        client.post("/auth/login", json={"login": LOGIN, "senha": "x"})
    assert client.post("/auth/login", json={"login": LOGIN, "senha": SENHA}).status_code == 200
    assert rodar(lambda s: s.scalar(select(Admin.tentativas_falhas))) == 0


@pytest.mark.parametrize("rota", ["/pedidos", "/pedidos/separacao"])
def test_pedidos_exigem_admin(client, rota):
    assert client.get(rota).status_code == 401


def test_seed_cria_admin_uma_vez():
    asyncio.run(seed_main())
    asyncio.run(seed_main())
    assert rodar(lambda s: s.scalar(select(func.count()).select_from(Admin))) == 1
    admin = rodar(lambda s: s.scalar(select(Admin)))
    assert admin.login == settings.admin_login
    assert security.verificar_senha(admin.senha_hash, settings.admin_password)


def test_seed_exige_credenciais(monkeypatch):
    monkeypatch.setattr(settings, "admin_password", "")
    with pytest.raises(SystemExit):
        asyncio.run(seed_main())
