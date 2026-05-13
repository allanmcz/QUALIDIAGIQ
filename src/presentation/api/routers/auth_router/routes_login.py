"""POST /auth/login."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from . import deps, jwt_tokens
from .schemas import LoginRequest, LoginResponse

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """Login contra a tabela `admins`; token inclui tenant para RLS futuro."""
    settings_login = deps.get_settings()
    user: dict[str, Any] | None = None

    try:
        dsn_login = settings_login.sync_database_url
        if dsn_login:
            user = deps.buscar_admin_por_email_postgres(str(request.email), dsn_login)
        else:
            client = deps.get_supabase_client()
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
            deps.logger.error("admin_sem_hashed_password", email=request.email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Cadastro de administrador incompleto (senha não definida). Recrie o usuário.",
            )
        hash_norm = str(hash_bruto).strip()

        try:
            senha_ok = deps.pwd_context.verify(request.password, hash_norm)
        except ValueError as e:
            deps.logger.exception(
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
            deps.logger.error("admin_sem_tenant_id", email=request.email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Configuração de tenant ausente para este usuário",
            )

        try:
            tenant_id = UUID(str(raw_tid))
            user_id = UUID(str(user["id"]))
        except ValueError as e:
            deps.logger.exception("login_uuid_admin_invalido", erro=str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registro de administrador com identificador inválido no banco.",
            ) from e

        perfil_raw = user.get("perfil_conta") or "gratuito"
        perfil_login = str(perfil_raw).strip().lower()
        if perfil_login not in ("gratuito", "avancado", "admin"):
            perfil_login = "gratuito"

        access_token = jwt_tokens.create_access_token(
            subject_user_id=user_id,
            tenant_id=tenant_id,
            perfil_conta=perfil_login,
            expires_delta=timedelta(minutes=settings_login.jwt_expire_minutes),
        )
        nome_raw = user.get("nome")
        nome = str(nome_raw) if nome_raw is not None else None
        deps.logger.info(
            "auth_login_sucesso",
            tenant_id=str(tenant_id),
            user_id=str(user_id),
            perfil_conta=perfil_login,
        )
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            nome=nome,
            perfil_conta=perfil_login,
        )

    except HTTPException:
        raise
    except deps.psycopg2.Error as e:
        deps.logger.exception("login_postgres_erro", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Autenticação indisponível: não foi possível consultar o cadastro no PostgreSQL. "
                "Confira DATABASE_URL (host/porta; na API em Docker use «db», no host use localhost e a porta "
                "publicada, ex.: 60322) e se as migrações criaram a tabela `admins`."
            ),
        ) from e
    except deps.jwt.PyJWTError as e:
        deps.logger.exception("login_jwt_emit_erro", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao emitir o token de sessão. Confira JWT_SECRET_KEY e JWT_ALGORITHM no servidor.",
        ) from e
    except Exception as e:
        deps.logger.exception("login_falhou", tipo=type(e).__name__, erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Erro interno ao autenticar. Veja os logs da API (evento login_falhou). "
                "Se não usa DATABASE_URL, confira SUPABASE_URL/SUPABASE_ANON_KEY e conectividade."
            ),
        ) from e
