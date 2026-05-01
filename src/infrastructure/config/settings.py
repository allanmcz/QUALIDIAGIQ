"""
Configuração da aplicação carregada de variáveis de ambiente.

Camada: Infrastructure (adaptador de config — sem regras de domínio).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Self

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parâmetros runtime — nunca commitar segredos reais."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", validation_alias=AliasChoices("APP_ENV"))

    supabase_url: str = Field(
        default="http://127.0.0.1:54321",
        validation_alias=AliasChoices("SUPABASE_URL"),
    )
    supabase_key: str = Field(
        default="",
        validation_alias=AliasChoices("SUPABASE_ANON_KEY", "SUPABASE_KEY"),
    )

    jwt_secret_key: str = Field(
        default="",
        validation_alias=AliasChoices("JWT_SECRET_KEY"),
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias=AliasChoices("JWT_ALGORITHM"))
    jwt_expire_minutes: int = Field(
        default=480, validation_alias=AliasChoices("JWT_EXPIRE_MINUTES")
    )

    database_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DATABASE_URL"),
        description="PostgreSQL (ex.: postgresql+asyncpg://...). Usado para idempotência sync.",
    )

    otel_tracing_enabled: bool = Field(
        default=False,
        validation_alias=AliasChoices("OTEL_TRACING_ENABLED"),
    )
    otel_service_name: str = Field(
        default="qualidiagiq-api",
        validation_alias=AliasChoices("OTEL_SERVICE_NAME"),
    )

    cors_allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        validation_alias=AliasChoices("CORS_ALLOWED_ORIGINS"),
    )

    # Idempotência (POST /diagnosticos/) — MVP em memória; produção pode usar Redis
    idempotency_ttl_seconds: int = Field(
        default=3600,
        validation_alias=AliasChoices("IDEMPOTENCY_TTL_SECONDS"),
    )
    idempotency_max_entries: int = Field(
        default=10_000,
        validation_alias=AliasChoices("IDEMPOTENCY_MAX_ENTRIES"),
    )

    @model_validator(mode="after")
    def _jwt_secret_minimo(self) -> Self:
        """Em development permite fallback local; fora disso exige chave forte."""
        key = self.jwt_secret_key.strip()
        if len(key) >= 32:
            self.jwt_secret_key = key
        elif self.app_env == "development":
            self.jwt_secret_key = "dev-only-secret-min-32-chars-qdi-local!!"
        else:
            raise ValueError(
                "JWT_SECRET_KEY deve ter ao menos 32 caracteres ou defina APP_ENV=development."
            )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        partes = [p.strip() for p in self.cors_allowed_origins.split(",") if p.strip()]
        return partes if partes else ["http://localhost:3000"]

    @property
    def sync_database_url(self) -> str | None:
        """URL para SQLAlchemy sync (middleware idempotência)."""
        if not self.database_url or not str(self.database_url).strip():
            return None
        u = str(self.database_url).strip()
        if "+asyncpg" in u:
            return u.replace("postgresql+asyncpg://", "postgresql://", 1)
        if u.startswith("postgresql://"):
            return u
        return None


@lru_cache
def get_settings() -> Settings:
    """Instância singleton de Settings (cache por processo)."""
    return Settings()
