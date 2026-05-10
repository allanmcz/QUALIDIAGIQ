"""
Rotas de autenticação — conta na plataforma (login/cadastro consultor).

Camada: Presentation
"""

from __future__ import annotations

from fastapi import APIRouter

from .deps import (
    buscar_admin_por_email_postgres,
    codigo_store,
    get_settings,
    get_supabase_client,
    inserir_admin_postgres,
    jwt,
    logger,
)
from .jwt_tokens import create_access_token, create_self_service_access_token
from .routes_cadastro import router as cadastro_routes
from .routes_login import router as login_routes
from .routes_self_service_token import router as self_service_routes
from .routes_verificacao_email import router as verificacao_routes
from .schemas import (
    CadastroConsultorB2BRequest,
    ConfirmarVerificacaoEmailRequest,
    ConfirmarVerificacaoEmailResponse,
    LoginRequest,
    LoginResponse,
    SelfServiceTokenRequest,
    SelfServiceTokenResponse,
    SolicitarVerificacaoEmailRequest,
    SolicitarVerificacaoEmailResponse,
)

router = APIRouter(prefix="/auth", tags=["Conta na plataforma"])
router.include_router(login_routes)
router.include_router(cadastro_routes)
router.include_router(self_service_routes)
router.include_router(verificacao_routes)

__all__ = [
    "CadastroConsultorB2BRequest",
    "ConfirmarVerificacaoEmailRequest",
    "ConfirmarVerificacaoEmailResponse",
    "LoginRequest",
    "LoginResponse",
    "SelfServiceTokenRequest",
    "SelfServiceTokenResponse",
    "SolicitarVerificacaoEmailRequest",
    "SolicitarVerificacaoEmailResponse",
    "buscar_admin_por_email_postgres",
    "codigo_store",
    "create_access_token",
    "create_self_service_access_token",
    "get_settings",
    "get_supabase_client",
    "inserir_admin_postgres",
    "jwt",
    "logger",
    "router",
]
