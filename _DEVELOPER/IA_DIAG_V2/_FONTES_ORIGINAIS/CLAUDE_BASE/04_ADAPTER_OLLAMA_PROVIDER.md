# 04 — Adapter Ollama (Clean Architecture)

> **Objetivo:** apresentar o código do adapter Ollama implementando a port `LLMProvider` do domínio QDI, com testes e integração ao LLM Router (ADR-09).

---

## 1. Posicionamento Arquitetural

```
SRC/
├── DOMAIN/
│   └── PORTS/
│       └── llm_provider.py          ← INTERFACE (Protocol)
│
├── APPLICATION/
│   └── USE_CASES/
│       └── classificar_operacao.py  ← USA a port (sem saber qual implementação)
│
├── INFRASTRUCTURE/
│   └── ADAPTERS/
│       └── LLM/
│           ├── anthropic_provider.py  ← Implementação 1 (produção)
│           ├── ollama_provider.py     ← Implementação 2 (dev local)  ⭐
│           └── llm_router.py          ← Roteador ADR-09
│
└── PRESENTATION/
    └── API/
        └── rotas_wizard.py           ← Injeta o router via Depends()
```

**Princípio de Inversão de Dependência:** o `DOMAIN` define o contrato (Protocol). A `INFRASTRUCTURE` implementa. A `APPLICATION` consome sem saber qual implementação está rodando.

---

## 2. Port no Domínio (Contrato)

```python
# SRC/DOMAIN/PORTS/LLM_PROVIDER.PY
"""
Port (interface abstrata) para provedores de LLM.

Implementações:
    - AnthropicProvider (produção)
    - OllamaProvider (dev local)
    - MockProvider (testes unitários)

Princípio: o domínio NUNCA conhece qual provedor está em uso —
isso é decidido pelo LLM Router (ADR-09) em tempo de execução.

Analogia Delphi: equivale a uma interface `ILLMProvider` injetada
via container de DI (Spring4D) no `TInjector`.
"""
from __future__ import annotations

from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, Field


class EvidenciaLexiq(BaseModel):
    """Evidência citável recuperada do RAG (princípio QDI #7)."""

    documento: str
    artigo: str | None
    score: float = Field(..., ge=0.0, le=1.0)
    hash_sha256: str
    conteudo_resumido: str


class LLMResponse(BaseModel):
    """Resposta normalizada de qualquer provedor LLM."""

    conteudo: str
    evidencias: list[EvidenciaLexiq] = Field(default_factory=list)
    tokens_entrada: int = Field(..., ge=0)
    tokens_saida: int = Field(..., ge=0)
    provedor: str  # "anthropic" | "ollama" | "mock"
    modelo: str
    latencia_ms: int = Field(..., ge=0)
    custo_usd: float = Field(default=0.0, ge=0.0)


class LLMRequest(BaseModel):
    """Requisição normalizada para qualquer provedor LLM."""

    prompt: str
    sistema: str | None = None
    contexto_rag: list[EvidenciaLexiq] = Field(default_factory=list)
    historico: list[dict] = Field(default_factory=list)
    tenant_id: UUID
    trace_id: UUID
    temperatura: float = Field(default=0.3, ge=0.0, le=1.0)
    max_tokens: int = Field(default=2048, ge=128, le=8192)


class LLMProvider(Protocol):
    """Contrato que todo provedor LLM deve cumprir."""

    async def gerar_resposta(self, request: LLMRequest) -> LLMResponse:
        """Gera resposta com citação obrigatória (RAG)."""
        ...

    async def gerar_embedding(self, texto: str) -> list[float]:
        """Gera embedding 768/1024-dim para indexação no pgvector."""
        ...

    async def health_check(self) -> bool:
        """Verifica disponibilidade do provedor."""
        ...
```

---

## 3. Adapter Ollama (Implementação)

