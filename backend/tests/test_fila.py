from datetime import timedelta

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import func, select

from app.models import MensagemRecebida, Pedido, StatusMensagem, StatusPedido
from app.routers import webhook
from app.routers.webhook import MSG_IA_FALHA, MSG_OPCOES
from app.services import fila
from tests.conftest import TELEFONE, _Sessao, itens_do_texto, mensagem, mensagem_audio, rodar

scenarios("features/fila_retentativa.feature")

PASSO = 10  # segundos entre execuções do laço da fila (igual ao padrão em produção)


@pytest.fixture(autouse=True)
def _sessao_de_teste(monkeypatch):
    """A fila roda fora do loop do TestClient; sessões sem pool funcionam em qualquer loop."""
    monkeypatch.setattr(fila, "SessionLocal", _Sessao)
    monkeypatch.setattr(webhook, "SessionLocal", _Sessao)


def _reprocessar() -> None:
    rodar(lambda _s: fila.reprocessar_pendentes(webhook.processar_mensagem))


def _avancar(relogio, segundos: int) -> None:
    """Passa o tempo simulado, rodando o laço da fila a cada PASSO segundos."""
    for _ in range(segundos // PASSO):
        relogio["agora"] += timedelta(seconds=PASSO)
        _reprocessar()


def _mensagens() -> list[MensagemRecebida]:
    return list(rodar(lambda s: s.scalars(select(MensagemRecebida).order_by(MensagemRecebida.criado_em))))


def _pedidos() -> list[Pedido]:
    return list(rodar(lambda s: s.scalars(select(Pedido).order_by(Pedido.id))))


def _enviar(ctx, evento) -> None:
    assert ctx["client"].post("/webhook/whatsapp", json=evento).status_code == 200
    ctx["relogio"]["agora"] += timedelta(seconds=1)  # mensagens chegam em instantes distintos


@given("um catálogo ativo com tomate e banana", target_fixture="ctx")
def _catalogo(catalogo, client, whatsapp_fake, llm_fake, audio_fake, relogio):
    return {"client": client, "enviadas": whatsapp_fake, "llm": llm_fake, "audio": audio_fake, "relogio": relogio}


@given(parsers.re(r"que a IA extrai (?P<texto>.+)"))
def _ia_extrai(ctx, texto):
    ctx["llm"]["responder"](*itens_do_texto(texto))


@given("que a IA está fora do ar")
def _ia_fora(ctx):
    ctx["llm"]["erro"] = RuntimeError("503 Service Unavailable")


@given("que o download do áudio falha")
def _download_falha(ctx):
    ctx["audio"]["erro"] = RuntimeError("Evolution fora do ar")


@given(parsers.parse('o cliente envia "{texto}"'))
@when(parsers.parse('o cliente envia "{texto}"'))
def _envia(ctx, texto):
    _enviar(ctx, mensagem(texto))


@given(parsers.parse("o cliente envia um áudio de {segundos:d} segundos"))
def _envia_audio(ctx, segundos):
    _enviar(ctx, mensagem_audio(segundos=segundos))


@given(parsers.parse("{n:d} clientes enviam pedidos durante a falha"))
def _varios_clientes(ctx, n):
    for i in range(n):
        _enviar(ctx, mensagem("quero 2 kg de tomate", telefone=f"55839999{i:05d}"))


@when(parsers.parse('o cliente envia "{texto}" e a Evolution reenvia o mesmo evento'))
def _envia_duas_vezes(ctx, texto):
    evento = mensagem(texto)
    for _ in range(2):
        _enviar(ctx, evento)


@when(parsers.parse("passam {minutos:d} minutos com a IA fora do ar"))
def _passam_minutos(ctx, minutos):
    _avancar(ctx["relogio"], minutos * 60)


@when("a IA volta")
def _ia_volta(ctx):
    ctx["llm"]["erro"] = None
    ctx["volta_em"] = ctx["relogio"]["agora"]


@when("a IA volta e a fila é reprocessada")
def _ia_volta_e_reprocessa(ctx):
    _ia_volta(ctx)
    ctx["relogio"]["agora"] += timedelta(seconds=fila.espera(10).total_seconds())  # além da maior espera
    _reprocessar()


@when("o download volta e a fila é reprocessada")
def _download_volta(ctx):
    ctx["audio"]["erro"] = None
    ctx["relogio"]["agora"] += timedelta(seconds=fila.espera(10).total_seconds())
    _reprocessar()


@then("a mensagem fica gravada aguardando nova tentativa")
def _gravada(ctx):
    (msg,) = _mensagens()
    assert msg.status == StatusMensagem.PENDENTE
    assert msg.tentativas == 1
    assert msg.payload["message"]["conversation"] == "quero 2 kg de tomate"


@then("apenas uma mensagem fica gravada")
def _uma_gravada(ctx):
    assert len(_mensagens()) == 1


@then("o cliente é avisado uma vez que o pedido está em processamento")
def _avisado(ctx):
    assert ctx["enviadas"] == [(TELEFONE, fila.MSG_EM_PROCESSAMENTO)]


@then("nenhum pedido é criado")
def _nenhum(ctx):
    assert rodar(lambda s: s.scalar(select(func.count()).select_from(Pedido))) == 0


@then("um pedido é criado aguardando confirmação")
def _criado(ctx):
    (pedido,) = _pedidos()
    assert pedido.status == StatusPedido.AGUARDANDO_CONFIRMACAO


@then("o cliente recebe o resumo do pedido")
def _resumo(ctx):
    numero, texto = ctx["enviadas"][-1]
    assert numero == TELEFONE
    assert "Entendi seu pedido #1" in texto
    assert MSG_OPCOES in texto


@then("a mensagem fica como processada")
def _processada(ctx):
    (msg,) = _mensagens()
    assert msg.status == StatusMensagem.PROCESSADA


@then("todas as mensagens são processadas em até 5 minutos")
def _ate_5_minutos(ctx):
    relogio = ctx["relogio"]
    limite = ctx["volta_em"] + timedelta(minutes=5)
    while relogio["agora"] < limite and any(m.status == StatusMensagem.PENDENTE for m in _mensagens()):
        relogio["agora"] += timedelta(seconds=PASSO)
        _reprocessar()
    mensagens = _mensagens()
    assert len(mensagens) == 3  # nenhuma perdida
    assert all(m.status == StatusMensagem.PROCESSADA for m in mensagens)


@then(parsers.parse("{n:d} pedidos são criados aguardando confirmação"))
def _n_pedidos(ctx, n):
    pedidos = _pedidos()
    assert len(pedidos) == n
    assert all(p.status == StatusPedido.AGUARDANDO_CONFIRMACAO for p in pedidos)


@then("cada cliente recebeu um único aviso de processamento")
def _um_aviso_por_cliente(ctx):
    avisos = [numero for numero, texto in ctx["enviadas"] if texto == fila.MSG_EM_PROCESSAMENTO]
    assert len(avisos) == len(set(avisos)) == 3


@then("a mensagem fica marcada como falha")
def _falhou(ctx):
    (msg,) = _mensagens()
    assert msg.status == StatusMensagem.FALHOU


@then("o cliente é avisado que o pedido não pôde ser lido")
def _aviso_final(ctx):
    assert ctx["enviadas"] == [(TELEFONE, fila.MSG_EM_PROCESSAMENTO), (TELEFONE, MSG_IA_FALHA)]


@then(parsers.parse("o áudio foi baixado {n:d} vezes"))
def _baixado(ctx, n):
    assert ctx["audio"]["baixados"] == n


@then("o pedido fica confirmado")
def _confirmado(ctx):
    (pedido,) = _pedidos()
    assert pedido.status == StatusPedido.CONFIRMADO
