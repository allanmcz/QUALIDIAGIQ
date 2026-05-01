# Rules `.mdc` por camada — `.cursor/rules/`

> **Como usar este arquivo:**
> 1. Abra `/Users/allan/000-PROJETOS/018-QUALIDIAGIQ/.cursor/rules/`
> 2. Existem 3 arquivos `.mdc` atuais: `communication-style.mdc`, `python-clean-architecture.mdc`, `qdi-domain-context.mdc`
> 3. **MANTER** os 3 existentes (estão bons)
> 4. **ADICIONAR** os 5 novos arquivos abaixo (criados a partir das lições da auditoria)

---

## Inventário (após esta atualização)

| # | Arquivo | Status | Glob | Always Apply |
|---|---|---|---|:---:|
| 1 | `communication-style.mdc` | mantém | `**/*` | ✅ |
| 2 | `python-clean-architecture.mdc` | mantém | `src/**/*.py, tests/**/*.py` | ✅ |
| 3 | `qdi-domain-context.mdc` | mantém | `**/*` | ✅ |
| 4 | **`security-hardening.mdc`** *(novo)* | **CRIAR** | `src/**/*.py` | ✅ |
| 5 | **`port-adapter-pattern.mdc`** *(novo)* | **CRIAR** | `src/application/ports/**, src/infrastructure/adapters/**` | ✅ |
| 6 | **`testing-discipline.mdc`** *(novo)* | **CRIAR** | `tests/**/*.py` | ✅ |
| 7 | **`commits-pt-br.mdc`** *(novo)* | **CRIAR** | `**/*` | ✅ |
| 8 | **`fastapi-presentation.mdc`** *(novo)* | **CRIAR** | `src/presentation/**/*.py` | ✅ |

---

## 4. CRIAR: `.cursor/rules/security-hardening.mdc`

```markdown
---
description: Padrões de segurança obrigatórios pós-auditoria 30/04/2026
globs: src/**/*.py
alwaysApply: true
---

# Segurança — Hardening QDI

## Anti-padrões PROIBIDOS (descobertos na auditoria)

### S-01 · Segredos hardcoded
```python
# ❌ NUNCA
SECRET_KEY = "qualidiagiq-super-secret-key-dev"

# ✅ SEMPRE — via pydantic-settings
from src.infrastructure.config.settings import settings
chave = settings.jwt_secret_key
```

### S-02 · Endpoints administrativos públicos
```python
# ❌ NUNCA
@router.post("/auth/create_admin")  # sem auth!
async def create_admin(req: AdminCreate): ...

# ✅ SEMPRE
@router.post("/auth/create_admin", dependencies=[Depends(verificar_admin)])
async def create_admin(req: AdminCreate, current: Admin = Depends(get_current_admin)):
    if not current.has_permission("admin:create"):
        raise HTTPException(403)
    ...
```

### S-03 · Backdoors em fallback
```python
# ❌ NUNCA
try: ...
except Exception:
    if email == "allan@...." and password == "admin123":
        return create_token(...)  # backdoor!

# ✅ SEMPRE — falhar limpo
try: ...
except Exception as e:
    logger.error("auth_falhou", erro=str(e), email=email)
    raise HTTPException(500, "Erro interno de autenticação")
```

### S-04 · Tenant ID em header cleartext
```python
# ❌ NUNCA — qualquer cliente forja
def get_tenant_id(x_tenant_id: Annotated[str, Header()]) -> UUID:
    return UUID(x_tenant_id)

# ✅ SEMPRE — JWT custom claim
def get_current_user_tenant(
    cred: HTTPAuthorizationCredentials = Depends(bearer)
) -> tuple[UUID, UUID]:
    payload = jwt.decode(cred.credentials, settings.jwt_secret_key, [settings.jwt_algorithm])
    return UUID(payload["sub"]), UUID(payload["tenant_id"])
```

### S-05 · CORS aberto
```python
# ❌ NUNCA — combinação proibida W3C
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, ...)

# ✅ SEMPRE — lista explícita
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,  # de env: csv
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "Idempotency-Key"],
)
```

### S-06 · Print em produção
```python
# ❌ NUNCA
print(f"Erro ao gerar PDF: {e}")