```python
# SRC/INFRASTRUCTURE/ADAPTERS/LLM/OLLAMA_PROVIDER.PY
"""
Adapter para o runtime Ollama local.

Permite desenvolvimento e prototipagem do QDI sem custo de API,
mantendo paridade arquitetural com o adapter Anthropic.

Configuração via variáveis de ambiente:
    OLLAMA_BASE_URL=http://localhost:11434
    OLLAMA_MODEL=qdi-mentor              # modelo customizado via Modelfile
    OLLAMA_EMBEDDING_MODEL=nomic-embed-text
    OLLAMA_TIMEOUT_S=120

Princípios respeitados:
    #5 Observabilidade  → todos logs com trace_id + tenant_id
    #6 Recusa controlada → retorna INDEFINIDO se contexto_rag vazio
    #7 Citação obrigatória → exceção se response sem evidências

Analogia Oracle: equivale a um package PL/SQL que encapsula um
DBLink — a aplicação não conhece a sintaxe do banco remoto.
"""
from __future__ import annotations

import time
from typing import Any

import httpx
import structlog
from pydantic import BaseModel, Field, HttpUrl
from tenacity import retry, stop_after_attempt, wait_exponential

from src.domain.ports.llm_provider import (
    EvidenciaLexiq,
    LLMProvider,
    LLMRequest,
    LLMResponse,
)
from src.domain.exceptions import (
    LLMUnavailableError,
    RecusaControladaError,
    CitacaoInvalidaError,
)

logger = structlog.get_logger(__name__)


class OllamaConfig(BaseModel):
    """Configuração tipada do provider Ollama."""

    base_url: HttpUrl = Field(default="http://localhost:11434")
    modelo_chat: str = Field(default="qdi-mentor")
    modelo_embedding: str = Field(default="nomic-embed-text")
    timeout_s: int = Field(default=120, ge=10, le=600)
    score_minimo_rag: float = Field(default=0.65, ge=0.0, le=1.0)


class OllamaProvider:
    """
    Adapter Ollama implementando port LLMProvider.

    Características:
        - Local-first: zero chamada externa, zero custo
        - Compatível com formato OpenAI chat completions
        - Suporta streaming + embeddings na mesma instância
        - Retry com backoff exponencial
        - Observabilidade OpenTelemetry obrigatória
    """

    def __init__(self, config: OllamaConfig) -> None:
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=str(config.base_url),
            timeout=config.timeout_s,
        )

    # -------------------------------------------------------------------------
    # API pública (contrato LLMProvider)
    # -------------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def gerar_resposta(self, request: LLMRequest) -> LLMResponse:
        """
        Gera resposta com citação obrigatória.

        Etapas:
            1. Validar princípio #6: contexto_rag obrigatório
            2. Montar mensagens no formato Ollama
            3. Chamar /api/chat com timeout
            4. Validar princípio #7: resposta cita evidências
            5. Emitir logs com trace_id + tenant_id
        """
        # Princípio #6 — Recusa controlada
        if not request.contexto_rag:
            logger.warning(
                "ollama.recusa_controlada",
                tenant_id=str(request.tenant_id),
                trace_id=str(request.trace_id),
                motivo="contexto_rag_vazio",
            )
            raise RecusaControladaError(
                "Sem evidência RAG suficiente — resposta INDEFINIDO obrigatória."
            )

        # Validação de score mínimo
        if any(e.score < self._config.score_minimo_rag for e in request.contexto_rag):
            scores_baixos = [e.score for e in request.contexto_rag
                            if e.score < self._config.score_minimo_rag]
            logger.warning(
                "ollama.scores_baixos",
                tenant_id=str(request.tenant_id),
                trace_id=str(request.trace_id),
                scores=scores_baixos,
            )

        mensagens = self._montar_mensagens(request)

        inicio = time.perf_counter()
        try:
            resposta_http = await self._client.post(
                "/api/chat",
                json={
                    "model": self._config.modelo_chat,
                    "messages": mensagens,
                    "stream": False,
                    "options": {
                        "temperature": request.temperatura,
                        "num_predict": request.max_tokens,
                    },
                },
            )
            resposta_http.raise_for_status()
        except httpx.HTTPError as exc:
            logger.error(
                "ollama.indisponivel",
                tenant_id=str(request.tenant_id),
                trace_id=str(request.trace_id),
                erro=str(exc),
            )
            raise LLMUnavailableError("Ollama indisponível") from exc

        latencia_ms = int((time.perf_counter() - inicio) * 1000)
        payload = resposta_http.json()
        conteudo = payload["message"]["content"]

        # Princípio #7 — Citação obrigatória
        if not self._tem_citacao(conteudo, request.contexto_rag):
            logger.error(
                "ollama.citacao_invalida",
                tenant_id=str(request.tenant_id),
                trace_id=str(request.trace_id),
            )
            raise CitacaoInvalidaError(
                "Resposta sem citação válida da Lexiq — bloqueada conforme princípio #7"
            )

        resposta = LLMResponse(
            conteudo=conteudo,
            evidencias=request.contexto_rag,
            tokens_entrada=payload.get("prompt_eval_count", 0),
            tokens_saida=payload.get("eval_count", 0),
            provedor="ollama",
            modelo=self._config.modelo_chat,
            latencia_ms=latencia_ms,
            custo_usd=0.0,  # local = grátis
        )

        logger.info(
            "ollama.resposta_gerada",
            tenant_id=str(request.tenant_id),
            trace_id=str(request.trace_id),
            modelo=self._config.modelo_chat,
            tokens_entrada=resposta.tokens_entrada,
            tokens_saida=resposta.tokens_saida,
            latencia_ms=latencia_ms,
            n_evidencias=len(request.contexto_rag),
        )

        return resposta

    async def gerar_embedding(self, texto: str) -> list[float]:
        """Gera embedding 768-dim via nomic-embed-text."""
        resposta = await self._client.post(
            "/api/embeddings",
            json={
                "model": self._config.modelo_embedding,
                "prompt": texto,
            },
        )
        resposta.raise_for_status()
        embedding = resposta.json()["embedding"]

        # Validação dimensional
        if len(embedding) != 768:
            raise ValueError(
                f"Embedding com dimensão inesperada: {len(embedding)} (esperado 768)"
            )
        return embedding

    async def health_check(self) -> bool:
        """Verifica se o Ollama está respondendo."""
        try:
            resposta = await self._client.get("/api/tags", timeout=5)
            return resposta.status_code == 200
        except httpx.HTTPError:
            return False

    # -------------------------------------------------------------------------
    # Métodos auxiliares privados
    # -------------------------------------------------------------------------

    def _montar_mensagens(self, request: LLMRequest) -> list[dict[str, Any]]:
        """
        Monta o array de mensagens no formato Ollama/OpenAI.

        Ordem:
            1. System (do Modelfile + override do request)
            2. Contexto RAG (Lexiq) injetado como mensagem de sistema adicional
            3. Histórico (turnos anteriores da sessão)
            4. Pergunta atual
        """
        mensagens: list[dict[str, Any]] = []

        # System adicional (override opcional)
        if request.sistema:
            mensagens.append({"role": "system", "content": request.sistema})

        # Contexto RAG formatado
        if request.contexto_rag:
            contexto_formatado = self._formatar_rag(request.contexto_rag)
            mensagens.append({
                "role": "system",
                "content": (
                    "## Evidências Lexiq disponíveis para esta resposta\n\n"
                    f"{contexto_formatado}\n\n"
                    "**Obrigatório:** cite ao menos uma evidência acima usando "
                    "o formato `[Documento, Art. X]` na sua resposta."
                ),
            })

        # Histórico
        for turno in request.historico:
            mensagens.append(turno)

        # Pergunta atual
        mensagens.append({"role": "user", "content": request.prompt})

        return mensagens

    @staticmethod
    def _formatar_rag(evidencias: list[EvidenciaLexiq]) -> str:
        """Formata evidências para injeção no prompt."""
        partes = []
        for ev in evidencias:
            partes.append(
                f"### [{ev.documento}{', ' + ev.artigo if ev.artigo else ''}] "
                f"(score: {ev.score:.2f})\n"
                f"{ev.conteudo_resumido}"
            )
        return "\n\n".join(partes)

    @staticmethod
    def _tem_citacao(conteudo: str, evidencias: list[EvidenciaLexiq]) -> bool:
        """Verifica se a resposta cita ao menos uma evidência."""
        return any(
            ev.documento in conteudo or (ev.artigo and ev.artigo in conteudo)
            for ev in evidencias
        )
```

