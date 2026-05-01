# Guia de Desenvolvimento — QDI no Cursor

| Campo | Valor |
|---|---|
| **Documento** | Manual prático de desenvolvimento — padrões, workflows, exemplos |
| **Audiência** | Allan Marcio + agente Cursor (Claude Sonnet 4.6) |
| **Quando usar** | Consulta diária durante S0.5 → S4 |
| **Versão** | 1.0 |

---

## 1. Filosofia de desenvolvimento

> **"Faça certo da primeira vez. Se não der, faça certo na refatoração — antes do PR."**

Esta é a filosofia operacional do QDI pós-auditoria 30/04. Os 12 P0 surgiram porque atalhos foram tomados em 14 commits sucessivos. A S0.5 corrige; daqui para a frente, **rigor disciplinado**.

### Os 5 mandamentos

1. **Citação > Inferência** — sem `Evidencia` válida, melhor recusar do que inventar
2. **Tipagem > "Pythônico"** — `mypy strict` é amigo, não inimigo
3. **Teste antes de PR** — DOMAIN ≥ 85%, sempre
4. **PT-BR canônico** — código, comentários, commits, mensagens HTTP
5. **Auditabilidade** — todo número/decisão deve ter trilha verificável

---

## 2. Workflow diário (template)

### 2.1 Início de sessão (10 minutos)

```bash
# Cobrir os 4 checks fundamentais
cd /Users/allan/000-PROJETOS/018-QUALIDIAGIQ

# 1. Saúde do repositório
git status                          # deve estar limpo
git pull origin main                # sincronizar
make test                           # 100% verde antes de começar
make lint                           # zero warnings

# 2. Status do ambiente
docker ps                           # 3 containers (qdi-db, qdi-api, qdi-web)
make logs --tail 50                 # checar últimos logs

# 3. Self-check Allan
echo "Glicemia? Hidratação? Sono ≥ 6h? Pausa programada?"

# 4. Plano do dia
cat _DEVELOPER/ORIENTACAO_CURSOR/04_PLANO_EXECUCAO.md | grep -A 30 "$(date +%Y-%m-%d)"
```

### 2.2 Durante o trabalho (loop de 45 min)

```
┌─ 0min ──────────────────────────────────────┐
│ Definir objetivo SMART do bloco             │
│ Ex.: "Criar Port BaseNormativaPort + 3 testes" │
└───────────────────────────────────────────────┘
                    ↓
┌─ 5min ──────────────────────────────────────┐
│ Cmd+L no Cursor — pedir o bloco completo    │
│ (use prompt de 05_PROMPTS_OPERACIONAIS)     │
└───────────────────────────────────────────────┘
                    ↓
┌─ 25min ─────────────────────────────────────┐
│ Code review do que o Cursor produziu        │
│ - Lê tudo, NÃO confia cego                  │
│ - Aplica pequenos ajustes via Cmd+K         │
└───────────────────────────────────────────────┘
                    ↓
┌─ 40min ─────────────────────────────────────┐
│ make test && make lint                      │
│ Se OK → commit                              │
└───────────────────────────────────────────────┘
                    ↓
┌─ 45min ─────────────────────────────────────┐
│ PAUSA 15min — hidratação, glicemia, alongar │
└───────────────────────────────────────────────┘
```

### 2.3 Fim de sessão (10 minutos)

```bash
# 1. Garantir tudo commitado
git status                          # deve estar limpo
git log --oneline -3                # confirmar últimos commits

# 2. Verificar cobertura
make test                           # ver % de coverage

# 3. Atualizar plano
# Marcar tasks completadas em 04_PLANO_EXECUCAO.md
# Anotar bloqueadores para próxima sessão

# 4. Encerrar ambiente
make down                           # se for ficar offline > 2h
```

---

## 3. Padrões de código por camada

### 3.1 DOMAIN — exemplos práticos

#### Entidade com invariantes