# ✅ SEMPRE
import structlog
logger = structlog.get_logger(__name__)
logger.error("pdf_geracao_falhou", erro=str(e), exc_info=True)
```

## Checklist de segurança antes de cada PR

- [ ] Sem `SECRET`, `API_KEY`, `password` hardcoded (grep -r)
- [ ] Todos POST validam `Idempotency-Key`
- [ ] Tenant_id sempre vem de JWT, nunca de header HTTP
- [ ] CORS configurado com lista explícita
- [ ] Sem `print()` — apenas `structlog.get_logger()`
- [ ] Endpoints administrativos protegidos por `Depends(verificar_admin)`
- [ ] Sem fallback que aceite credenciais hardcoded
```

---

## 5. CRIAR: `.cursor/rules/port-adapter-pattern.mdc`

```markdown
---
description: Padrão Port-Adapter uniforme — sempre ABC + @abstractmethod
globs: src/application/ports/**/*.py, src/infrastructure/adapters/**/*.py, src/infrastructure/repositories/**/*.py
alwaysApply: true
---

# Port-Adapter Pattern — QDI (uniforme)

## Decisão arquitetural (auditoria 30/04)

**Padronizar em ABC + @abstractmethod.** Eliminar mistura com `Protocol` (typing).

## Template de Port

```python
"""
Port (interface) de [responsabilidade].

Camada: Application/Domain (interface — Dependency Inversion Principle)

Implementação concreta vive em:
    src/infrastructure/adapters/[adapter_concreto].py

Princípio: domain define contrato, infrastructure implementa.

Analogia Allan:
    É como definir uma interface no Delphi
    (`type IDiagnosticoRepo = interface`)
    que múltiplas implementações concretas podem honrar.
"""

from __future__ import annotations
from abc import ABC, abstractmethod

class [NomeDoServico]Port(ABC):
    """Port de [responsabilidade]."""

    @abstractmethod
    async def [metodo](self, [params]) -> [retorno]:
        """
        [Descrição do método em PT-BR].

        Args:
            [param]: [descrição]

        Returns:
            [tipo]: [descrição]

        Raises:
            [Exceção]: [quando]
        """
        ...
```

## Template de Adapter

```python
"""
Adapter [Tecnologia] para o port [NomeDoServico]Port.

Camada: Infrastructure
Implementa: src.application.ports.[modulo].[NomeDoServico]Port

Analogia Allan:
    É como o DataModule do Delphi com TFDQuery —
    encapsula a "ferida" da tecnologia externa,
    isolando-a das regras de negócio.
"""

from __future__ import annotations
import structlog
from src.application.ports.[modulo] import [NomeDoServico]Port

logger = structlog.get_logger(__name__)

class [Tecnologia][NomeDoServico]Adapter([NomeDoServico]Port):
    """Adapter concreto que implementa via [Tecnologia]."""

    def __init__(self, ...) -> None:
        ...

    async def [metodo](self, ...) -> ...:
        try:
            ...
        except Exception as e:
            logger.error("[evento]", erro=str(e), exc_info=True)
            raise
```

## Anti-padrões

- ❌ Misturar `typing.Protocol` com `ABC` em ports — padronize ABC
- ❌ Imports tardios dentro de método (`from ... import` no meio do código)
- ❌ Adapter retornando dados mockados em produção sem distinguir DEV/PROD
- ❌ `print()` no adapter — sempre `structlog`
```

---

## 6. CRIAR: `.cursor/rules/testing-discipline.mdc`

```markdown
---
description: Disciplina de testes — pyramid pattern + cobertura
globs: tests/**/*.py
alwaysApply: true
---

# Disciplina de Testes — QDI

## Pirâmide de testes

```
         /\
        /e2e\        ~5% (Playwright — wizard completo)
       /------\
      /integr. \    ~25% (testcontainers + DB real)
     /----------\
    /   unit     \  ~70% (sem I/O, sem rede)
   /--------------\
```

## Coverage obrigatório

| Camada | Mínimo |
|---|---|
| `src/domain/` | **≥ 85%** (princípio §10) |
| `src/application/` | ≥ 80% |
| `src/infrastructure/` | ≥ 70% |
| `src/presentation/` | ≥ 70% |
| **Geral** | ≥ 80% |

CI bloqueia merge se < threshold.

## Padrão de teste unitário

```python
"""Tests for src.domain.value_objects.score (camada DOMAIN)."""
import pytest
from src.domain.value_objects.score import ScoreNumerico, NivelMaturidade


