"""US-11: endereço de entrega do cliente."""

import logging
from datetime import timedelta

import pytest
from pydantic import ValidationError
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import select

from app.database import engine
from app.models import Cliente, MensagemRecebida, Pedido, RascunhoEndereco, StatusMensagem, StatusPedido
from app.routers import webhook
from app.routers.webhook import MSG_IA_FALHA_ENDERECO, MSG_OPCOES
from app.schemas.pedido import EnderecoExtraido, PedidoExtraido
from app.services import endereco, fila
from tests.conftest import ENDERECO, TELEFONE, _Sessao, mensagem, mensagem_audio, rodar

scenarios("features/pedido_endereco.feature")

COMPLETO = {"rua": "Rua das Flores", "numero": "120", "bairro": "Catolé", "cidade": "Campina Grande"}
# o que a IA (falsa) extrai de cada texto dos cenários
EXTRACOES = {
    ENDERECO: COMPLETO,
    "Rua das Flores, Catolé, Campina Grande": {**COMPLETO, "numero": None},
    "120, Catolé, Campina Grande": {**COMPLETO, "rua": None},
}
PEDIDO = ("tomate", 2, "kg")


@pytest.fixture
def ctx(catalogo, client, whatsapp_fake, llm_fake, audio_fake):
    return {"client": client, "enviadas": whatsapp_fake, "llm": llm_fake, "audio": audio_fake}


def _enviar(ctx, evento):
    assert ctx["client"].post("/webhook/whatsapp", json=evento).status_code == 200


def _dizer(ctx, texto, *itens, endereco=None) -> str:
    """Envia o texto com a IA falsa preparada e devolve a última resposta do bot."""
    ctx["llm"]["responder"](*itens, endereco=endereco)
    _enviar(ctx, mensagem(texto))
    return ctx["enviadas"][-1][1]


def _pedir(ctx) -> str:
    return _dizer(ctx, "quero 2 kg de tomate", PEDIDO)


def _cliente() -> Cliente | None:
    return rodar(lambda s: s.scalar(select(Cliente).where(Cliente.telefone == TELEFONE)))


def _pedido() -> Pedido:
    return rodar(lambda s: s.scalar(select(Pedido).order_by(Pedido.id.desc())))


def _rascunhos() -> list[RascunhoEndereco]:
    return list(rodar(lambda s: s.scalars(select(RascunhoEndereco))))


@given("um cliente sem endereço salvo")
def _sem_endereco(ctx):
    assert _cliente() is None


@when(parsers.parse('o cliente envia "{texto}"'))
def _envia(ctx, texto):
    _dizer(ctx, texto, endereco=EXTRACOES[texto])


@then("o endereço é salvo e mostrado ao cliente para confirmação")
def _salvo(ctx):
    assert _cliente().endereco == ENDERECO
    assert ENDERECO in ctx["enviadas"][-1][1]


@then("o próximo pedido do cliente já usa esse endereço")
def _reaproveitado(ctx):
    resumo = _pedir(ctx)
    assert f"Entrega em: {ENDERECO}" in resumo
    assert MSG_OPCOES in resumo
    _dizer(ctx, "1")
    assert _pedido().status == StatusPedido.CONFIRMADO


@then(parsers.parse('o cliente recebe o pedido de "{falta}"'))
def _pede_o_que_falta(ctx, falta):
    trecho = {"número": "Falta o número", "rua": "Falta o nome da rua"}[falta]
    assert trecho in ctx["enviadas"][-1][1]
    assert _cliente().endereco is None


@then("o pedido não pode ser confirmado sem endereço completo")
def _nao_confirma(ctx):
    assert MSG_OPCOES not in _pedir(ctx)
    resposta = _dizer(ctx, "confirmar")
    assert "Ainda não posso confirmar" in resposta
    assert _pedido().status == StatusPedido.AGUARDANDO_CONFIRMACAO


@then(parsers.parse('nenhum log da API contém "{trecho}"'))
def _sem_log(ctx, trecho, caplog):
    caplog.set_level(logging.DEBUG)
    _dizer(ctx, ENDERECO, endereco=COMPLETO)
    _pedir(ctx)
    _dizer(ctx, "1")
    assert caplog.records
    assert trecho not in caplog.text


