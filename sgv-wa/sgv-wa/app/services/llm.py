from google import genai
from google.genai import types

from app.config import settings
from app.schemas.pedido import PedidoExtraido

PROMPT = """Você interpreta pedidos de hortifrúti enviados por clientes no WhatsApp, em português
do Brasil, incluindo gírias e expressões regionais (ex: "meia dúzia", "um quilo e meio",
"dois maços", "uma caixa"). Extraia APENAS os itens realmente pedidos.
Normalize nomes para o singular e minúsculo. Se a quantidade for ambígua, use 1.
Se a mensagem não for um pedido, devolva a lista de itens vazia."""

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

    resposta = await _get_client().aio.models.generate_content(
        model=settings.gemini_model,
        contents=partes,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PedidoExtraido,
            temperature=0,
        ),
    )
    return resposta.parsed or PedidoExtraido()
