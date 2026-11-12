from decimal import Decimal

from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy import func, select

from app.config import settings
from app.models import Pedido, Produto, StatusPedido
from app.routers.webhook import MSG_OPCOES
from tests.conftest import TELEFONE, itens_do_texto, mensagem_audio, rodar

scenarios("features/pedido_audio.feature")


@given("um catálogo ativo com tomate e macaxeira", target_fixture="ctx")
def _catalogo(client, whatsapp_fake, llm_fake, audio_fake):
    async def _criar(session):
        session.add_all(
            [
                Produto(nome="tomate", unidade="kg", preco=Decimal("6.50")),
                Produto(nome="macaxeira", unidade="kg", preco=Decimal("5.00")),
            ]
        )
        await session.commit()

    rodar(_criar)
    return {"client": client, "enviadas": whatsapp_fake, "llm": llm_fake, "audio": audio_fake}


@given(parsers.re(r"que a IA extrai (?P<texto>.+)"))
def _ia_extrai(ctx, texto):
    ctx["llm"]["responder"](*itens_do_texto(texto))


@given("que a IA não extrai nenhum item")
def _ia_vazia(ctx):
    ctx["llm"]["responder"]()


@given(parsers.parse("que o arquivo baixado tem {n:d} megabytes"))
def _arquivo_grande(ctx, n):
    ctx["audio"]["dados"] = b"x" * (n * 1_000_000)


@given("que o download do áudio falha")
def _download_falha(ctx):
    ctx["audio"]["erro"] = RuntimeError("Evolution fora do ar")


@given("que a IA está fora do ar")
def _ia_fora(ctx):
    ctx["llm"]["erro"] = RuntimeError("503 Service Unavailable")


@given("que a IA demora mais que o limite de espera")
def _ia_demora(ctx, monkeypatch):
    monkeypatch.setattr(settings, "audio_timeout_segundos", 0.05)
    ctx["llm"]["demora"] = 1


def _enviar(ctx, evento):
    assert ctx["client"].post("/webhook/whatsapp", json=evento).status_code == 200


@when(parsers.parse("o cliente envia um áudio de {segundos:d} segundos"))
def _envia_audio(ctx, segundos):
    _enviar(ctx, mensagem_audio(segundos=segundos))


@when(parsers.parse('o cliente envia um áudio no formato "{mime}"'))
def _envia_audio_formato(ctx, mime):
    _enviar(ctx, mensagem_audio(segundos=10, mimetype=mime))


@when("o cliente envia um áudio sem duração informada")
def _envia_audio_sem_duracao(ctx):
    _enviar(ctx, mensagem_audio(segundos=None))


def _pedidos():
    return list(rodar(lambda s: s.scalars(select(Pedido).order_by(Pedido.id))))


@then(parsers.parse("um pedido é criado aguardando confirmação com {n:d} itens"))
def _criado(ctx, n):
    (pedido,) = _pedidos()
    assert pedido.status == StatusPedido.AGUARDANDO_CONFIRMACAO
    assert len(pedido.itens) == n


@then(parsers.parse('o cliente recebe o resumo com valor estimado de "{valor}"'))
def _resumo(ctx, valor):
    numero, texto = ctx["enviadas"][-1]
    assert numero == TELEFONE
    assert f"Valor estimado: {valor}" in texto
    assert MSG_OPCOES in texto


@then(parsers.parse('o áudio foi enviado à IA como "{mime}"'))
def _mime(ctx, mime):
    assert ctx["llm"]["audio"] == ctx["audio"]["dados"]
    assert ctx["llm"]["audio_mime"] == mime


@then("nenhum pedido é criado")
def _nenhum(ctx):
    assert rodar(lambda s: s.scalar(select(func.count()).select_from(Pedido))) == 0


@then("o áudio não é baixado nem enviado à IA")
def _nao_baixou(ctx):
    assert ctx["audio"]["baixados"] == 0
    assert ctx["llm"]["chamadas"] == 0


@then("a IA não é chamada")
def _ia_nao_chamada(ctx):
    assert ctx["llm"]["chamadas"] == 0


@then("o cliente é orientado a reenviar em áudio mais curto ou em texto")
def _orienta(ctx):
    assert len(ctx["enviadas"]) == 1  # sempre uma resposta: nunca silêncio nem duplicada
    numero, texto = ctx["enviadas"][0]
    assert numero == TELEFONE
    assert "áudio" in texto and "texto" in texto
    assert 'Exemplo: "quero 2 kg de tomate' in texto