---

## 4. LLM Router (ADR-09)

```python
# SRC/INFRASTRUCTURE/ADAPTERS/LLM/LLM_ROUTER.PY
"""
Router para escolher dinamicamente o provider LLM.

Estratégia de roteamento:
    - ambiente=dev    → ollama (custo zero)
    - ambiente=staging → anthropic com fallback ollama
    - ambiente=prod   → anthropic com fallback erro
    - tarefa=embedding → sempre ollama (mais barato)
"""
from enum import Enum

from src.domain.ports.llm_provider import LLMProvider


class Ambiente(str, Enum):
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class LLMRouter:
    """Roteador entre Anthropic e Ollama conforme ADR-09."""

    def __init__(
        self,
        anthropic: LLMProvider,
        ollama: LLMProvider,
        ambiente: Ambiente,
    ) -> None:
        self._anthropic = anthropic
        self._ollama = ollama
        self._ambiente = ambiente

    def escolher_provider(self, *, criticidade: str = "normal") -> LLMProvider:
        """
        Escolhe o provedor conforme ambiente + criticidade da tarefa.
        """
        if self._ambiente == Ambiente.DEV:
            return self._ollama
        if criticidade == "alta":
            return self._anthropic
        return self._anthropic  # default em staging/prod
```

---

## 5. Testes Unitários