```python
"""
Entidade Recomendacao — agregado-filho de Diagnostico.

Camada: Domain (puro Python)
Base normativa: §10.7 INSTRUCAO_KICKOFF — citação obrigatória RAG
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4


class StatusRecomendacao(Enum):
    """
    Estados possíveis de uma recomendação.

    Princípio §10.6: recusa controlada — quando retriever score < 0.65,
    a recomendação fica como INDEFINIDA e o cliente vê badge honesto
    "Não foi possível classificar com segurança".
    """
    DEFINIDA = "definida"
    INDEFINIDO = "indefinido"


@dataclass(frozen=True, slots=True)
class Evidencia:
    """
    Citação verificável de base legal — exigida em toda Recomendacao DEFINIDA.

    Base normativa:
        - §10.7 INSTRUCAO_KICKOFF — sem evidencia_lexiq ⇒ HTTP 422
        - LC 214/2025 art. 26, § 3º (exemplo de campo a citar)

    Analogia Allan: pense como um INNER JOIN obrigatório no Oracle —
    só que aqui a integridade é com a Lexiq versionada.
    """
    fonte: str  # "LC 214/2025"
    artigo: str  # "art. 26"
    paragrafo: str | None  # "§ 3º"
    inciso: str | None
    texto_citado: str
    vigencia_inicio: datetime
    score_retriever: float

    def __post_init__(self) -> None:
        if not self.fonte:
            raise ValueError("Evidencia exige campo `fonte` não-vazio")
        if not 0.0 <= self.score_retriever <= 1.0:
            raise ValueError(f"score_retriever fora de [0,1]: {self.score_retriever}")


@dataclass(frozen=True, slots=True)
class Recomendacao:
    """
    Recomendação de ação tributária derivada do diagnóstico.

    Invariantes:
        1. Status DEFINIDA exige ao menos 1 Evidencia
        2. Status DEFINIDA exige score_retriever_medio ≥ 0.65 (§10.6)
        3. Status INDEFINIDO permite zero evidências
    """
    id: UUID = field(default_factory=uuid4)
    titulo: str = ""
    texto: str = ""
    status: StatusRecomendacao = StatusRecomendacao.INDEFINIDO
    evidencias: tuple[Evidencia, ...] = ()
    score_retriever_medio: float = 0.0
    criado_em: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.status == StatusRecomendacao.DEFINIDA:
            if not self.evidencias:
                raise ValueError(
                    "Recomendacao DEFINIDA exige ao menos 1 Evidencia "
                    "(§10.7 INSTRUCAO_KICKOFF)"
                )
            if self.score_retriever_medio < 0.65:
                raise ValueError(
                    f"Recomendacao DEFINIDA exige score_retriever_medio ≥ 0.65 "
                    f"(§10.6 INSTRUCAO_KICKOFF). Recebido: {self.score_retriever_medio}"
                )
```

#### Value Object com cálculo determinístico

```python
@dataclass(frozen=True, slots=True)
class PesoDimensao:
    """
    Peso de uma dimensão do score, versionado normativamente.

    Princípio §10.2: versionamento normativo — vigência sobreposta.

    Analogia Allan: equivale a `WHERE :data BETWEEN VIGENCIA_INI AND
    NVL(VIGENCIA_FIM, DATE'9999-12-31')` em SQL Oracle.
    """
    dimensao: Dimensao
    peso: float
    vigencia_inicio: datetime
    vigencia_fim: datetime | None  # None = vigente sem prazo final

    def __post_init__(self) -> None:
        if self.peso < 0:
            raise ValueError(f"Peso não pode ser negativo: {self.peso}")
        if self.vigencia_fim and self.vigencia_fim <= self.vigencia_inicio:
            raise ValueError("vigencia_fim deve ser posterior a vigencia_inicio")

    def vigente_em(self, data: datetime) -> bool:
        """Retorna True se peso é aplicável na data informada."""
        if data < self.vigencia_inicio:
            return False
        if self.vigencia_fim and data >= self.vigencia_fim:
            return False
        return True
```

### 3.2 APPLICATION — exemplos práticos

#### Use case com Ports

