"""Recebe os eventos da Evolution API (mensagens do WhatsApp)."""

import asyncio
import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import SessionLocal
from app.models import Cliente, ItemPedido, Pedido, RascunhoEndereco, StatusPedido
from app.schemas.pedido import EnderecoExtraido, PedidoExtraido
from app.services import audio, catalogo, endereco, expiracao, fila, llm, whatsapp
from app.services.webhook_auth import exigir_token

router = APIRouter(prefix="/webhook", tags=["webhook"])
log = logging.getLogger("sgv.webhook")

# Resposta ao resumo do pedido (US-08): 1-Confirmar, 2-Corrigir, 3-Cancelar
OPCOES = {
    **dict.fromkeys(("1", "sim", "s", "confirmo", "confirmar", "ok", "isso"), "confirmar"),
    **dict.fromkeys(("2", "corrigir"), "corrigir"),
    **dict.fromkeys(("3", "nao", "não", "n", "cancelar", "cancela"), "cancelar"),
}
MSG_OPCOES = "Responda *1* para confirmar, *2* para corrigir ou *3* para cancelar."
MSG_JA_EXPIROU = (
    "O pedido #{id} expirou e não pode mais ser confirmado. "
    "Quer refazer? É só mandar o pedido de novo, por texto ou áudio."
)
EXEMPLO = 'Exemplo: "quero 2 kg de tomate e 1 caixa de banana".'
MSG_SEM_ITENS = f"Não consegui entender os itens do pedido. Pode repetir? 🙏\n{EXEMPLO}"
MSG_AUDIO_LONGO = (
    "Seu áudio ficou longo demais (o limite é de {limite} segundos). "
    "Pode mandar um áudio mais curto ou escrever o pedido em texto? 🙏\n" + EXEMPLO
)
MSG_AUDIO_FORMATO = (
    "Não consegui abrir esse tipo de áudio. "
    "Pode gravar uma mensagem de voz pelo WhatsApp ou escrever o pedido em texto? 🙏\n" + EXEMPLO
)
MSG_AUDIO_INCOMPREENDIDO = (
    "Não consegui entender seu áudio. "
    "Pode gravar de novo, mais curto e perto do celular, ou escrever o pedido em texto? 🙏\n" + EXEMPLO
)
MSG_IA_FALHA = (
    "Não consegui processar seu pedido agora. Pode mandar de novo daqui a pouco? 🙏\n" + EXEMPLO
)
MSG_AUDIO_FALHA = (
    "Não consegui ouvir seu áudio agora. Pode mandar de novo daqui a pouco ou escrever o pedido em texto? 🙏\n"
    + EXEMPLO
)
MSG_IA_FALHA_ENDERECO = (
    "Não consegui ler sua mensagem agora. Pode mandar de novo daqui a pouco? 🙏\n"
    "Se for o endereço, mande assim: " + endereco.EXEMPLO.removeprefix("Exemplo: ")
)


@router.post("/whatsapp", dependencies=[Depends(exigir_token)])
async def receber(payload: dict, background: BackgroundTasks):
    """Responde 200 imediatamente e processa a mensagem em segundo plano."""
    if payload.get("event", "").lower().replace("_", ".") != "messages.upsert":
        return {"ignored": True}
    data = payload.get("data", {})
    key = data.get("key", {})
    jid = key.get("remoteJid", "")
    if key.get("fromMe") or not jid.endswith("@s.whatsapp.net"):
        return {"ignored": True}  # ignora mensagens do próprio bot, grupos e status

    # Grava antes de processar (RK-03): se a IA cair, a mensagem não se perde. Reenvio do mesmo id é ignorado.
    mensagem_id = await fila.registrar(jid.split("@")[0], data)
    if mensagem_id is None:
        log.info("Mensagem %s já recebida; ignorada", key.get("id"))
        return {"received": True}
    background.add_task(fila.processar, mensagem_id, processar_mensagem)
    return {"received": True}


