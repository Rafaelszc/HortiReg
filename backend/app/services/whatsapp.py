import base64

import httpx

from app.config import settings


def _headers() -> dict[str, str]:
    return {"apikey": settings.evolution_api_key}


async def enviar_texto(numero: str, texto: str) -> None:
    """Envia uma mensagem de texto via Evolution API."""
    url = f"{settings.evolution_url}/message/sendText/{settings.evolution_instance}"
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(url, headers=_headers(), json={"number": numero, "text": texto})
        r.raise_for_status()


async def baixar_audio(message_key: dict) -> bytes:
    """Pede à Evolution API o áudio de uma mensagem (em base64) e devolve os bytes."""
    url = f"{settings.evolution_url}/chat/getBase64FromMediaMessage/{settings.evolution_instance}"
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            url, headers=_headers(), json={"message": {"key": message_key}, "convertToMp4": False}
        )
        r.raise_for_status()
        return base64.b64decode(r.json()["base64"])
