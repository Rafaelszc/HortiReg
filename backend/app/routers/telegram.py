"""Rotas do bot do Telegram: webhook de updates e administração do webhook."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.config import settings
from app.routers.auth import get_current_admin
from app.schemas.telegram import TelegramBotInfo, WebhookConfigRequest
from app.services import telegram, telegram_bot
from app.services.webhook_auth import exigir_secret_telegram

router = APIRouter(tags=["telegram"])


@router.post("/webhook/telegram", dependencies=[Depends(exigir_secret_telegram)])
async def receber_update(payload: dict, background: BackgroundTasks):
    """Responde 200 imediatamente ao Telegram e processa o update em segundo plano."""
    if "message" not in payload and "callback_query" not in payload:
        return {"ignored": True}
    background.add_task(telegram_bot.processar_update, payload)
    return {"received": True}


@router.get("/telegram/info", response_model=TelegramBotInfo, dependencies=[Depends(get_current_admin)])
async def info_bot():
    """Retorna os dados configurados do bot HortiReg (@HortRegBot)."""
    return TelegramBotInfo(
        nome=settings.telegram_bot_name,
        username=settings.telegram_bot_username,
        token_configurado=bool(settings.telegram_bot_token),
        webhook_url=settings.telegram_webhook_url,
    )


@router.get("/telegram/webhook", dependencies=[Depends(get_current_admin)])
async def consultar_webhook():
    """Consulta o status do webhook na Bot API do Telegram."""
    try:
        return await telegram.info_webhook()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/telegram/webhook", dependencies=[Depends(get_current_admin)])
async def configurar_webhook(body: WebhookConfigRequest | None = None):
    """Registra a URL pública do webhook na Bot API do Telegram."""
    url = (body.url if body and body.url else settings.telegram_webhook_url).strip()
    if not url:
        raise HTTPException(status_code=400, detail="Informe a URL do webhook ou defina TELEGRAM_WEBHOOK_URL")
    try:
        return await telegram.configurar_webhook(url, secret_token=settings.telegram_webhook_secret or None)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/telegram/webhook", dependencies=[Depends(get_current_admin)])
async def remover_webhook():
    """Remove o webhook configurado na Bot API do Telegram."""
    try:
        return await telegram.remover_webhook()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
