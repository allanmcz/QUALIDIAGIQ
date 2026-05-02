"""
Rotas de autenticação B2B.

Camada: Presentation
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, cast
from uuid import UUID, uuid4

import jwt
import psycopg2
import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field

from src.application.ports.email_service import EmailServicePort  # noqa: TC001
from src.infrastructure.auth.postgres_admin_login import buscar_admin_por_email_postgres
from src.infrastructure.config.settings import get_settings
from src.infrastructure.email_verificacao import codigo_store
from src.presentation.api.dependencies import (
    SELF_SERVICE_DIAGNOSTICO_SCOPE,
    get_email_service,
    get_supabase_client,
)

logger = structlog.get_logger(__name__)

_VALIDADE_MINUTOS_CODIGO = 10

router = APIRouter(prefix="/auth", tags=["Autenticação B2B"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    nome: str | None


class SolicitarVerificacaoEmailRequest(BaseModel):
    """Wizard passo 1 — confirmação de posse do inbox (LGPD)."""

    email: EmailStr


class SolicitarVerificacaoEmailResponse(BaseModel):
    mensagem: str


class ConfirmarVerificacaoEmailRequest(BaseModel):
    email: EmailStr
    codigo: str = Field(min_length=4, max_length=8, description="Código recebido por e-mail")


class ConfirmarVerificacaoEmailResponse(BaseModel):
    verificado: bool


class SelfServiceTokenRequest(BaseModel):
    """Troca código OTP (mesmo fluxo de /verificar-email/solicitar) por JWT para POST /diagnosticos/self-service."""

    email: EmailStr
    codigo: str = Field(
        min_length=4, max_length=8, description="Código numérico recebido por e-mail"
    )


class SelfServiceTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def create_access_token(
    *,
    subject_user_id: UUID,
    tenant_id: UUID,
    expires_delta: timedelta | None = None,
) -> str:
    """Gera JWT com `sub` (id do admin) e claim `tenant_id`."""
    settings = get_settings()
    expire = datetime.now(UTC) + (
        expires_delta if expires_delta is not None else timedelta(minutes=15)
    )
    payload: dict[str, Any] = {
        "sub": str(subject_user_id),
        "tenant_id": str(tenant_id),
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_self_service_access_token(*, email_norm: str) -> tuple[str, int]:
    """JWT de curta duração para gravar um diagnóstico no tenant self-service após OTP."""
    settings = get_settings()
    minutes = settings.self_service_jwt_expire_minutes
    expire = datetime.now(UTC) + timedelta(minutes=minutes)
    payload_jwt: dict[str, Any] = {
        "sub": str(uuid4()),
        "tenant_id": str(settings.self_service_tenant_id),
        "email": email_norm,
        "scope": SELF_SERVICE_DIAGNOSTICO_SCOPE,
        "exp": expire,
    }
    token = jwt.encode(payload_jwt, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, int(minutes * 60)


@router.post(
    "/self-service/token",
    response_model=SelfServiceTokenResponse,
    summary="OTP → JWT self-service (gravar diagnóstico)",
    description=(
        "Consumir o código enviado por POST /auth/verificar-email/solicitar e receber um Bearer JWT "
        "válido para POST /diagnosticos/self-service (Idempotency-Key obrigatório). "
        "O e-mail do diagnóstico deve ser o mesmo verificado."
    ),
)
async def emitir_token_self_service(body: SelfServiceTokenRequest) -> SelfServiceTokenResponse:
    email_norm = codigo_store.normalizar_email(str(body.email))
    codigo_limpo = body.codigo.strip().replace(" ", "")
    if not codigo_limpo.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código deve conter apenas números.",
        )
    if not codigo_store.validar_e_consumir(email_norm, codigo_limpo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido ou expirado. Solicite um novo código.",
        )
    token, ttl_sec = create_self_service_access_token(email_norm=email_norm)
    return SelfServiceTokenResponse(access_token=token, expires_in=ttl_sec)


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """Login contra a tabela `admins`; token inclui tenant para RLS futuro."""
    settings_login = get_settings()
    user: dict[str, Any] | None = None

    try:
        dsn_login = settings_login.sync_database_url
        # Com DATABASE_URL (Compose, CI, etc.) a tabela `admins` está no Postgres — evita REST Supabase em :54321 inexistente no container.
        if dsn_login:
            user = buscar_admin_por_email_postgres(str(request.email), dsn_login)
        else:
            client = get_supabase_client()
            response = client.table("admins").select("*").eq("email", str(request.email)).execute()
            users = response.data
            if users:
                user = cast("dict[str, Any]", users[0])

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-mail ou senha incorretos",
            )

        hash_bruto = user.get("hashed_password")
        if hash_bruto is None or str(hash_bruto).strip() == "":
            logger.error("admin_sem_hashed_password", email=request.email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cadastro de administrador incompleto (senha não definida). Recrie o usuário.",
            )
        hash_norm = str(hash_bruto).strip()

        try:
            senha_ok = pwd_context.verify(request.password, hash_norm)
        except ValueError as e:
            logger.exception(
                "login_hash_bcrypt_invalido",
                email=request.email,
                erro=str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Hash de senha do administrador é inválido ou incompatível com o bcrypt atual. "
                    "Gere nova senha com: python -m src.scripts.criar_admin (ou atualize o registro em `admins`)."
                ),
            ) from e

        if not senha_ok:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="E-mail ou senha incorretos",
            )

        raw_tid = user.get("tenant_id")
        if raw_tid is None:
            logger.error("admin_sem_tenant_id", email=request.email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Configuração de tenant ausente para este usuário",
            )

        try:
            tenant_id = UUID(str(raw_tid))
            user_id = UUID(str(user["id"]))
        except ValueError as e:
            logger.exception("login_uuid_admin_invalido", erro=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registro de administrador com identificador inválido no banco.",
            ) from e

        access_token = create_access_token(
            subject_user_id=user_id,
            tenant_id=tenant_id,
            expires_delta=timedelta(minutes=settings_login.jwt_expire_minutes),
        )
        nome_raw = user.get("nome")
        nome = str(nome_raw) if nome_raw is not None else None
        return LoginResponse(access_token=access_token, token_type="bearer", nome=nome)

    except HTTPException:
        raise
    except psycopg2.Error as e:
        logger.exception("login_postgres_erro", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Autenticação indisponível: não foi possível consultar o cadastro no PostgreSQL. "
                "Confira DATABASE_URL (host/porta; na API em Docker use «db», no host use localhost e a porta "
                "publicada, ex.: 60322) e se as migrações criaram a tabela `admins`."
            ),
        ) from e
    except jwt.PyJWTError as e:
        logger.exception("login_jwt_emit_erro", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao emitir o token de sessão. Confira JWT_SECRET_KEY e JWT_ALGORITHM no servidor.",
        ) from e
    except Exception as e:
        logger.exception("login_falhou", tipo=type(e).__name__, erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Erro interno ao autenticar. Veja os logs da API (evento login_falhou). "
                "Se não usa DATABASE_URL, confira SUPABASE_URL/SUPABASE_ANON_KEY e conectividade."
            ),
        ) from e


@router.post(
    "/verificar-email/solicitar",
    response_model=SolicitarVerificacaoEmailResponse,
    summary="Solicitar código por e-mail",
    description=(
        "Envia OTP numérico para o endereço informado (SMTP configurável). "
        "Rate limit por e-mail entre reenvios. MVP: armazenamento em memória no processo da API."
    ),
)
async def solicitar_verificacao_email(
    body: SolicitarVerificacaoEmailRequest,
    email_service: Annotated[EmailServicePort, Depends(get_email_service)],
) -> SolicitarVerificacaoEmailResponse:
    settings = get_settings()
    email_norm = codigo_store.normalizar_email(str(body.email))
    if not codigo_store.pode_reenviar(email_norm):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Aguarde alguns segundos antes de pedir novo código.",
        )
    codigo = f"{secrets.randbelow(1_000_000):06d}"
    ok = await email_service.enviar_codigo_verificacao_email(
        email_norm, codigo, _VALIDADE_MINUTOS_CODIGO
    )
    if settings.app_env == "development":
        logger.info(
            "email_verificacao_codigo_dev",
            email=email_norm,
            codigo=codigo,
            smtp_ok=ok,
        )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Não foi possível enviar o e-mail. Se a API roda no Docker: confira se o serviço "
                "mailpit está no ar (make dev) e SMTP_HOST=mailpit. No host: Mailpit em "
                "127.0.0.1:1025 e SMTP_HOST=127.0.0.1. Mensagens de dev: http://127.0.0.1:8025 ."
            ),
        )
    codigo_store.registrar_envio(email_norm, codigo)
    return SolicitarVerificacaoEmailResponse(
        mensagem=f"Código enviado. Válido por {_VALIDADE_MINUTOS_CODIGO} minutos.",
    )


@router.post(
    "/verificar-email/confirmar",
    response_model=ConfirmarVerificacaoEmailResponse,
    summary="Confirmar código do e-mail",
)
async def confirmar_verificacao_email(
    body: ConfirmarVerificacaoEmailRequest,
) -> ConfirmarVerificacaoEmailResponse:
    email_norm = codigo_store.normalizar_email(str(body.email))
    codigo_limpo = body.codigo.strip().replace(" ", "")
    if not codigo_limpo.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código deve conter apenas números.",
        )
    if codigo_store.validar_e_consumir(email_norm, codigo_limpo):
        return ConfirmarVerificacaoEmailResponse(verificado=True)
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Código inválido ou expirado. Solicite um novo código.",
    )
