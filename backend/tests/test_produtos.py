from decimal import Decimal

from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import select

from app.models import ItemPedido, Produto
from tests.conftest import mensagem, rodar

scenarios("features/produtos.feature")


@given("que o administrador está autenticado", target_fixture="ctx")
def _autenticado(token, client, whatsapp_fake, llm_fake):
    return {"client": client, "h": token, "llm": llm_fake}


def _cadastrar(ctx, nome, unidade, preco):
    ctx["resp"] = ctx["client"].post(
        "/produtos", headers=ctx["h"], json={"nome": nome, "unidade": unidade, "preco": preco}
    )


@given(parsers.parse('o produto "{nome}" em "{unidade}" por {preco} está cadastrado'))
def _cadastrado(ctx, nome, unidade, preco):
    _cadastrar(ctx, nome, unidade, preco)
    assert ctx["resp"].status_code == 201
    ctx["id"] = ctx["resp"].json()["id"]


@given(parsers.parse("existe um pedido de {qtd:d} kg de tomate"))
def _pedido_existente(ctx, qtd):
    ctx["llm"]["responder"](("tomate", qtd, "kg"))
    r = ctx["client"].post("/webhook/whatsapp", json=mensagem(f"quero {qtd} kg de tomate"))
    assert r.status_code == 200


@when(parsers.parse('cadastra o produto "{nome}" em "{unidade}" por {preco}'))
def _quando_cadastra(ctx, nome, unidade, preco):
    _cadastrar(ctx, nome, unidade, preco)


@when(parsers.parse("altera o preço do produto para {preco}"))
def _altera(ctx, preco):
    ctx["resp"] = ctx["client"].patch(f"/produtos/{ctx['id']}", headers=ctx["h"], json={"preco": preco})
    assert ctx["resp"].status_code == 200


@when("inativa o produto")
def _inativa(ctx):
    ctx["resp"] = ctx["client"].patch(f"/produtos/{ctx['id']}", headers=ctx["h"], json={"ativo": False})
    assert ctx["resp"].status_code == 200


@when("consulta a lista de produtos sem sessão", target_fixture="ctx")
def _sem_sessao(client):
    return {"resp": client.get("/produtos")}


@then(parsers.parse("o produto é criado ativo com preço {preco}"))
def _criado(ctx, preco):
    assert ctx["resp"].status_code == 201
    corpo = ctx["resp"].json()
    assert corpo["ativo"] is True
    assert Decimal(str(corpo["preco"])) == Decimal(preco)


@then("ele aparece na lista de produtos")
def _lista(ctx):
    nomes = [p["nome"] for p in ctx["client"].get("/produtos", headers=ctx["h"]).json()]
    assert nomes == ["tomate"]


@then("o cadastro é recusado por nome repetido")
def _repetido(ctx):
    assert ctx["resp"].status_code == 409
    assert ctx["resp"].json()["detail"] == "Já existe um produto com esse nome."


@then("o cadastro é recusado por dados inválidos")
def _invalido(ctx):
    assert ctx["resp"].status_code == 422


def _produto():
    return rodar(lambda s: s.scalar(select(Produto)))


@then(parsers.parse("o preço do produto passa a ser {preco}"))
def _preco(ctx, preco):
    assert _produto().preco == Decimal(preco)


@then(parsers.parse("o pedido existente continua com o preço {preco}"))
def _pedido_antigo(preco):
    item = rodar(lambda s: s.scalar(select(ItemPedido)))
    assert item.preco_unitario == Decimal(preco)


@then("o produto fica inativo")
def _inativo(ctx):
    assert _produto().ativo is False


@then("um novo pedido de tomate não usa preço do catálogo")
def _sem_preco(ctx):
    ctx["llm"]["responder"](("tomate", 1, "kg"))
    ctx["client"].post("/webhook/whatsapp", json=mensagem("quero 1 kg de tomate"))
    item = rodar(lambda s: s.scalar(select(ItemPedido)))
    assert item.preco_unitario is None


@then("o acesso é negado")
def _negado(ctx):
    assert ctx["resp"].status_code == 401