@pytest.mark.regressao
def test_pedido_sem_endereco_pede_o_endereco(ctx):
    resumo = _pedir(ctx)
    assert "Entendi seu pedido #1" in resumo
    assert "endereço de entrega" in resumo
    assert MSG_OPCOES not in resumo

    resposta = _dizer(ctx, ENDERECO, endereco=COMPLETO)
    assert f"Entrega em: {ENDERECO}" in resposta
    assert MSG_OPCOES in resposta
    _dizer(ctx, "1")
    assert _pedido().status == StatusPedido.CONFIRMADO


@pytest.mark.regressao
@pytest.mark.parametrize("numero", ["1", "2", "3", "120", "nº 45", "120A", "s/n", "sem número"])
def test_resposta_com_numero_da_casa_nao_cancela_o_pedido(ctx, numero):
    _pedir(ctx)
    assert "Falta o número" in _dizer(ctx, "Rua das Flores", endereco={"rua": "Rua das Flores"})
    chamadas = ctx["llm"]["chamadas"]

    resposta = _dizer(ctx, numero)

    assert ctx["llm"]["chamadas"] == chamadas  # número solto não passa pela IA
    assert _pedido().status == StatusPedido.AGUARDANDO_CONFIRMACAO
    assert MSG_OPCOES in resposta
    assert _cliente().endereco.startswith("Rua das Flores, ")
    assert _rascunhos() == []


@pytest.mark.regressao
def test_cancelar_por_palavra_enquanto_falta_o_numero(ctx):
    _pedir(ctx)
    assert "*cancelar*" in _dizer(ctx, "Rua das Flores", endereco={"rua": "Rua das Flores"})
    _dizer(ctx, "cancelar")
    assert _pedido().status == StatusPedido.CANCELADO


@pytest.mark.regressao
def test_endereco_em_partes_comecando_pelo_numero(ctx):
    _pedir(ctx)
    _dizer(ctx, "120, Catolé", endereco={"numero": "120", "bairro": "Catolé"})
    _dizer(ctx, "Rua das Flores", endereco={"rua": "Rua das Flores"})
    assert _cliente().endereco == "Rua das Flores, 120, Catolé"


@pytest.mark.regressao
def test_pedido_e_endereco_na_mesma_mensagem(ctx):
    resumo = _dizer(ctx, f"quero 2 kg de tomate na {ENDERECO}", PEDIDO, endereco=COMPLETO)
    assert "Entendi seu pedido #1" in resumo
    assert f"Entrega em: {ENDERECO}" in resumo
    assert len(ctx["enviadas"]) == 1


@pytest.mark.regressao
def test_endereco_por_audio_com_pedido_pendente(ctx):
    _pedir(ctx)
    ctx["llm"]["responder"](endereco=COMPLETO)
    _enviar(ctx, mensagem_audio(segundos=10))
    assert _cliente().endereco == ENDERECO
    assert MSG_OPCOES in ctx["enviadas"][-1][1]


@pytest.mark.regressao
def test_troca_de_endereco_com_pedido_pendente(cliente_com_endereco, ctx):
    _pedir(ctx)
    novo = {"rua": "Rua do Sol", "numero": "45"}
    assert "Entrega em: Rua do Sol, 45" in _dizer(ctx, "agora é Rua do Sol, 45", endereco=novo)
    assert _cliente().endereco == "Rua do Sol, 45"


@pytest.mark.regressao
def test_troca_incompleta_bloqueia_a_confirmacao(cliente_com_endereco, ctx):
    _pedir(ctx)
    _dizer(ctx, "mudei para a Rua do Sol", endereco={"rua": "Rua do Sol"})
    assert "Ainda não posso confirmar" in _dizer(ctx, "confirmar")
    assert _pedido().status == StatusPedido.AGUARDANDO_CONFIRMACAO
    assert _cliente().endereco == ENDERECO  # o salvo só muda quando o novo estiver completo


