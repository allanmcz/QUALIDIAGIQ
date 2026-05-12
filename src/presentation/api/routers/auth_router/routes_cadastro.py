"""POST /auth/cadastro."""

from __future__ import annotations

from datetime import timedelta
from typing import Any, cast
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, status

from src.domain.value_objects.email import normalizar_email

from . import deps, jwt_tokens
from .schemas import CadastroConsultorB2BRequest, LoginResponse

router = APIRouter()


@router.post(
    "/cadastro",
    response_model=LoginResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar conta na plataforma (nome, e-mail, senha)",
    description=(
        "Cria registro em `admins` com tenant dedicado e `perfil_conta` gratuito; devolve o mesmo "
        "contrato de `POST /auth/login` (JWT). Requer PostgreSQL acessível como em login (`DATABASE_URL`) "
        "ou Supabase configurado. Desabilite em produção com `QDI_CADASTRO_CONSULTOR_B2B_HABILITADO=false`."
    ),
)
async def cadastro_consultor_b2b(body: CadastroConsultorB2BRequest) -> LoginResponse:
    """Cadastro público MVP — mesma base de credenciais do login na plataforma."""
    settings_cad = deps.get_settings()
    if not settings_cad.cadastro_consultor_b2b_habilitado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cadastro na plataforma está desabilitado neste ambiente (QDI_CADASTRO_CONSULTOR_B2B_HABILITADO).",
        )

    email_norm = normalizar_email(str(body.email))
    nome_limpo = body.nome.strip()
    hashed = deps.pwd_context.hash(body.password)
    tenant_novo = uuid4()

    try:
        dsn_cad = settings_cad.sync_database_url
        if dsn_cad:
            if deps.buscar_admin_por_email_postgres(email_norm, dsn_cad):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Este e-mail já está cadastrado.",
                )
            try:
                novo_id = deps.inserir_admin_postgres(
                    email=email_norm,
                    hashed_password=hashed,
                    nome=nome_limpo,
                    tenant_id=tenant_novo,
                    dsn_sync=dsn_cad,
                    perfil_conta="gratuito",
                )
            except ValueError as e:
                msg = str(e).lower()
                if "cadastrado" in msg or "duplicado" in msg:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=str(e),
                    ) from e
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(e),
                ) from e
        else:
            client = deps.get_supabase_client()
            response = client.table("admins").select("id").eq("email", email_norm).execute()
            if response.data:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Este e-mail já está cadastrado.",
                )
            ins = (
                client.table("admins")
                .insert(
                    {
                        "email": email_norm,
                        "hashed_password": hashed,
                        "nome": nome_limpo[:255],
                        "tenant_id": str(tenant_novo),
                        "perfil_conta": "gratuito",
                    }
                )
                .execute()
            )
            data_ins = ins.data
            if not data_ins:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Cadastro não retornou dados do Supabase. Confira políticas RLS em `admins`.",
                )
            row0 = cast("dict[str, Any]", data_ins[0])
            novo_id = UUID(str(row0["id"]))

        access_token = jwt_tokens.create_access_token(
            subject_user_id=novo_id,
            tenant_id=tenant_novo,
            perfil_conta="gratuito",
            expires_delta=timedelta(minutes=settings_cad.jwt_expire_minutes),
        )
        deps.logger.info("cadastro_consultor_b2b_ok", email=email_norm)
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            nome=nome_limpo,
            perfil_conta="gratuito",
        )

    except HTTPException:
        raise
    except deps.psycopg2.Error as e:
        deps.logger.exception("cadastro_postgres_erro", erro=str(e))
        # Mensagem única para todos os ambientes (contrato HTTP igual ao de produção).
        # Diagnóstico operacional: README («Cadastro na plataforma») + logs da API.
        detail = (
            "Cadastro indisponível: não foi possível gravar no PostgreSQL. "
            "Confira DATABASE_URL e migrações (`admins`, coluna `perfil_conta`)."
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        ) from e
    except deps.jwt.PyJWTError as e:
        deps.logger.exception("cadastro_jwt_emit_erro", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao emitir o token de sessão após cadastro.",
        ) from e
    except Exception as e:
        deps.logger.exception("cadastro_consultor_falhou", tipo=type(e).__name__, erro=str(e))
        msg = str(e).lower()
        if "unique" in msg or "duplicate" in msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Este e-mail já está cadastrado.",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao cadastrar. Veja os logs (evento cadastro_consultor_falhou).",
        ) from e
