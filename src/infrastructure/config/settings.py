"""
Configuração da aplicação carregada de variáveis de ambiente.

Camada: Infrastructure (adaptador de config — sem regras de domínio).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal, Self
from uuid import UUID

from pydantic import AliasChoices, Field, SecretStr, model_validator
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

    jwt_secret_key: SecretStr = Field(
        default_factory=lambda: SecretStr(""),
        validation_alias=AliasChoices("JWT_SECRET_KEY"),
    )

    #: SMTP para validação em produção (evita mailpit/localhost em APP_ENV=production).
    smtp_host: str = Field(
        default="127.0.0.1",
        validation_alias=AliasChoices("SMTP_HOST"),
    )

    #: Sentry SDK — vazio desativa envio (Sprint 11 handoff).
    sentry_dsn: str | None = Field(
        default=None,
        validation_alias=AliasChoices("SENTRY_DSN"),
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias=AliasChoices("JWT_ALGORITHM"))
    jwt_expire_minutes: int = Field(
        default=480, validation_alias=AliasChoices("JWT_EXPIRE_MINUTES")
    )

    #: Tenant dedicado a diagnósticos gravados após OTP no e-mail (sem conta B2B).
    self_service_tenant_id: UUID = Field(
        default=UUID("44444444-4444-4444-8444-444444444444"),
        validation_alias=AliasChoices("QDI_SELF_SERVICE_TENANT_ID"),
    )
    self_service_jwt_expire_minutes: int = Field(
        default=30,
        ge=5,
        le=120,
        validation_alias=AliasChoices("QDI_SELF_SERVICE_JWT_EXPIRE_MINUTES"),
        description="Validade do JWT emitido após confirmar OTP (gravar diagnóstico self-service).",
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
    otel_exporter_otlp_endpoint: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OTEL_EXPORTER_OTLP_ENDPOINT"),
        description="URL do collector OTLP/HTTP (ex.: https://otel.example.com:4318/v1/traces).",
    )
    otel_exporter_otlp_headers: str | None = Field(
        default=None,
        validation_alias=AliasChoices("OTEL_EXPORTER_OTLP_HEADERS"),
        description="Cabeçalhos OTLP opcionais, formato k=v,k2=v2 (ex.: autenticação no collector).",
    )

    ci_playwright_integrated: bool = Field(
        default=False,
        validation_alias=AliasChoices("QDI_CI_PLAYWRIGHT_INTEGRATED"),
        description="CI: login via Postgres + repo diagnósticos em memória (sem Supabase).",
    )

    public_rate_limit_enabled: bool = Field(
        default=True,
        validation_alias=AliasChoices("QDI_PUBLIC_RATE_LIMIT_ENABLED"),
    )
    public_rate_limit_per_minute: int = Field(
        default=120,
        ge=1,
        validation_alias=AliasChoices("QDI_PUBLIC_RATE_LIMIT_PER_MINUTE"),
        description="Limite por IP/minuto para rotas públicas (normativa, manifesto, metodologia, questionário).",
    )

    pdf_render_timeout_seconds: float = Field(
        default=90.0,
        ge=5.0,
        validation_alias=AliasChoices("QDI_PDF_RENDER_TIMEOUT_SECONDS"),
        description="Timeout WeasyPrint (asyncio.wait_for) por geração de PDF.",
    )

    ollama_base_url: str = Field(
        default="http://127.0.0.1:11434",
        validation_alias=AliasChoices("OLLAMA_BASE_URL", "OLLAMA_URL"),
        description="Endpoint HTTP do Ollama — LLM padrão em desenvolvimento (ADR-003).",
    )
    ollama_model: str = Field(
        default="llama3",
        validation_alias=AliasChoices("OLLAMA_MODEL"),
        description="Nome do modelo no Ollama (ex.: llama3, mistral).",
    )
    ollama_timeout_seconds: float = Field(
        default=30.0,
        ge=1.0,
        le=600.0,
        validation_alias=AliasChoices("OLLAMA_TIMEOUT_SECONDS"),
        description="Timeout (segundos) nas chamadas ao Ollama — REST direta ou cliente LangChain.",
    )

    llm_backend: Literal["langgraph_ollama", "http_ollama", "anthropic"] = Field(
        default="langgraph_ollama",
        validation_alias=AliasChoices("QDI_LLM_BACKEND"),
        description=(
            "Backend de recomendação IA: LangGraph+Ollama (default), HTTP Ollama ou Anthropic Claude."
        ),
    )

    anthropic_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("ANTHROPIC_API_KEY"),
        description="Chave API Anthropic — obrigatória se QDI_LLM_BACKEND=anthropic.",
    )
    anthropic_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        validation_alias=AliasChoices("ANTHROPIC_MODEL", "LLM_MODEL"),
        description="Modelo Claude (Messages API).",
    )

    openai_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY"),
        description="OpenAI — embeddings para RAG-light (busca pgvector) quando DATABASE_URL definido.",
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        validation_alias=AliasChoices("OPENAI_EMBEDDING_MODEL", "QDI_OPENAI_EMBEDDING_MODEL"),
        description="Modelo de embedding — deve produzir 1536 dims (migração 0020).",
    )
    qdi_rag_similarity_threshold: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        validation_alias=AliasChoices("QDI_RAG_SIMILARITY_THRESHOLD"),
        description="Threshold cosine similarity pós-processamento Lexiq RAG.",
    )

    cors_allowed_origins: str = Field(
        default=(
            "http://localhost:3010,http://127.0.0.1:3010,"
            "http://localhost:60001,http://127.0.0.1:60001,"
            "http://localhost:3333,http://127.0.0.1:3333,"
            "http://127.0.0.1:8765,http://localhost:8765"
        ),
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
        key = self.jwt_secret_key.get_secret_value().strip()
        if len(key) >= 32:
            self.jwt_secret_key = SecretStr(key)
        elif (self.app_env or "").strip().lower() == "development":
            self.jwt_secret_key = SecretStr("dev-only-secret-min-32-chars-qdi-local!!")
        else:
            raise ValueError(
                "JWT_SECRET_KEY deve ter ao menos 32 caracteres ou defina APP_ENV=development."
            )
        return self

    @model_validator(mode="after")
    def _producao_segredos_obrigatorios(self) -> Self:
        """
        Sprint 11 — validações adicionais quando APP_ENV=production.

        Falha na inicialização se segredos ou endpoints de desenvolvimento persistirem.
        """
        if (self.app_env or "").strip().lower() != "production":
            return self
        jwt_val = self.jwt_secret_key.get_secret_value().strip()
        if len(jwt_val) < 32:
            raise ValueError("JWT_SECRET_KEY deve ter ao menos 32 caracteres em producao.")
        sup_url = self.supabase_url.strip()
        if not sup_url.startswith("https://"):
            raise ValueError("SUPABASE_URL deve iniciar com https:// em producao.")
        if not self.supabase_key.strip():
            raise ValueError("SUPABASE_ANON_KEY ou SUPABASE_KEY nao pode ser vazio em producao.")
        if self.database_url is None or not str(self.database_url).strip():
            raise ValueError("DATABASE_URL e obrigatorio em producao.")
        host = self.smtp_host.strip().lower()
        if host in ("localhost", "127.0.0.1", "mailpit", "::1"):
            raise ValueError(
                "SMTP_HOST nao pode apontar para ambiente local em producao "
                "(localhost, 127.0.0.1, mailpit)."
            )
        return self

    @model_validator(mode="after")
    def _ci_playwright_somente_dev_com_postgres(self) -> Self:
        """Evita modo CI acidental em produção."""
        if self.ci_playwright_integrated:
            if self.app_env != "development":
                raise ValueError(
                    "QDI_CI_PLAYWRIGHT_INTEGRATED só é permitido com APP_ENV=development."
                )
            if not self.sync_database_url:
                raise ValueError(
                    "QDI_CI_PLAYWRIGHT_INTEGRATED exige DATABASE_URL (Postgres) para login em admins."
                )
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        partes = [p.strip() for p in self.cors_allowed_origins.split(",") if p.strip()]
        return partes if partes else ["http://localhost:3010"]

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
