"""
Dependências partilhadas do fluxo self-service (facilita patches em testes).

Camada: Presentation
"""

from __future__ import annotations

import asyncio

import psycopg2
import structlog

from src.infrastructure.auth.postgres_admin_login import buscar_email_admin_por_id_e_tenant_postgres
from src.infrastructure.config.settings import get_settings
from src.infrastructure.email_verificacao import codigo_store

logger = structlog.get_logger(__name__)

__all__ = [
    "asyncio",
    "buscar_email_admin_por_id_e_tenant_postgres",
    "codigo_store",
    "get_settings",
    "logger",
    "psycopg2",
]