```python
"""
Caso de uso: gerar relatório PDF de diagnóstico.

Camada: Application
Depende de: Domain + Ports (PdfGeneratorPort, StoragePort)
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import structlog

from src.application.ports.pdf_generator import PdfGeneratorPort
from src.application.ports.storage_service import StoragePort
from src.domain.entities.diagnostico import Diagnostico

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class ComandoGerarRelatorio:
    diagnostico: Diagnostico
    score_completo: ScoreCompleto


@dataclass(frozen=True)
class ResultadoRelatorio:
    pdf_url: str
    sha256: str  # princípio §10.4 WORM


class GerarRelatorioPdf:
    """
    Use case que orquestra: render PDF → SHA-256 → upload → return URL.
    """

    def __init__(
        self,
        pdf_generator: PdfGeneratorPort,
        storage: StoragePort,
    ) -> None:
        self.pdf_generator = pdf_generator
        self.storage = storage

    async def execute(self, cmd: ComandoGerarRelatorio) -> ResultadoRelatorio:
        # 1. Renderizar PDF
        pdf_bytes = await self.pdf_generator.gerar_pdf_diagnostico(
            cmd.diagnostico, cmd.score_completo
        )

        # 2. Calcular SHA-256 (§10.4 WORM)
        sha = hashlib.sha256(pdf_bytes).hexdigest()
        logger.info(
            "pdf_gerado",
            tenant_id=str(cmd.diagnostico.tenant_id),
            diagnostico_id=str(cmd.diagnostico.id),
            sha256=sha,
            tamanho_bytes=len(pdf_bytes),
        )

        # 3. Upload com path imutável
        url = await self.storage.upload_pdf(
            tenant_id=cmd.diagnostico.tenant_id,
            diagnostico_id=cmd.diagnostico.id,
            file_bytes=pdf_bytes,
            sha256=sha,  # path: tenant_id/diagnostico_id-sha256.pdf
        )

        # 4. Anexar via método de DOMAIN (não mutar diretamente!)
        cmd.diagnostico.anexar_relatorio(url)

        return ResultadoRelatorio(pdf_url=url, sha256=sha)
```

### 3.3 INFRASTRUCTURE — exemplos práticos

#### Adapter Supabase com AsyncClient

```python
"""
Adapter Supabase para DiagnosticoRepository.

Camada: Infrastructure
Implementa: src.domain.repositories.diagnostico_repository.DiagnosticoRepository
"""
from __future__ import annotations
import structlog
from uuid import UUID

from supabase._async.client import AsyncClient
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.domain.entities.diagnostico import Diagnostico

logger = structlog.get_logger(__name__)


class SupabaseDiagnosticoRepository(DiagnosticoRepository):
    """
    Persiste em Supabase com RLS habilitado.

    Princípio §10.1: cliente recebe AsyncClient já com JWT setado
    (`set_session(jwt_token)`) antes de cada request — RLS aplica filtros
    automaticamente baseado no claim `tenant_id`.
    """

    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def salvar(self, diagnostico: Diagnostico) -> None:
        """Upsert idempotente — RLS garante isolamento."""
        payload = self._para_dict(diagnostico)
        try:
            await self.client.table("diagnosticos").upsert(payload).execute()
            logger.info(
                "diagnostico_salvo",
                tenant_id=str(diagnostico.tenant_id),
                diagnostico_id=str(diagnostico.id),
            )
        except Exception as e:
            logger.error(
                "salvar_falhou",
                tenant_id=str(diagnostico.tenant_id),
                erro=str(e),
                exc_info=True,
            )
            raise
```

### 3.4 PRESENTATION — exemplos práticos

#### Router com idempotência + JWT

```python
"""Rotas HTTP de Diagnóstico."""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, Header, HTTPException, status

from src.presentation.api.dependencies import (
    get_current_user_tenant,
    get_realizar_diagnostico_use_case,
)

router = APIRouter(prefix="/diagnosticos", tags=["Diagnósticos"])


@router.post(
    "/",
    response_model=DiagnosticoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar diagnóstico tributário",
    description=(
        "Cria um novo diagnóstico baseado nas respostas do wizard. "
        "Calcula score 0-100 em 7 dimensões e gera PDF executivo."
    ),
)
async def criar_diagnostico(
    payload: IniciarDiagnosticoRequest,
    current: Annotated[tuple[UUID, UUID], Depends(get_current_user_tenant)],
    use_case: Annotated[RealizarDiagnostico, Depends(get_realizar_diagnostico_use_case)],
    idempotency_key: Annotated[
        str,
        Header(
            alias="Idempotency-Key",
            description="UUID único por requisição (princípio §10.3)",
        ),
    ],
) -> DiagnosticoResponse:
    """Cria diagnóstico — idempotente por `Idempotency-Key`."""
    user_id, tenant_id = current

    try:
        resultado = await use_case.execute(...)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        # logger já registrou contexto no adapter
        raise HTTPException(status_code=500, detail="Erro interno ao criar diagnóstico")

    return DiagnosticoResponse.model_validate(resultado)
```

---

## 4. Como pedir coisas ao Cursor (engenharia de prompt)

### 4.1 Princípios

1. **Sempre citar Princípio NN** quando aplicável: "respeite §10.4 WORM"
2. **Sempre dizer a camada** Clean Arch: "criar em `src/application/ports/`"
3. **Sempre incluir base legal** se for regra fiscal: "art. 26 LC 214/2025"
4. **Sempre pedir testes junto** com o código: "+ 3 testes unitários parametrizados"
5. **Sempre pedir docstring PT-BR** explícita