@pytest.mark.regressao
def test_cancelar_descarta_a_troca_incompleta(cliente_com_endereco, ctx):
    _pedir(ctx)
    _dizer(ctx, "mudei para a Rua do Sol", endereco={"rua": "Rua do Sol"})
    _dizer(ctx, "cancelar")
    assert _rascunhos() == []
    assert _cliente().endereco == ENDERECO


@pytest.mark.regressao
def test_pedido_novo_descarta_troca_abandonada(cliente_com_endereco, ctx):
    _dizer(ctx, "mudei para a Rua do Sol", endereco={"rua": "Rua do Sol"})
    assert f"Entrega em: {ENDERECO}" in _pedir(ctx)
    assert _rascunhos() == []


@pytest.mark.regressao
def test_outra_rua_nao_herda_dados_do_rascunho(ctx):
    _dizer(ctx, "Rua das Flores, Catolé", endereco={"rua": "Rua das Flores", "bairro": "Catolé"})
    _dizer(ctx, "Rua do Sol, 45", endereco={"rua": "Rua do Sol", "numero": "45"})
    assert _cliente().endereco == "Rua do Sol, 45"


@pytest.mark.regressao
def test_numero_que_o_cliente_nao_escreveu_e_descartado(ctx):
    resposta = _dizer(ctx, "Rua das Flores", endereco={"rua": "Rua das Flores", "numero": "12"})
    assert "Falta o número" in resposta
    assert _cliente().endereco is None


@pytest.mark.regressao
@pytest.mark.parametrize(
    ("numero", "texto", "esperado"),
    [
        ("120", "Rua A, 120", "120"),
        ("12", "Rua A, 120", None),
        ("s/n", "Rua A, sem número", "s/n"),
        ("s/n", "Rua A", None),
        ("não informado", "Rua A", None),
        ("120", None, "120"),  # áudio: não há texto para conferir
    ],
)
def test_limpar_numero(numero, texto, esperado):
    assert endereco.limpar(EnderecoExtraido(numero=numero), texto).numero == esperado


@pytest.mark.regressao
def test_endereco_longo_cabe_na_coluna(ctx):
    longo = {"rua": "R" * 400, "numero": "1", "bairro": "B" * 400, "cidade": "C" * 400}
    _dizer(ctx, "endereço 1", endereco=longo)
    assert len(_cliente().endereco) <= 255


@pytest.mark.regressao
def test_falha_da_ia_ao_ler_o_endereco(ctx, relogio, monkeypatch):
    monkeypatch.setattr(fila, "SessionLocal", _Sessao)
    monkeypatch.setattr(webhook, "SessionLocal", _Sessao)
    _pedir(ctx)
    relogio["agora"] += timedelta(seconds=1)
    ctx["llm"]["erro"] = RuntimeError("503")

    _enviar(ctx, mensagem(ENDERECO))
    assert ctx["enviadas"][-1][1] == fila.MSG_EM_PROCESSAMENTO

    relogio["agora"] += timedelta(minutes=61)
    rodar(lambda _s: fila.reprocessar_pendentes(webhook.processar_mensagem))
    assert ctx["enviadas"][-1][1] == MSG_IA_FALHA_ENDERECO

    mensagens = rodar(lambda s: s.scalars(select(MensagemRecebida).order_by(MensagemRecebida.criado_em))).all()
    assert mensagens[-1].status == StatusMensagem.FALHOU
    assert mensagens[-1].payload == {}


@pytest.mark.regressao
@pytest.mark.seguranca
def test_conteudo_da_mensagem_e_apagado_depois_de_processada(ctx):
    _dizer(ctx, ENDERECO, endereco=COMPLETO)
    msg = rodar(lambda s: s.scalar(select(MensagemRecebida)))
    assert msg.status == StatusMensagem.PROCESSADA
    assert msg.payload == {}


@pytest.mark.regressao
@pytest.mark.seguranca
def test_erros_nao_repetem_dados_do_cliente():
    assert engine.sync_engine.hide_parameters  # erro do banco não lista os valores gravados
    with pytest.raises(ValidationError) as erro:
        PedidoExtraido.model_validate_json('{"endereco": {"rua": ["Rua das Flores"]}}')
    assert "Rua das Flores" not in str(erro.value)