async def processar_mensagem(data: dict) -> None:
    """Interpreta uma mensagem já gravada. Falha da IA levanta FalhaTransitoria para a fila tentar de novo."""
    try:
        key = data.get("key", {})
        telefone = key.get("remoteJid", "").split("@")[0]

        msg = data.get("message", {}) or {}
        texto = msg.get("conversation") or msg.get("extendedTextMessage", {}).get("text")
        eh_audio = "audioMessage" in msg

        async with SessionLocal() as session:
            cliente = await _obter_cliente(session, telefone, data.get("pushName"))

            # Etapa 2: com pedido pendente, valem as opções 1, 2 e 3 ou o endereço; nada vira pedido novo
            await expiracao.expirar_pendentes(session)  # pendente vencido não pode ser confirmado
            pendente = await _pedido_pendente(session, cliente)
            rascunho = await session.get(RascunhoEndereco, cliente.id)

            # Quando só falta o número, "2" é o número da casa, e não "corrigir" (US-11)
            if texto and rascunho and endereco.falta(rascunho) == ["número"]:
                if numero := endereco.numero_avulso(texto):
                    await _receber_endereco(session, cliente, pendente, EnderecoExtraido(numero=numero))
                    return

            opcao = OPCOES.get(texto.strip().lower()) if texto else None
            if opcao:
                await _tratar_resposta(session, cliente, pendente, opcao)
                return

            # Etapa 1: interpretar a mensagem (pedido, endereço ou os dois)
            esperando_endereco = pendente is not None or rascunho is not None
            msg_sem_itens = MSG_SEM_ITENS
            if eh_audio:
                extraido = await _extrair_do_audio(telefone, key, msg["audioMessage"])
                if extraido is None:
                    return  # o cliente já foi avisado
                msg_sem_itens = MSG_AUDIO_INCOMPREENDIDO
            elif texto:
                falha = MSG_IA_FALHA_ENDERECO if esperando_endereco else MSG_IA_FALHA
                extraido = await _extrair_do_texto(key, texto, falha)
            else:
                if pendente:
                    await _tratar_resposta(session, cliente, pendente, None)
                return

            novo = endereco.limpar(extraido.endereco, None if eh_audio else texto)
            trouxe_endereco = endereco.informa(novo, rascunho)

            if pendente:
                if trouxe_endereco:
                    await _receber_endereco(session, cliente, pendente, novo)
                else:
                    await _tratar_resposta(session, cliente, pendente, None)
                return

            if not extraido.itens:
                if trouxe_endereco:
                    await _receber_endereco(session, cliente, None, novo)
                else:
                    await whatsapp.enviar_texto(telefone, msg_sem_itens)
                return

            if trouxe_endereco:
                await endereco.aplicar(session, cliente, novo)
            else:
                await endereco.descartar_troca(session, cliente)

            pedido = Pedido(
                cliente_id=cliente.id,
                observacao=extraido.observacao,
                itens=await catalogo.montar_itens(session, extraido.itens),
            )
            session.add(pedido)
            await session.commit()

            await whatsapp.enviar_texto(
                telefone,
                f"Entendi seu pedido #{pedido.id}:\n{_resumo(pedido.itens)}\n\n"
                + await _proximo_passo(session, cliente, pedido),
            )
    except fila.FalhaTransitoria:
        raise
    except Exception:
        log.exception("Erro ao processar mensagem do WhatsApp")


async def _extrair_do_texto(key: dict, texto: str, msg_falha: str) -> PedidoExtraido:
    """Interpreta o texto. Se a IA falhar ou demorar, a fila tenta de novo (RK-03: a mensagem nunca se perde)."""
    try:
        return await asyncio.wait_for(
            llm.extrair_pedido(texto=texto),
            timeout=settings.ia_texto_timeout_segundos,
        )
    except Exception as erro:
        log.exception("Falha ao interpretar o texto da mensagem %s", key.get("id"))
        raise fila.FalhaTransitoria(msg_falha) from erro


async def _extrair_do_audio(telefone: str, key: dict, msg_audio: dict) -> PedidoExtraido | None:
    """Valida, baixa e interpreta o áudio. Recusa definitiva avisa e devolve None; falha técnica vai para a fila."""
    rejeicao = audio.validar(msg_audio)
    if rejeicao is audio.Rejeicao.FORMATO:
        await whatsapp.enviar_texto(telefone, MSG_AUDIO_FORMATO)
        return None
    if rejeicao is audio.Rejeicao.LONGO:
        await whatsapp.enviar_texto(telefone, MSG_AUDIO_LONGO.format(limite=settings.audio_max_segundos))
        return None

    try:
        dados = await whatsapp.baixar_audio(key)
        if audio.tamanho_valido(dados):
            return await asyncio.wait_for(
                llm.extrair_pedido(audio=dados, audio_mime=audio.mime_gemini(msg_audio.get("mimetype"))),
                timeout=settings.audio_timeout_segundos,
            )
    except Exception as erro:
        log.exception("Falha ao interpretar o áudio da mensagem %s", key.get("id"))
        raise fila.FalhaTransitoria(MSG_AUDIO_FALHA) from erro

    await whatsapp.enviar_texto(telefone, MSG_AUDIO_LONGO.format(limite=settings.audio_max_segundos))
    return None