### 4.2 Template de prompt

```
Tarefa: [verbo no imperativo + objeto]

Camada Clean Arch: [domain/application/infrastructure/presentation]
Princípios NN aplicáveis: [§10.X, §10.Y]
Base legal/normativa: [LC 214 art. X / ABNT 17301 cap Y / EC 132 art Z]

Especificação:
- [requisito 1]
- [requisito 2]
- [requisito 3]

Entregáveis:
- [arquivo].py com docstring PT-BR
- tests/unit/[camada]/test_[arquivo].py com 3+ casos felizes e 2+ erros
- Atualizar [arquivo dependente] se necessário

Restrições:
- Sem print(), usar structlog
- Sem hardcode — usar settings/env
- Type hints estritos (mypy strict)

Validação:
- make test passa
- make lint zero warnings
- Cobertura DOMAIN ≥ 85%
```

### 4.3 Exemplo concreto

```
Tarefa: criar Port BaseNormativaPort + Adapter FileSystem

Camada Clean Arch: application/ports + infrastructure/adapters
Princípios NN aplicáveis: §10.7 (citação RAG), Clean Arch (Application sem I/O)
Base legal: Decreto 12.955/2026

Especificação:
- Port abstrato com método `async def obter_base_normativa(tipo: str) -> str`
- Adapter FileSystem que lê de `_DEVELOPER/_NOVIDADE/` (DEV)
- Adapter Supabase que lê de bucket Storage (PROD)
- Trocar implementação via env LLM_PROVIDER

Entregáveis:
- src/application/ports/base_normativa.py (ABC)
- src/infrastructure/adapters/base_normativa_filesystem.py
- tests/unit/application/test_base_normativa_port.py com mock
- Atualizar dependencies.py para injetar conforme env

Restrições:
- Adapter não pode levar Application a saber de filesystem
- Path injetado via __init__, não hardcoded
- Cache LRU de 100 entradas no FileSystem

Validação:
- make test passa
- Refatorar realizar_diagnostico.py para usar este Port
- Remover import os do realizar_diagnostico.py
```

---

## 5. Recursos públicos para estudo aprofundado

### 5.1 Clean Architecture em Python

- **Robert C. Martin — "Clean Architecture"** (livro) cap. 22
- **Leonardo Giordani — "Clean Architectures in Python" (free book)**: `https://www.thedigitalcatonline.com/blog/2016/11/14/clean-architectures-in-python-a-step-by-step-example/`
- **Repo referência**: `https://github.com/Enforcer/clean-architecture-example-1`

### 5.2 FastAPI avançado

- **FastAPI Security** (JWT + OAuth2): `https://fastapi.tiangolo.com/tutorial/security/`
- **FastAPI Best Practices**: `https://github.com/zhanymkanov/fastapi-best-practices`

### 5.3 Pydantic v2

- **Migration guide v1→v2**: `https://docs.pydantic.dev/latest/migration/`
- **pydantic-settings**: `https://docs.pydantic.dev/latest/concepts/pydantic_settings/`

### 5.4 Supabase + RLS

- **RLS guide oficial**: `https://supabase.com/docs/guides/database/postgres/row-level-security`
- **Supabase Python AsyncClient**: `https://supabase.com/docs/reference/python/async-api`
- **PostgREST policies**: `https://postgrest.org/en/stable/auth.html`

### 5.5 Testing

- **pytest documentação**: `https://docs.pytest.org/`
- **testcontainers Python**: `https://testcontainers-python.readthedocs.io/`
- **Hypothesis (property-based)**: `https://hypothesis.readthedocs.io/`

### 5.6 Observabilidade

- **OpenTelemetry Python**: `https://opentelemetry.io/docs/languages/python/`
- **structlog cookbook**: `https://www.structlog.org/en/stable/`

### 5.7 Resiliência

- **tenacity (retry)**: `https://tenacity.readthedocs.io/`
- **pybreaker (circuit breaker)**: `https://github.com/danielfm/pybreaker`

### 5.8 LangChain + LangGraph

- **LangGraph Python**: `https://langchain-ai.github.io/langgraph/`
- **State machines com LangGraph**: `https://langchain-ai.github.io/langgraph/concepts/low_level/`

### 5.9 Reforma Tributária Brasileira