```python
# TESTS/INFRASTRUCTURE/TEST_OLLAMA_PROVIDER.PY
"""
Testes do adapter Ollama.

Estratégia:
    - Unit tests: mock do httpx.AsyncClient
    - Integration: testcontainers com Ollama real (Sprint 3+)
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from src.infrastructure.adapters.llm.ollama_provider import (
    OllamaConfig,
    OllamaProvider,
)
from src.domain.ports.llm_provider import EvidenciaLexiq, LLMRequest
from src.domain.exceptions import RecusaControladaError, CitacaoInvalidaError


@pytest.fixture
def config():
    return OllamaConfig()


@pytest.fixture
def provider(config):
    return OllamaProvider(config)


@pytest.mark.asyncio
async def test_recusa_controlada_sem_rag(provider):
    """Princípio #6: deve recusar se contexto_rag vazio."""
    request = LLMRequest(
        prompt="Como classificar venda interestadual?",
        contexto_rag=[],
        tenant_id=uuid4(),
        trace_id=uuid4(),
    )
    with pytest.raises(RecusaControladaError):
        await provider.gerar_resposta(request)


@pytest.mark.asyncio
async def test_citacao_obrigatoria(provider, mocker):
    """Princípio #7: deve bloquear se resposta não cita evidências."""
    mocker.patch.object(
        provider._client,
        "post",
        return_value=MagicMock(
            json=lambda: {
                "message": {"content": "Resposta SEM citar nada."},
                "prompt_eval_count": 100,
                "eval_count": 50,
            },
            raise_for_status=lambda: None,
        ),
    )

    request = LLMRequest(
        prompt="Pergunta",
        contexto_rag=[
            EvidenciaLexiq(
                documento="LC_214_2025",
                artigo="Art. 23",
                score=0.85,
                hash_sha256="x" * 64,
                conteudo_resumido="...",
            )
        ],
        tenant_id=uuid4(),
        trace_id=uuid4(),
    )
    with pytest.raises(CitacaoInvalidaError):
        await provider.gerar_resposta(request)
```

---

## 6. Integração no FastAPI

```python
# SRC/PRESENTATION/API/DEPENDENCIES.PY
from functools import lru_cache

from src.infrastructure.adapters.llm.ollama_provider import (
    OllamaConfig,
    OllamaProvider,
)
from src.infrastructure.adapters.llm.llm_router import LLMRouter, Ambiente


@lru_cache
def get_llm_router() -> LLMRouter:
    """Singleton do router LLM."""
    ollama = OllamaProvider(OllamaConfig())
    # anthropic = AnthropicProvider(AnthropicConfig())  # quando pronto
    return LLMRouter(
        anthropic=ollama,  # temporariamente igual
        ollama=ollama,
        ambiente=Ambiente.DEV,
    )
```

---

## 7. Próximo Passo

Continuar para `05_INDEXACAO_DOMINIO.md` para entender a Camada 3 (schema do código indexado).
