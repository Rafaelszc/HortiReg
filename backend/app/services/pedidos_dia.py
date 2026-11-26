"""Pedidos confirmados do dia para o painel (US-12)."""

from datetime import datetime, time, timedelta, timezone

from app.config import settings
from app.models import Pedido
from app.services import catalogo, security


def intervalo_de_hoje() -> tuple[datetime, datetime]:
    """Início e fim do dia corrente no fuso da feira (o Brasil não tem horário de verão desde 2019)."""
    fuso = timezone(timedelta(hours=settings.fuso_horario_utc))
    hoje = security.agora().astimezone(fuso).date()
    inicio = datetime.combine(hoje, time.min, tzinfo=fuso)
    return inicio, inicio + timedelta(days=1)


def resumo(pedido: Pedido) -> dict:
    """Cliente, itens, endereço, valor e status. Item fora do catálogo (sem preço) não entra no valor."""
    # Mesmo cálculo do resumo do WhatsApp (arredonda por item), senão painel e mensagem divergem
    valor = catalogo.total_estimado(pedido.itens)
    return {
        "id": pedido.id,
        "cliente": pedido.cliente.nome or pedido.cliente.telefone,
        "telefone": pedido.cliente.telefone,
        "endereco": pedido.cliente.endereco,
        "itens": [
            {"nome": i.nome, "quantidade": float(i.quantidade), "unidade": i.unidade} for i in pedido.itens
        ],
        "valor": float(valor),
        "status": pedido.status,
        "criado_em": pedido.criado_em.isoformat(),
    }
