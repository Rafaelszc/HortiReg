from datetime import UTC, datetime, timedelta
from decimal import Decimal

from pytest_bdd import given, parsers, scenarios, then, when

from app.models import Cliente, ItemPedido, Pedido, StatusPedido
from app.services import catalogo, pedidos_dia
from tests.conftest import itens_do_texto, rodar

scenarios("features/pedidos_do_dia.feature")


def _criar_pedido(telefone, status, criado_em, nome=None, endereco=None, itens=(("tomate", 1, "kg", "6.50"),)):
    async def _criar(session):
        cliente = Cliente(telefone=telefone, nome=nome, endereco=endereco)
        session.add(cliente)
        await session.flush()
        session.add(
            Pedido(
                cliente_id=cliente.id,
                status=status,
                criado_em=criado_em,
                itens=[
                    ItemPedido(nome=n, quantidade=Decimal(str(q)), unidade=u, preco_unitario=p and Decimal(p))
                    for n, q, u, p in itens
                ],
            )
        )
        await session.commit()

    rodar(_criar)


@given("que o administrador está autenticado", target_fixture="ctx")
def _autenticado(token, client):
    return {"client": client, "h": token}


@given(parsers.parse('que há um pedido confirmado hoje de "{nome}" com "{texto}" no endereço "{endereco}"'))
def _confirmado_hoje(nome, texto, endereco):
    itens = [(n, q, u, "6.50") for n, q, u in itens_do_texto(f'"{texto}"')]
    _criar_pedido("5583900000001", StatusPedido.CONFIRMADO, datetime.now(UTC), nome, endereco, itens)


@given("que há um pedido confirmado ontem e um pedido aguardando confirmação hoje")
def _outros():
    _criar_pedido("5583900000002", StatusPedido.CONFIRMADO, datetime.now(UTC) - timedelta(days=1))
    _criar_pedido("5583900000003", StatusPedido.AGUARDANDO_CONFIRMACAO, datetime.now(UTC))


@given("que não há pedidos confirmados hoje")
def _nenhum():
    _criar_pedido("5583900000004", StatusPedido.CANCELADO, datetime.now(UTC))


@when("consulta os pedidos do dia")
def _consulta(ctx):
    ctx["resp"] = ctx["client"].get("/pedidos/dia", headers=ctx["h"])
    assert ctx["resp"].status_code == 200


@when("consulta os pedidos do dia sem sessão", target_fixture="ctx")
def _sem_sessao(client):
    return {"resp": client.get("/pedidos/dia")}


@then(parsers.parse('recebe 1 pedido de "{nome}" no endereço "{endereco}" com valor {valor:f} e status "{status}"'))
def _um_pedido(ctx, nome, endereco, valor, status):
    pedidos = ctx["resp"].json()
    assert len(pedidos) == 1
    p = pedidos[0]
    assert (p["cliente"], p["endereco"], p["valor"], p["status"]) == (nome, endereco, valor, status)
    assert p["itens"] == [{"nome": "tomate", "quantidade": 2.0, "unidade": "kg"}]


@then("recebe uma lista vazia")
def _vazia(ctx):
    assert ctx["resp"].json() == []


@then(parsers.parse("a resposta é {codigo:d}"))
def _codigo(ctx, codigo):
    assert ctx["resp"].status_code == codigo


def test_intervalo_usa_o_fuso_da_feira(relogio):
    # 01:30 UTC de 26/11 ainda é 25/11 às 22:30 em Campina Grande (UTC-3)
    relogio["agora"] = datetime(2026, 11, 26, 1, 30, tzinfo=UTC)
    inicio, fim = pedidos_dia.intervalo_de_hoje()
    assert inicio == datetime(2026, 11, 25, 3, 0, tzinfo=UTC)
    assert fim - inicio == timedelta(days=1)


def test_item_fora_do_catalogo_nao_soma_no_valor(token, client):
    _criar_pedido(
        "5583900000005",
        StatusPedido.CONFIRMADO,
        datetime.now(UTC),
        itens=(("tomate", 2, "kg", "6.50"), ("jaca", 1, "un", None)),
    )
    p = client.get("/pedidos/dia", headers=token).json()[0]
    assert p["valor"] == 13.0
    assert p["cliente"] == "5583900000005"  # sem nome, mostra o telefone
    assert len(p["itens"]) == 2


def test_valor_igual_ao_resumo_do_whatsapp(token, client):
    # 0,25 kg x R$ 6,50 = 1,625 por item; o WhatsApp arredonda cada item, então o painel também
    itens = (("tomate", 0.25, "kg", "6.50"), ("cebola", 0.25, "kg", "6.50"))
    _criar_pedido("5583900000006", StatusPedido.CONFIRMADO, datetime.now(UTC), itens=itens)
    p = client.get("/pedidos/dia", headers=token).json()[0]
    esperado = catalogo.total_estimado(
        [ItemPedido(nome=n, quantidade=Decimal(str(q)), unidade=u, preco_unitario=Decimal(pr)) for n, q, u, pr in itens]
    )
    assert p["valor"] == float(esperado) == 3.24
