"""Endereço de entrega do cliente (US-11).

`Cliente.endereco` guarda só endereço completo (rua e número). O que chega em partes fica em `RascunhoEndereco`
até completar. LGPD: nada daqui vai para o log.
"""

import re

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Cliente, RascunhoEndereco
from app.schemas.pedido import EnderecoExtraido
from app.services.catalogo import normalizar

# A soma, com os separadores, cabe em Cliente.endereco (255)
LIMITES = {"rua": 120, "numero": 20, "bairro": 60, "cidade": 40}
SEM_NUMERO = "s/n"
_SEM_NUMERO = r"s\s*/\s*n|sem\s+n[uú]mero"
# Resposta que é só o número da casa: "120", "nº 45", "120A", "s/n"
_NUMERO_AVULSO = re.compile(
    rf"(?:(?:n[ºo°.]{{1,2}}|n[uú]mero)\s*)?(?P<numero>\d{{1,5}}(?:-?[a-z])?)|(?P<sem>{_SEM_NUMERO})",
    re.IGNORECASE,
)

EXEMPLO = 'Exemplo: "Rua das Flores, 120, Catolé, Campina Grande".'


def numero_avulso(texto: str) -> str | None:
    achado = _NUMERO_AVULSO.fullmatch(texto.strip().rstrip("."))
    if achado is None:
        return None
    return SEM_NUMERO if achado["sem"] else achado["numero"]


def _numero_valido(numero: str, texto: str | None) -> str | None:
    """O sistema nunca adivinha: em mensagem de texto, o número precisa ter sido escrito pelo cliente."""
    if re.fullmatch(_SEM_NUMERO, numero, re.IGNORECASE):
        return SEM_NUMERO if texto is None or re.search(_SEM_NUMERO, texto, re.IGNORECASE) else None
    digitos = re.search(r"\d+", numero)
    if digitos is None:
        return None
    if texto is not None and not re.search(rf"(?<!\d){digitos[0]}(?!\d)", texto):
        return None
    return numero


def limpar(extraido: EnderecoExtraido | None, texto: str | None) -> EnderecoExtraido:
    """Normaliza o que a IA devolveu. `texto` é None no áudio (não há como conferir o número)."""
    campos = {}
    for campo, limite in LIMITES.items():
        valor = " ".join((getattr(extraido, campo, None) or "").split()).strip(" ,;")
        campos[campo] = valor[:limite] or None
    if campos["numero"]:
        campos["numero"] = _numero_valido(campos["numero"], texto)
    return EnderecoExtraido(**campos)


def informa(novo: EnderecoExtraido, rascunho: RascunhoEndereco | None) -> bool:
    """A mensagem traz endereço? Bairro ou cidade soltos só valem para completar um rascunho."""
    if novo.rua or novo.numero:
        return True
    return rascunho is not None and bool(novo.bairro or novo.cidade)


def falta(rascunho: RascunhoEndereco | None) -> list[str]:
    campos = {"rua": "rua", "numero": "número"}
    return [nome for campo, nome in campos.items() if not getattr(rascunho, campo, None)]


def formatar(rascunho: RascunhoEndereco) -> str:
    return ", ".join(v for campo in LIMITES if (v := getattr(rascunho, campo)))


async def aplicar(session: AsyncSession, cliente: Cliente, novo: EnderecoExtraido) -> None:
    """Junta os dados novos ao rascunho; completo, vira o endereço salvo do cliente."""
    rascunho = await session.get(RascunhoEndereco, cliente.id)
    if rascunho is None:
        rascunho = RascunhoEndereco(cliente_id=cliente.id)
        session.add(rascunho)
    elif novo.rua and rascunho.rua and normalizar(novo.rua) != normalizar(rascunho.rua):
        for campo in LIMITES:  # outra rua é outro endereço: não herda número nem bairro
            setattr(rascunho, campo, None)
    for campo in LIMITES:
        if valor := getattr(novo, campo):
            setattr(rascunho, campo, valor)

    if not falta(rascunho):
        cliente.endereco = formatar(rascunho)
        await session.flush()
        await session.delete(rascunho)
    await session.commit()


async def descartar_troca(session: AsyncSession, cliente: Cliente) -> None:
    """Abandona uma troca incompleta de quem já tem endereço salvo."""
    if cliente.endereco and (rascunho := await session.get(RascunhoEndereco, cliente.id)):
        await session.delete(rascunho)
        await session.commit()


def pedir(rascunho: RascunhoEndereco | None, com_pedido: bool) -> str:
    """Pede só o que falta, em linguagem simples e com exemplo (DA-USAB-I3-03)."""
    pendencias = falta(rascunho)
    if pendencias == ["número"]:
        # aqui "2" e "3" são número de casa: o cancelamento é só pela palavra
        texto = f'Falta o número da casa. Responda só com o número (ou "{SEM_NUMERO}" se não tiver).'
        cancelar = "Para cancelar o pedido, escreva *cancelar*."
    else:
        if pendencias == ["rua"]:
            texto = f"Falta o nome da rua. {EXEMPLO}"
        else:
            texto = f"Me diga o endereço de entrega, com rua e número. {EXEMPLO}"
        cancelar = "Para cancelar o pedido, responda *3*."
    return f"{texto}\n{cancelar}" if com_pedido else texto
