from decimal import Decimal

import pytest

from app.models import ItemPedido
from app.schemas.pedido import ItemExtraido
from app.services import catalogo as cat
from tests.conftest import mensagem, rodar

pytestmark = pytest.mark.regressao


def _montar(*itens):
    extraidos = [ItemExtraido(nome=n, quantidade=q, unidade=u) for n, q, u in itens]
    return rodar(lambda s: cat.montar_itens(s, extraidos))


def test_normalizar():
    assert cat.normalizar("  Maçã  Verde ") == "maca verde"


def test_item_do_catalogo_recebe_preco(catalogo):
    (item,) = _montar(("Tomate", 1.5, "kg"))
    assert item.produto_id is not None
    assert item.preco_unitario == Decimal("6.50")
    assert cat.subtotal(item) == Decimal("9.75")


@pytest.mark.parametrize(
    "item",
    [("tomate", 3, "un"), ("macaxeira", 2, "kg"), ("coentro", 1, "maço")],
    ids=["unidade-diferente", "produto-inativo", "fora-do-catalogo"],
)
def test_item_sem_preco_fica_a_confirmar(catalogo, item):
    (montado,) = _montar(item)
    assert montado.produto_id is None
    assert montado.preco_unitario is None
    assert cat.subtotal(montado) is None


def test_total_ignora_itens_sem_preco():
    itens = [
        ItemPedido(quantidade=Decimal("2"), preco_unitario=Decimal("6.50")),
        ItemPedido(quantidade=Decimal("1"), preco_unitario=None),
    ]
    assert cat.total_estimado(itens) == Decimal("13.00")


def test_brl():
    assert cat.brl(Decimal("1234.5")) == "R$ 1.234,50"


def test_resumo_marca_item_sem_preco(catalogo, client, whatsapp_fake, llm_fake):
    llm_fake["responder"](("tomate", 2, "kg"), ("coentro", 1, "maço"))
    client.post("/webhook/whatsapp", json=mensagem("2 kg de tomate e 1 maço de coentro"))
    texto = whatsapp_fake[-1][1]
    assert "2 kg de tomate — R$ 13,00" in texto
    assert "1 maço de coentro — preço a confirmar" in texto
    assert "Valor estimado: R$ 13,00" in texto
