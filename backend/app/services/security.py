from datetime import UTC, datetime, timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.config import settings

_hasher = PasswordHasher()
# Hash fixo para igualar o tempo de resposta quando o login não existe.
DUMMY_HASH = _hasher.hash("senha-inexistente")


def hash_senha(senha: str) -> str:
    return _hasher.hash(senha)


def verificar_senha(senha_hash: str, senha: str) -> bool:
    try:
        return _hasher.verify(senha_hash, senha)
    except VerifyMismatchError:
        return False


def agora() -> datetime:
    return datetime.now(UTC)


def criar_token(login: str, emitido: datetime | None = None) -> str:
    emitido = emitido or agora()
    payload = {"sub": login, "iat": emitido, "exp": emitido + timedelta(minutes=settings.session_minutes)}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def ler_token(token: str) -> str | None:
    try:
        data = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except jwt.PyJWTError:
        return None
    return data.get("sub")
