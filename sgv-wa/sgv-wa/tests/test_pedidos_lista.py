from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest

from app.models import Cliente, ItemPedido, Pedido, StatusPedido
from tests.conftest import rodar

pytestmark = pytest.mark.regressao
FUSO = ZoneInfo("America/Fortaleza")


@pytest.fixture
def pedidos():
    """Dois pedidos em 29/10 (um confirmado, um pendente) e um em 28/10."""

    async def _criar(s):
        cliente = Cliente(telefone="5583999990000", nome="Maria")
        s.add(cliente)
        await s.flush()

        def pedido(dia, hora, status, *itens):
            return Pedido(
                cliente_id=cliente.id,
                status=status,
                criado_em=datetime(2026, 10, dia, hora, tzinfo=FUSO),
                itens=[ItemPedido(nome=n, quantidade=Decimal(q), unidade=u, preco_unitario=p) for n, q, u, p in itens],
            )

        s.add_all(
            [
                pedido(
                    29,
                    8,
                    StatusPedido.CONFIRMADO,
                    ("tomate", "2", "kg", Decimal("6.50")),
                    ("coentro", "1", "maço", None),
                ),
                pedido(29, 23, StatusPedido.AGUARDANDO_CONFIRMACAO, ("banana", "1", "caixa", Decimal("32.00"))),
                pedido(28, 10, StatusPedido.CONFIRMADO, ("tomate", "5", "kg", Decimal("6.00"))),
            ]
        )
        await s.commit()

    rodar(_criar)


def test_lista_pedidos_do_dia_no_fuso_local(client, token, pedidos):
    r = client.get("/pedidos", params={"dia": "2026-10-29"}, headers=token)
    assert r.status_code == 200
    corpo = r.json()
    assert [p["id"] for p in corpo] == [2, 1]
    confirmado = corpo[1]
    assert confirmado["status"] == "CONFIRMADO"
    assert confirmado["cliente"] == {"telefone": "5583999990000", "nome": "Maria"}
    assert confirmado["total_estimado"] == 13.0
    assert confirmado["itens"] == [
        {"nome": "tomate", "quantidade": 2.0, "unidade": "kg", "preco_unitario": 6.5, "subtotal": 13.0},
        {"nome": "coentro", "quantidade": 1.0, "unidade": "maço", "preco_unitario": None, "subtotal": None},
    ]


def test_filtra_por_status(client, token, pedidos):
    r = client.get("/pedidos", params={"dia": "2026-10-29", "status": "CONFIRMADO"}, headers=token)
    assert [p["id"] for p in r.json()] == [1]


def test_sem_dia_mantem_ultimos_pedidos(client, token, pedidos):
    r = client.get("/pedidos", headers=token)
    assert [p["id"] for p in r.json()] == [3, 2, 1]


def test_dia_sem_pedidos(client, token, pedidos):
    assert client.get("/pedidos", params={"dia": "2020-01-01"}, headers=token).json() == []


def test_separacao_soma_confirmados(client, token, pedidos):
    r = client.get("/pedidos/separacao", headers=token)
    assert r.json() == [
        {"produto": "coentro", "unidade": "maço", "total": 1.0},
        {"produto": "tomate", "unidade": "kg", "total": 7.0},
    ]
