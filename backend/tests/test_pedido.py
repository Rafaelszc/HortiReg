import re

from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import func, select

from app.models import ItemPedido, Pedido, StatusPedido
from tests.conftest import TELEFONE, mensagem, rodar

scenarios("features/pedido.feature")


@given("um catálogo ativo com tomate e banana", target_fixture="ctx")
def _catalogo(catalogo, client, whatsapp_fake, llm_fake):
    return {"client": client, "enviadas": whatsapp_fake, "llm": llm_fake}


def _itens(texto: str) -> list[tuple[str, float, str]]:
    itens = []
    for trecho in re.findall(r'"([^"]+)"', texto):
        qtd, unidade, nome = re.fullmatch(r"(\S+) (\S+) de (.+)", trecho).groups()
        itens.append((nome, float(qtd), unidade))
    return itens


@given(parsers.re(r"que a IA extrai (?P<texto>.+)"))
def _ia_extrai(ctx, texto):
    ctx["llm"]["responder"](*_itens(texto))


@given("que a IA não extrai nenhum item")
def _ia_vazia(ctx):
    ctx["llm"]["responder"]()


@given(parsers.parse('o cliente envia "{texto}"'))
@when(parsers.parse('o cliente envia "{texto}"'))
def _envia(ctx, texto):
    r = ctx["client"].post("/webhook/whatsapp", json=mensagem(texto))
    assert r.status_code == 200


@when(parsers.parse('o cliente envia "{texto}" e a Evolution reenvia o mesmo evento'))
def _envia_duas_vezes(ctx, texto):
    evento = mensagem(texto)
    for _ in range(2):
        assert ctx["client"].post("/webhook/whatsapp", json=evento).status_code == 200


def _pedidos():
    return rodar(lambda s: s.scalars(select(Pedido).order_by(Pedido.id)))


@then(parsers.parse("um pedido é criado aguardando confirmação com {n:d} itens"))
def _criado(ctx, n):
    (pedido,) = list(_pedidos())
    assert pedido.status == StatusPedido.AGUARDANDO_CONFIRMACAO
    assert len(pedido.itens) == n


@then(parsers.parse('o cliente recebe o resumo com valor estimado de "{valor}"'))
def _resumo(ctx, valor):
    numero, texto = ctx["enviadas"][-1]
    assert numero == TELEFONE
    assert f"Valor estimado: {valor}" in texto
    assert "Responda *SIM*" in texto


@then("nenhum pedido é criado")
def _nenhum(ctx):
    assert rodar(lambda s: s.scalar(select(func.count()).select_from(Pedido))) == 0


@then("o cliente recebe orientação de como pedir com um exemplo")
def _orienta(ctx):
    assert 'Exemplo: "quero 2 kg de tomate' in ctx["enviadas"][-1][1]


@then(parsers.parse("o item usa o preço do catálogo de {preco}"))
def _preco(ctx, preco):
    item = rodar(lambda s: s.scalar(select(ItemPedido)))
    assert float(item.preco_unitario) == float(preco)


@then("o pedido fica confirmado")
def _confirmado(ctx):
    (pedido,) = list(_pedidos())
    assert pedido.status == StatusPedido.CONFIRMADO
    assert "confirmado" in ctx["enviadas"][-1][1]


@then("apenas um pedido é criado")
def _um_pedido(ctx):
    assert len(list(_pedidos())) == 1


@then("o cliente recebe apenas um resumo")
def _um_resumo(ctx):
    assert len(ctx["enviadas"]) == 1
