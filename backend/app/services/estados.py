"""Máquina de estados em memória para a conversa de cada cliente no bot do Telegram."""

import asyncio
import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum

from app.config import settings

log = logging.getLogger("sgv.estados")

TimeoutCallback = Callable[[int, int | None], Awaitable[None]]


class EstadoConversa(str, Enum):
    ESPERANDO = "ESPERANDO"
    FAZENDO_PEDIDO = "FAZENDO_PEDIDO"
    AGUARDANDO_CONFIRMACAO = "AGUARDANDO_CONFIRMACAO"
    EDITANDO = "EDITANDO"
    PEDIDO_CONFIRMADO = "PEDIDO_CONFIRMADO"


ESTADOS_COM_TIMER = frozenset({EstadoConversa.AGUARDANDO_CONFIRMACAO, EstadoConversa.EDITANDO})


@dataclass
class SessaoConversa:
    estado: EstadoConversa = EstadoConversa.ESPERANDO
    pedido_id: int | None = None
    timer: asyncio.Task | None = None


_sessoes: dict[int, SessaoConversa] = {}


def obter(chat_id: int) -> SessaoConversa:
    """Retorna a sessão atual do chat (ou uma sessão padrão em ESPERANDO)."""
    return _sessoes.get(chat_id, SessaoConversa())


def obter_estado(chat_id: int) -> EstadoConversa:
    """Retorna o estado atual da conversa do chat."""
    return obter(chat_id).estado


def _cancelar_timer(sessao: SessaoConversa | None) -> None:
    if sessao and sessao.timer and not sessao.timer.done():
        sessao.timer.cancel()


def definir(
    chat_id: int,
    estado: EstadoConversa,
    pedido_id: int | None = None,
    on_timeout: TimeoutCallback | None = None,
    timeout_segundos: float | None = None,
) -> SessaoConversa:
    """Atualiza o estado do chat e reinicia o timer de inatividade quando aplicável."""
    _cancelar_timer(_sessoes.get(chat_id))

    if estado == EstadoConversa.ESPERANDO:
        _sessoes.pop(chat_id, None)
        return SessaoConversa()

    sessao = SessaoConversa(estado=estado, pedido_id=pedido_id)
    _sessoes[chat_id] = sessao

    if estado in ESTADOS_COM_TIMER and on_timeout is not None:
        prazo = settings.telegram_estado_timeout_segundos if timeout_segundos is None else timeout_segundos
        if prazo > 0:
            sessao.timer = asyncio.create_task(_aguardar_timeout(chat_id, sessao, prazo, on_timeout))

    return sessao


async def _aguardar_timeout(
    chat_id: int,
    sessao: SessaoConversa,
    prazo: float,
    on_timeout: TimeoutCallback,
) -> None:
    try:
        await asyncio.sleep(prazo)
        # Só expira se ainda for a mesma sessão ativa deste chat.
        if _sessoes.get(chat_id) is not sessao:
            return
        pedido_id = sessao.pedido_id
        _sessoes.pop(chat_id, None)
        log.info("Sessão do chat %s expirou após %.0fs (pedido=%s)", chat_id, prazo, pedido_id)
        await on_timeout(chat_id, pedido_id)
    except asyncio.CancelledError:
        return
    except Exception:
        log.exception("Erro ao executar callback de timeout do chat %s", chat_id)


def resetar(chat_id: int) -> None:
    """Cancela o timer ativo e volta o chat para ESPERANDO."""
    _cancelar_timer(_sessoes.pop(chat_id, None))


def limpar_todos() -> None:
    """Cancela todos os timers e limpa as sessões em memória (shutdown e testes)."""
    for sessao in _sessoes.values():
        _cancelar_timer(sessao)
    _sessoes.clear()
