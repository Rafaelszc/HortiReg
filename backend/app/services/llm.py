import logging
import time

from google import genai
from google.genai import errors, types

from app.config import settings
from app.schemas.pedido import PedidoExtraido

log = logging.getLogger("sgv.llm")

PROMPT = """Você interpreta pedidos e comandos de hortifrúti enviados por clientes via mensagem de texto ou áudio,
em português do Brasil, incluindo gírias e expressões regionais (ex: "meia dúzia", "um quilo e meio",
"dois maços", "uma caixa"). Extraia APENAS os itens realmente pedidos.
Normalize nomes para o singular e minúsculo. Se a quantidade for ambígua, use 1.
Use "kg" para quilo, quilos e kilo. A mensagem pode ser um áudio: ouça-o inteiro e extraia só o que foi dito.

Escolha o campo "acao" conforme a intenção do cliente:
- "adicionar" (padrão): cliente está fazendo um pedido novo ou acrescentando itens ao pedido atual.
- "substituir": cliente pede para cancelar/descartar o pedido atual e fazer outro com novos itens
  (ex: "cancela esse e faz outro com 2 kg de batata", "esquece o anterior, quero só 1 caixa de banana").
- "remover": cliente pede apenas para retirar itens do pedido atual (ex: "tira a banana"); coloque os nomes
  em "itens_remover".
- "confirmar": cliente confirma o pedido (ex: "pode confirmar", "tá certo", "fechado").
- "cancelar": cliente cancela o pedido sem pedir novos itens (ex: "cancela tudo", "não quero mais").

Se o cliente pedir para tirar um item E adicionar outro na mesma mensagem (ex: "tira a banana e bota 1 kg de cebola"),
use acao="adicionar", coloque "banana" em "itens_remover" e a cebola em "itens".
Se a mensagem não for um pedido nem um comando, ou o áudio estiver inaudível ou ininteligível, devolva acao="adicionar"
e listas vazias. Nunca invente produtos.
A mensagem pode trazer o endereço de entrega, sozinho ou junto do pedido. Nesse caso preencha "endereco"
separando rua, numero, bairro e cidade, só com o que o cliente disse; nunca complete nem adivinhe. Preencha
"rua" apenas com nome de rua, avenida ou travessa. "numero" é o número da casa, nunca a quantidade de um
produto; use "s/n" se o cliente disser que não tem. Sem endereço na mensagem, "endereco" fica vazio.
Não repita o endereço na observação."""

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
