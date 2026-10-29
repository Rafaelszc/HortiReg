from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models import Admin
from app.services import security

router = APIRouter(prefix="/auth", tags=["auth"])
_bearer = HTTPBearer(auto_error=False)

MSG_INVALIDO = "Login ou senha inválidos."
MSG_BLOQUEADO = "Acesso temporariamente bloqueado. Tente novamente mais tarde."


class LoginIn(BaseModel):
    login: str
    senha: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeOut(BaseModel):
    login: str


@router.post("/login", response_model=TokenOut)
async def login(dados: LoginIn, session: AsyncSession = Depends(get_session)) -> TokenOut:
    admin = await session.scalar(select(Admin).where(Admin.login == dados.login))
    agora = security.agora()

    if admin and admin.bloqueado_ate and admin.bloqueado_ate > agora:
        raise HTTPException(status.HTTP_423_LOCKED, MSG_BLOQUEADO)

    senha_ok = security.verificar_senha(admin.senha_hash if admin else security.DUMMY_HASH, dados.senha)
    if not (admin and senha_ok):
        if admin:
            admin.tentativas_falhas += 1
            if admin.tentativas_falhas >= settings.lockout_attempts:
                admin.bloqueado_ate = agora + timedelta(minutes=settings.lockout_minutes)
                admin.tentativas_falhas = 0
            await session.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, MSG_INVALIDO)

    admin.tentativas_falhas = 0
    admin.bloqueado_ate = None
    await session.commit()
    return TokenOut(access_token=security.criar_token(admin.login, agora))


async def get_current_admin(
    cred: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: AsyncSession = Depends(get_session),
) -> Admin:
    login_ = security.ler_token(cred.credentials) if cred else None
    admin = await session.scalar(select(Admin).where(Admin.login == login_)) if login_ else None
    if not admin:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Sessão inválida ou expirada.")
    return admin


@router.get("/me", response_model=MeOut)
async def me(admin: Admin = Depends(get_current_admin)) -> MeOut:
    return MeOut(login=admin.login)
