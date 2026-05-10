"""
Dependências compartilhadas do pacote `auth_router` (facilita patches nos testes).

Camada: Presentation
"""

from __future__ import annotations

import jwt
import psycopg2
import structlog
from passlib.context import CryptContext

from src.infrastructure.auth.postgres_admin_login import (
    buscar_admin_por_email_postgres,
    inserir_admin_postgres,
)
from src.infrastructure.config.settings import get_settings
from src.infrastructure.email_verificacao import codigo_store
from src.presentation.api.dependencies import get_email_service, get_supabase_client

logger = structlog.get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=12, deprecated="auto")

__all__ = [
    "buscar_admin_por_email_postgres",
    "codigo_store",
    "get_email_service",
    "get_settings",
    "get_supabase_client",
    "inserir_admin_postgres",
    "jwt",
    "logger",
    "psycopg2",
    "pwd_context",
]
