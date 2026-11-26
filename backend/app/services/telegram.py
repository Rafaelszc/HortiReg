"""Cliente HTTP para a Bot API do Telegram (HortiReg / @HortRegBot)."""

import httpx

from app.config import settings


def _token() -> str:
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN não configurado")
    return settings.telegram_bot_token


def _api_url(metodo: str) -> str:
    return f"{settings.telegram_api_url.rstrip('/')}/bot{_token()}/{metodo}"


async def enviar_texto(
    chat_id: int | str,
    texto: str,
    parse_mode: str | None = None,
    reply_markup: dict | None = None,
) -> dict:
    """Envia uma mensagem de texto para um chat do Telegram."""
    payload: dict = {"chat_id": chat_id, "text": texto}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(_api_url("sendMessage"), json=payload)
        r.raise_for_status()
        return r.json()


async def responder_callback(callback_query_id: str, texto: str | None = None) -> dict:
    """Confirma o clique em um botão inline para encerrar o estado de carregamento no Telegram."""
    payload: dict = {"callback_query_id": callback_query_id}
    if texto:
        payload["text"] = texto
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(_api_url("answerCallbackQuery"), json=payload)
        r.raise_for_status()
        return r.json()


async def baixar_audio(file_id: str) -> bytes:
    """Consulta o caminho do arquivo no Telegram (getFile) e baixa os bytes do áudio."""
    async with httpx.AsyncClient(timeout=60) as client:
        meta = await client.post(_api_url("getFile"), json={"file_id": file_id})
        meta.raise_for_status()
        file_path = meta.json()["result"]["file_path"]
        download_url = f"{settings.telegram_api_url.rstrip('/')}/file/bot{_token()}/{file_path}"
        arquivo = await client.get(download_url)
        arquivo.raise_for_status()
        return arquivo.content


async def configurar_webhook(url: str, secret_token: str | None = None) -> dict:
    """Registra a URL de webhook do bot na Bot API do Telegram."""
    payload: dict = {"url": url}
    if secret_token:
        payload["secret_token"] = secret_token
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(_api_url("setWebhook"), json=payload)
        r.raise_for_status()
        return r.json()


async def remover_webhook() -> dict:
    """Remove o webhook configurado na Bot API do Telegram."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(_api_url("deleteWebhook"))
        r.raise_for_status()
        return r.json()


async def info_webhook() -> dict:
    """Consulta o status atual do webhook na Bot API do Telegram."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(_api_url("getWebhookInfo"))
        r.raise_for_status()
        return r.json()


async def obter_me() -> dict:
    """Retorna os metadados do bot autenticado (getMe)."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(_api_url("getMe"))
        r.raise_for_status()
        return r.json()


async def buscar_updates(offset: int | None = None, timeout: int = 25) -> list[dict]:
    """Busca novos updates via long polling (getUpdates) para uso em desenvolvimento local."""
    payload: dict = {"timeout": timeout, "allowed_updates": ["message", "callback_query"]}
    if offset is not None:
        payload["offset"] = offset
    async with httpx.AsyncClient(timeout=timeout + 10) as client:
        r = await client.post(_api_url("getUpdates"), json=payload)
        r.raise_for_status()
        return r.json().get("result", [])
