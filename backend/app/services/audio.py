"""Regras para os áudios de pedido (US-06). Só decide se o áudio serve; quem responde ao cliente é o webhook."""

from enum import Enum

from app.config import settings

# Formatos que o Gemini lê, indexados pelo tipo base do WhatsApp (sem "; codecs=...").
# A nota de voz do WhatsApp chega como "audio/ogg; codecs=opus".
FORMATOS_GEMINI = {
    "audio/ogg": "audio/ogg",
    "audio/mpeg": "audio/mp3",
    "audio/mp3": "audio/mp3",
    "audio/aac": "audio/aac",
    "audio/wav": "audio/wav",
    "audio/x-wav": "audio/wav",
}
FORMATO_PADRAO = "audio/ogg"  # nota de voz, quando o evento não informa o tipo


class Rejeicao(str, Enum):
    LONGO = "longo"
    FORMATO = "formato"


def tipo_base(mimetype: str | None) -> str:
    """'Audio/OGG; codecs=opus' -> 'audio/ogg'. Vazio vira o formato padrão."""
    base = (mimetype or "").split(";")[0].strip().lower()
    return base or FORMATO_PADRAO


def mime_gemini(mimetype: str | None) -> str | None:
    return FORMATOS_GEMINI.get(tipo_base(mimetype))


def _segundos(audio: dict) -> int:
    try:
        return int(float(audio.get("seconds") or 0))
    except (TypeError, ValueError):
        return 0


def validar(audio: dict) -> Rejeicao | None:
    """Confere formato e duração do audioMessage do evento, antes de baixar o arquivo."""
    if mime_gemini(audio.get("mimetype")) is None:
        return Rejeicao.FORMATO
    if _segundos(audio) > settings.audio_max_segundos:
        return Rejeicao.LONGO
    return None


def tamanho_valido(dados: bytes) -> bool:
    """Defesa extra: o evento pode não trazer a duração, mas o arquivo baixado tem tamanho."""
    return len(dados) <= settings.audio_max_bytes