def _resumo(itens: list[ItemPedido]) -> str:
    """Itens com preço do catálogo e valor estimado; itens fora do catálogo ficam a confirmar."""
    linhas = []
    for i in itens:
        sub = catalogo.subtotal(i)
        preco = f" — {catalogo.brl(sub)}" if sub is not None else " — preço a confirmar"
        linhas.append(f"• {float(i.quantidade):g} {i.unidade} de {i.nome}{preco}")
    if any(i.preco_unitario is not None for i in itens):
        linhas.append(f"\nValor estimado: {catalogo.brl(catalogo.total_estimado(itens))}")
    return "\n".join(linhas)


async def _obter_cliente(session: AsyncSession, telefone: str, nome: str | None) -> Cliente:
    cliente = await session.scalar(select(Cliente).where(Cliente.telefone == telefone))
    if cliente is None:
        cliente = Cliente(telefone=telefone, nome=nome)
        session.add(cliente)
        await session.commit()
    return cliente


async def _pedido_pendente(session: AsyncSession, cliente: Cliente) -> Pedido | None:
    """Pedido do próprio número aguardando confirmação (outro número nunca o altera)."""
    return await session.scalar(
        select(Pedido)
        .where(
            Pedido.cliente_id == cliente.id,
            Pedido.status == StatusPedido.AGUARDANDO_CONFIRMACAO,
        )
        .order_by(Pedido.id.desc())
    )


async def _proximo_passo(session: AsyncSession, cliente: Cliente, pedido: Pedido | None) -> str:
    """O que o cliente precisa fazer: completar o endereço ou, com ele completo, responder 1, 2 ou 3."""
    rascunho = await session.get(RascunhoEndereco, cliente.id)
    if rascunho or not cliente.endereco:
        return endereco.pedir(rascunho, com_pedido=pedido is not None)
    return f"Entrega em: {cliente.endereco}\nSe mudou, é só mandar o novo endereço.\n\n{MSG_OPCOES}"


async def _receber_endereco(
    session: AsyncSession, cliente: Cliente, pedido: Pedido | None, novo: EnderecoExtraido
) -> None:
    await endereco.aplicar(session, cliente, novo)
    completo = await session.get(RascunhoEndereco, cliente.id) is None
    if pedido is not None:
        texto = await _proximo_passo(session, cliente, pedido)
        if completo:
            texto = f"✅ Endereço salvo para o pedido #{pedido.id}.\n{texto}"
    elif completo:
        texto = (
            f"✅ Endereço salvo: {cliente.endereco}\nVou usar nos próximos pedidos. "
            "Se algo estiver errado, mande o endereço de novo."
        )
    else:
        texto = await _proximo_passo(session, cliente, None)
    await whatsapp.enviar_texto(cliente.telefone, texto)


async def _tratar_resposta(session: AsyncSession, cliente: Cliente, pedido: Pedido | None, opcao: str | None) -> None:
    if pedido is None:
        ultimo = await session.scalar(
            select(Pedido).where(Pedido.cliente_id == cliente.id).order_by(Pedido.id.desc())
        )
        if opcao == "confirmar" and ultimo is not None and ultimo.status == StatusPedido.EXPIRADO:
            await whatsapp.enviar_texto(cliente.telefone, MSG_JA_EXPIROU.format(id=ultimo.id))
            return
        # id interno no log, não o telefone (sem dados pessoais nos logs)
        log.warning("Cliente %s respondeu '%s' sem pedido aguardando confirmação", cliente.id, opcao)
        await whatsapp.enviar_texto(cliente.telefone, "Você não tem nenhum pedido aguardando confirmação.")
        return
    sem_endereco = not cliente.endereco or await session.get(RascunhoEndereco, cliente.id) is not None
    if opcao is None or (opcao == "confirmar" and sem_endereco):
        inicio = (
            f"Ainda não posso confirmar o pedido #{pedido.id}."
            if opcao
            else f"Não entendi sua resposta sobre o pedido #{pedido.id}."
        )
        instrucao = await _proximo_passo(session, cliente, pedido) if sem_endereco else MSG_OPCOES
        await whatsapp.enviar_texto(cliente.telefone, f"{inicio} {instrucao}")
        return

    pedido.status = StatusPedido.CONFIRMADO if opcao == "confirmar" else StatusPedido.CANCELADO
    await session.commit()
    if pedido.status == StatusPedido.CANCELADO:
        await endereco.descartar_troca(session, cliente)
    resposta = {
        "confirmar": f"✅ Pedido #{pedido.id} confirmado! Avisaremos quando sair para entrega.",
        # shortcut: corrigir = cancelar e pedir de novo; a edição item a item é a US-09
        "corrigir": f"✏️ Pedido #{pedido.id} cancelado para correção. Envie o pedido completo do jeito certo.",
        "cancelar": f"❌ Pedido #{pedido.id} cancelado.",
    }[opcao]
    await whatsapp.enviar_texto(cliente.telefone, resposta)