class TestScoreNumerico:
    """Testes do value object ScoreNumerico — invariantes 0..100."""

    @pytest.mark.parametrize("valor,peso", [(0.0, 1.0), (50.5, 5.0), (100.0, 10.0)])
    def test_aceita_valores_validos(self, valor: float, peso: float) -> None:
        score = ScoreNumerico(valor=valor, peso_total_aplicado=peso)
        assert score.valor == valor

    @pytest.mark.parametrize("invalido", [-0.1, 100.1, -1.0, 999.0])
    def test_rejeita_valores_fora_intervalo(self, invalido: float) -> None:
        with pytest.raises(ValueError, match="entre 0 e 100"):
            ScoreNumerico(valor=invalido, peso_total_aplicado=1.0)
```

## Padrão de teste de integração (com testcontainers)

```python
"""Integration tests para SupabaseDiagnosticoRepository."""
import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope="module")
def pg_container():
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg

@pytest.mark.asyncio
async def test_rls_isola_tenants(pg_container, fixture_diagnosticos):
    """RLS deve impedir tenant A de ver dados de tenant B."""
    repo_a = SupabaseDiagnosticoRepository(client=client_with_jwt(tenant_a))
    repo_b = SupabaseDiagnosticoRepository(client=client_with_jwt(tenant_b))

    # Tenant B salva
    await repo_b.salvar(diagnostico_b)

    # Tenant A NÃO deve ver
    resultado = await repo_a.buscar_por_id(diagnostico_b.id, tenant_a)
    assert resultado is None
```

## Anti-padrões

- ❌ Mock de DB em integration test → use testcontainers
- ❌ Teste sem `class Test...` agrupador
- ❌ Teste sem docstring explicando o objetivo
- ❌ Magic numbers nos asserts (use constantes ou parametrize)
- ❌ `assert True` ou `assert response.status_code` (verifique valor exato)
- ❌ Teste que só roda 1 cenário feliz — sempre incluir 1+ erro
```

---

## 7. CRIAR: `.cursor/rules/commits-pt-br.mdc`

```markdown
---
description: Conventional Commits em PT-BR — escopo qdi-*
globs: **/*
alwaysApply: true
---

# Commits PT-BR — QDI

## Padrão obrigatório

```
<tipo>(qdi-<escopo>): <descrição em PT-BR no infinitivo>

[corpo opcional explicando o porquê em PT-BR]

[Refs: `_DEVELOPER/ANALISE_30042026/...`]
```

## Tipos válidos

| Tipo | Quando usar |
|---|---|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `refactor` | Refatoração sem mudança comportamental |
| `arch` | Decisão arquitetural (publicar ADR junto) |
| `chore` | Manutenção (deps, config, limpeza) |
| `test` | Adição/correção de testes |
| `docs` | Documentação |
| `perf` | Melhoria de performance |
| `build` | Build system, Docker, deps |
| `ci` | CI/CD (GitHub Actions) |

## Escopos QDI

| Escopo | Cobertura |
|---|---|
| `qdi-domain` | `src/domain/` |
| `qdi-app` | `src/application/` |
| `qdi-infra` | `src/infrastructure/` |
| `qdi-api` | `src/presentation/` |
| `qdi-front` | `frontend/` |
| `qdi-test` | `tests/` |
| `qdi-docs` | `docs/`, `*.md` |
| `qdi-build` | `Dockerfile`, `Makefile`, `pyproject.toml` |
| `qdi-auth` | módulos de autenticação |
| `qdi-rag` | base de conhecimento, Lexiq |
| `qdi-pdf` | geração de relatório |
| `qdi-hardening` | Sprint S0.5 |

## Exemplos válidos

```
feat(qdi-domain): adicionar entidade Recomendacao com Evidencia
fix(qdi-app): corrigir PorteEmpresa.MEDIA → MEDIO em consultoria_service
refactor(qdi-infra): migrar SupabaseDiagnosticoRepository para AsyncClient
arch(qdi-domain): ADR-002 — pesos de dimensao versionados em tabela
chore(qdi-build): atualizar pyproject para langchain-anthropic 0.3
test(qdi-test): adicionar 5 cenários de RLS multi-tenant
docs(qdi-docs): consolidar fluxograma 8 etapas em 04_METODOLOGIA
```

## Exemplos REJEITADOS pelo hook

```
feat: implement B2B authentication                ← inglês
feat(auth): adiciona login                         ← escopo sem qdi-
add: nova entidade                                ← tipo inválido
qdi-domain: nova entidade                         ← falta tipo
feat (qdi-domain): nova entidade                  ← espaço entre tipo e parênteses
```

## Hook commit-msg (instalar uma vez)

```bash
# .githooks/commit-msg
#!/bin/sh
PADRAO="^(feat|fix|chore|arch|refactor|test|docs|perf|build|ci)\(qdi(-[a-z]+)?\): .+$"
if ! grep -qE "$PADRAO" "$1"; then
    echo "❌ Mensagem de commit não segue Conventional Commits PT-BR"
    echo "   Formato: feat(qdi-domain): adicionar entidade Recomendacao"
    echo "   Tipos: feat, fix, chore, arch, refactor, test, docs, perf, build, ci"
    echo "   Escopos: qdi-domain, qdi-app, qdi-infra, qdi-api, qdi-front, qdi-test, qdi-docs, qdi-build, qdi-auth, qdi-rag, qdi-pdf, qdi-hardening"
    exit 1
