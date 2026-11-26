"""Schemas de configuração e status do bot do Telegram."""

from pydantic import BaseModel


class WebhookConfigRequest(BaseModel):
    url: str | None = None


class TelegramBotInfo(BaseModel):
    nome: str
    username: str
    token_configurado: bool
    webhook_url: str
