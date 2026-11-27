import logging
import time

from google import genai
from google.genai import errors, types

from app.config import settings
from app.schemas.pedido import PedidoExtraido

log = logging.getLogger("sgv.llm")

PROMPT = """Você interpreta pedidos de hortifrúti enviados por clientes no WhatsApp, em português
do Brasil, incluindo gírias e expressões regionais (ex: "meia dúzia", "um quilo e meio",
"dois maços", "uma caixa"). Extraia APENAS os itens realmente pedidos.
Normalize nomes para o singular e minúsculo. Se a quantidade for ambígua, use 1.
Use "kg" para quilo, quilos e kilo. A mensagem pode ser um áudio: ouça-o inteiro e extraia só o que foi dito.
Se a mensagem não for um pedido, ou o áudio estiver inaudível ou ininteligível, devolva a lista de itens
vazia. Nunca invente produtos."""

_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


async def extrair_pedido(
    texto: str | None = None,
    audio: bytes | None = None,
    audio_mime: str = "audio/ogg",
) -> PedidoExtraido:
    """Converte texto OU áudio em um PedidoExtraido (JSON validado pelo Pydantic)."""
    partes: list = [PROMPT]
    if texto:
        partes.append(f"Mensagem do cliente: {texto}")
    if audio:
        partes.append(types.Part.from_bytes(data=audio, mime_type=audio_mime))

    modelos = [settings.gemini_model]
    if settings.gemini_fallback_model and settings.gemini_fallback_model != settings.gemini_model:
        modelos.append(settings.gemini_fallback_model)

    ultimo_erro: Exception | None = None
    for idx, modelo in enumerate(modelos):
        inicio = time.perf_counter()
        try:
            resposta = await _get_client().aio.models.generate_content(
                model=modelo,
                contents=partes,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=PedidoExtraido,
                    temperature=0,
                ),
            )
            duracao_ms = (time.perf_counter() - inicio) * 1000
            log.info("Gemini (%s) respondeu em %.0fms", modelo, duracao_ms)
            return resposta.parsed or PedidoExtraido()
        except errors.APIError as exc:
            duracao_ms = (time.perf_counter() - inicio) * 1000
            ultimo_erro = exc
            tem_fallback = idx + 1 < len(modelos)
            log.warning(
                "Gemini (%s) falhou em %.0fms (status=%s)%s",
                modelo,
                duracao_ms,
                exc.code,
                f"; tentando fallback {modelos[idx + 1]}" if tem_fallback else "",
            )
            if not tem_fallback:
                raise
    raise ultimo_erro  # pragma: no cover
