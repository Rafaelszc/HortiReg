from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import func, select

from app.config import settings
from app.models import Pedido
from tests.conftest import mensagem, rodar

scenarios("features/webhook_seguranca.feature")


@given("um catálogo ativo com tomate e banana", target_fixture="ctx")
def _catalogo(catalogo, client, whatsapp_fake, llm_fake):
    return {"client": client, "llm": llm_fake}


@given(parsers.re(r'que a IA extrai "(?P<qtd>\S+) (?P<unidade>\S+) de (?P<nome>[^"]+)"'))
def _ia_extrai(ctx, qtd, unidade, nome):
    ctx["llm"]["responder"]((nome, float(qtd), unidade))


@given(parsers.parse('que o webhook exige o token "{token}"'))
def _exige_token(monkeypatch, token):
    monkeypatch.setattr(settings, "webhook_token", token)


def _enviar(ctx, url="/webhook/whatsapp", headers=None):
    ctx["resposta"] = ctx["client"].post(url, json=mensagem("quero 2 kg de tomate"), headers=headers or {})


@when("a Evolution envia um pedido sem token")
def _sem_token(ctx):
    _enviar(ctx)


@when(parsers.parse('a Evolution envia um pedido com o token "{token}" na URL'))
def _token_url(ctx, token):
    _enviar(ctx, url=f"/webhook/whatsapp?token={token}")


@when(parsers.parse('a Evolution envia um pedido com o token "{token}" no cabeçalho'))
def _token_cabecalho(ctx, token):
    _enviar(ctx, headers={"X-Webhook-Token": token})


@then(parsers.parse("o webhook responde {codigo:d}"))
def _codigo(ctx, codigo):
    assert ctx["resposta"].status_code == codigo


def _total() -> int:
    return rodar(lambda s: s.scalar(select(func.count()).select_from(Pedido)))


@then("nenhum pedido é criado")
def _nenhum(ctx):
    assert _total() == 0


@then("um pedido é criado")
def _criado(ctx):
    assert _total() == 1
