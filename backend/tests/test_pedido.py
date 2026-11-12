from datetime import timedelta

from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import func, select, update

from app.config import settings
from app.models import ItemPedido, Pedido, StatusPedido
from app.routers.webhook import MSG_IA_FALHA, MSG_OPCOES
from app.services import expiracao
from tests.conftest import TELEFONE, itens_do_texto, mensagem, rodar

scenarios("features/pedido.feature")
scenarios("features/pedido_confirmacao.feature")
scenarios("features/pedido_expiracao.feature")
OUTRO_TELEFONE = "5583988887777"


@given("um catálogo ativo com tomate e banana", target_fixture="ctx")
def _catalogo(catalogo, client, whatsapp_fake, llm_fake):
    return {"client": client, "enviadas": whatsapp_fake, "llm": llm_fake}


@given(parsers.re(r"que a IA extrai (?P<texto>.+)"))
def _ia_extrai(ctx, texto):
    ctx["llm"]["responder"](*itens_do_texto(texto))


@given("que a IA não extrai nenhum item")
def _ia_vazia(ctx):
    ctx["llm"]["responder"]()


@given("que a IA está fora do ar")
def _ia_fora(ctx):
    ctx["llm"]["erro"] = RuntimeError("503 Service Unavailable")


@given("que a IA demora mais que o limite de espera")
def _ia_demora(ctx, monkeypatch):
    monkeypatch.setattr(settings, "ia_texto_timeout_segundos", 0.05)
    ctx["llm"]["demora"] = 1


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
    assert MSG_OPCOES in texto


@then("nenhum pedido é criado")
def _nenhum(ctx):
    assert rodar(lambda s: s.scalar(select(func.count()).select_from(Pedido))) == 0


@then("o cliente é avisado que o pedido não pôde ser lido agora")
def _avisado(ctx):
    assert ctx["enviadas"] == [(TELEFONE, MSG_IA_FALHA)]  # sempre uma resposta: nunca silêncio nem duplicada


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


@when(parsers.parse('outro número envia "{texto}"'))
def _outro_envia(ctx, texto, caplog):
    ctx["log"] = caplog
    assert ctx["client"].post("/webhook/whatsapp", json=mensagem(texto, telefone=OUTRO_TELEFONE)).status_code == 200


@then("o cliente recebe a confirmação com o número do pedido")
def _confirmacao_com_numero(ctx):
    assert ctx["enviadas"][-1] == (TELEFONE, "✅ Pedido #1 confirmado! Avisaremos quando sair para entrega.")


@then("o pedido continua aguardando confirmação")
def _continua(ctx):
    pedido = list(_pedidos())[0]
    assert pedido.status == StatusPedido.AGUARDANDO_CONFIRMACAO


@then("o sistema repete as opções 1, 2 e 3")
def _repete(ctx):
    assert ctx["enviadas"][-1] == (TELEFONE, f"Não entendi sua resposta sobre o pedido #1. {MSG_OPCOES}")


@then("nenhum pedido novo é criado")
def _sem_novo(ctx):
    assert len(list(_pedidos())) == 1


@then("a tentativa é registrada em log sem o telefone")
def _log(ctx):
    avisos = [r.getMessage() for r in ctx["log"].records if r.name == "sgv.webhook" and r.levelname == "WARNING"]
    assert len(avisos) == 1
    assert OUTRO_TELEFONE not in avisos[0]


@then("o pedido fica cancelado")
def _cancelado(ctx):
    assert list(_pedidos())[0].status == StatusPedido.CANCELADO


@then(parsers.parse('o cliente recebe "{trecho}"'))
def _recebe(ctx, trecho):
    assert trecho in ctx["enviadas"][-1][1]


@given(parsers.parse("que o pedido está aguardando confirmação há {minutos:d} minutos"))
def _envelhecer(ctx, minutos):
    async def _atualizar(s):
        await s.execute(update(Pedido).values(criado_em=func.now() - timedelta(minutes=minutos)))
        await s.commit()

    rodar(_atualizar)


@when("o prazo de expiração é verificado")
def _verificar_prazo(ctx):
    rodar(expiracao.expirar_pendentes)


@then("o pedido fica expirado")
def _expirado(ctx):
    assert list(_pedidos())[0].status == StatusPedido.EXPIRADO


@then("o pedido não entra na lista de separação")
def _fora_da_separacao(ctx, token):
    r = ctx["client"].get("/pedidos/separacao", headers=token)
    assert r.status_code == 200
    assert r.json() == []