- **Portal oficial Reforma**: `https://www.gov.br/fazenda/pt-br/acesso-a-informacao/acoes-e-programas/reforma-tributaria`
- **Texto LC 214/2025**: `https://www.planalto.gov.br/ccivil_03/leis/lcp/lcp214.htm`
- **NT 2025.002 — Portal NF-e**: `https://www.nfe.fazenda.gov.br/`

### 5.10 ABNT NBR 17301

- **ABNT Catálogo**: `https://www.abnt.org.br/`
- **Norma-mãe ISO 37301:2021**: `https://www.iso.org/standard/75080.html`

---

## 6. Anatomia de um bom Pull Request

```markdown
## feat(qdi-domain): adicionar entidade Recomendacao com Evidencia

### Contexto
A auditoria de 30/04 identificou que o LLM Adapter retorna texto livre sem citação
verificável (princípio §10.7 violado). Esta PR introduz a estrutura de domain para
que toda recomendação carregue suas evidências.

### O que muda
- ✅ Nova `Recomendacao` em `src/domain/entities/recomendacao.py`
- ✅ Novo `Evidencia` em `src/domain/value_objects/evidencia.py`
- ✅ Novo `StatusRecomendacao` enum (DEFINIDA/INDEFINIDO)
- ✅ 12 testes unitários (DOMAIN cov +3pp, agora 87%)
- ✅ Validação: `score_retriever_medio < 0.65` força status INDEFINIDO

### Refs
- `_DEVELOPER/ANALISE_30042026/04_CHECKLIST_PRINCIPIOS_NAO_NEGOCIAVEIS.md` §P-06, §P-07
- INSTRUCAO_KICKOFF_QDI.md §10.6, §10.7

### Como testar
```bash
make test
# Cenário específico:
pytest tests/unit/domain/test_recomendacao.py -v
```

### Próximos passos
- [ ] PR seguinte: `feat(qdi-app): RecomendacaoFactory consumir RAG`
- [ ] PR seguinte: `feat(qdi-infra): AnthropicLlmAdapter retornar Recomendacao tipada`
```

---

## 7. Dúvidas frequentes (FAQ)

### Q1. O Cursor sugeriu uma mudança que afeta 4 camadas. Aceito?

**Não.** Pare, abra um chat com o Claude (ou comigo) explicando a sugestão, e juntos avalie se é refatoração estratégica (vale ADR) ou antipattern.

### Q2. Posso usar `Optional[T]`?

**Não.** Sempre `T | None` (Python 3.10+).

### Q3. Posso colocar `BaseModel` em domain?

**Não.** Domain só usa stdlib + dataclass. `BaseModel` (Pydantic) só em `presentation/`.

### Q4. Quero rodar um experimento rápido. Crio em `src/`?

**Não.** Use `_DEVELOPER/sandbox/` ou um Jupyter notebook. `src/` é território de produção.

### Q5. Posso commitar com `make test` falhando?

**Não.** Hook pre-commit roda `make test`. Se falhar, refatora ou explica em PR draft.

### Q6. O Cursor está alucinando NCM/cClassTrib. O que fazer?

Lembre-o do **§10.7**: sem `Evidencia` da Lexiq, **recuse classificar**. O domínio fiscal exige citação.

### Q7. Encontrei um conflito normativo (LC 214 vs Decreto 12.955). O que fazer?

Pare. Documente o conflito em `docs/refs/conflitos_normativos.md`. Aplique a doutrina:
**hierarquia: EC > LC > Lei Ordinária > Decreto > Portaria > IN**.
Em caso de empate por hierarquia, prevalece a **norma mais recente**.

### Q8. A documentação `docs/refs/05_QUESTIONARIO_v1.md` tem 35 perguntas. Implemento todas?

Para Onda 1.0: **8-10 MUST** conforme INSTRUCAO_KICKOFF §6. As outras 25-27 ficam para Onda 1.1.

---

## 8. Encerramento

Este guia é **vivo**. Atualize-o conforme novos padrões emergirem ou auditorias futuras revelarem novos pontos. Especialmente:

- Novos exemplos práticos das camadas (após cada Sprint, adicione 1-2 cases reais)
- Novos anti-padrões descobertos
- Novos recursos de estudo úteis

**Próximo:** [`04_PLANO_EXECUCAO.md`](./04_PLANO_EXECUCAO.md) — cronograma S0.5 → S4

---

**Autor:** Claude · **Versão:** 1.0 · **Data:** 30/04/2026