fi
```

```bash
# Ativar
git config core.hooksPath .githooks
chmod +x .githooks/commit-msg
```
```

---

## 8. CRIAR: `.cursor/rules/fastapi-presentation.mdc`

```markdown
---
description: Padrões FastAPI — segurança, schemas, idempotência
globs: src/presentation/**/*.py
alwaysApply: true
---

# FastAPI Presentation — QDI

## Estrutura de router

```python
"""Rotas HTTP para o domínio de [contexto].

Camada: Presentation
Responsabilidade: Roteamento HTTP, conversão Pydantic ↔ Domain.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from src.application.use_cases.[caso_de_uso] import [UseCase]
from src.presentation.api.dependencies import (
    get_current_user_tenant,
    get_[caso_de_uso]_use_case,
)
from src.presentation.api.schemas import [Request, Response]

router = APIRouter(prefix="/[recurso]", tags=["[Tag]"])


@router.post(
    "/",
    response_model=[Response],
    status_code=status.HTTP_201_CREATED,
    summary="Criar [recurso]",
    description="...",
)
async def criar_[recurso](
    payload: [Request],
    current: Annotated[tuple[UUID, UUID], Depends(get_current_user_tenant)],
    use_case: Annotated[[UseCase], Depends(get_[caso_de_uso]_use_case)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> [Response]:
    """[descrição PT-BR]."""
    user_id, tenant_id = current

    try:
        resultado = await use_case.execute(...)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return [Response].model_validate(resultado)
```

## Pontos obrigatórios

1. **Sempre** `tags=["..."]` com nome PT-BR
2. **Sempre** `summary` e `description` PT-BR (vão para Swagger)
3. **Sempre** dependência `get_current_user_tenant` em endpoints autenticados
4. **Sempre** `Idempotency-Key` em POST (header obrigatório)
5. **Sempre** `response_model` explícito (não confiar em retorno tipado)
6. **Sempre** tratamento de `ValueError` → 400, `RuntimeError` → 500

## Schemas Pydantic v2

```python
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator

class CriarDiagnosticoRequest(BaseModel):
    """DTO de entrada para POST /diagnosticos/."""
    empresa: EmpresaSchema
    respondente: RespondenteSchema
    respostas: list[RespostaSchema] = Field(min_length=1)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
    )
```

## Anti-padrões

- ❌ `tenant_id` extraído de header `X-Tenant-ID` cleartext → use JWT
- ❌ Banco de dados/perguntas hardcoded em router → use Repository injetado
- ❌ Lógica de cálculo no router → mover para Use Case
- ❌ POST sem `Idempotency-Key` validado
- ❌ Retornar `score=None` em GET — persistir e devolver score real
- ❌ `from src.application.services... import ...` dentro do método (import tardio)
```

---

## Como aplicar tudo no Cursor

```bash
cd /Users/allan/000-PROJETOS/018-QUALIDIAGIQ/.cursor/rules/

# Manter os 3 atuais — apenas criar os 5 novos
# Use o conteúdo entre as marcas ``` markdown ``` de cada seção acima

cat > security-hardening.mdc <<'EOF'
[colar o conteúdo da seção 4]
EOF

cat > port-adapter-pattern.mdc <<'EOF'
[colar o conteúdo da seção 5]
EOF

cat > testing-discipline.mdc <<'EOF'
[colar o conteúdo da seção 6]
EOF

cat > commits-pt-br.mdc <<'EOF'
[colar o conteúdo da seção 7]
EOF

cat > fastapi-presentation.mdc <<'EOF'
[colar o conteúdo da seção 8]
EOF

ls -la
# Esperado: 8 arquivos .mdc no total (3 atuais + 5 novos)
```

Reabra o Cursor para garantir recarregamento das regras.

---

**Próximo:** [`03_GUIA_DESENVOLVIMENTO.md`](./03_GUIA_DESENVOLVIMENTO.md)
