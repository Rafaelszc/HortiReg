"""Autenticação do webhook: a Evolution manda o token na URL (?token=) ou no cabeçalho X-Webhook-Token."""

import hmac

from fastapi import Header, HTTPException, Query

from app.config import settings


async def exigir_token(
    token: str | None = Query(default=None),
    x_webhook_token: str | None = Header(default=None),
) -> None:
    """Sem WEBHOOK_TOKEN configurado o webhook fica aberto (desenvolvimento); com ele, só passa quem o enviar."""
    esperado = settings.webhook_token
    if not esperado:
        return
    recebido = x_webhook_token or token or ""
    if not hmac.compare_digest(recebido.encode(), esperado.encode()):
        raise HTTPException(status_code=401, detail="Token do webhook inválido")
