# Registro de Issues — 018-QUALIDIAGIQ

| Campo | Valor |
|---|---|
| **Total de issues** | 56 |
| **Distribuição** | P0 = 12 · P1 = 18 · P2 = 16 · P3 = 10 |
| **Data** | 30/04/2026 |

**Legenda de prioridades:**

- **P0** — Bloqueador. Resolver ANTES da S1 (04/05/2026). Risco de segurança, bug runtime ou violação de princípio não-negociável.
- **P1** — Alta. Resolver durante a S1.
- **P2** — Média. Resolver durante S1-S2.
- **P3** — Baixa / refinamento. Backlog.

---

## P0 — BLOQUEADORES (12 issues)

### Segurança

| ID | Arquivo:linha | Descrição | Ação sugerida |
|---|---|---|---|
| **P0-01** | `src/presentation/api/routers/auth_router.py:10` | `SECRET_KEY = "qualidiagiq-super-secret-key-dev"` hardcoded e versionado | Mover para env var `JWT_SECRET_KEY` carregada via `pydantic-settings`; gerar nova chave aleatória de 64 bytes; rotacionar |
| **P0-02** | `auth_router.py:69-84` | Endpoint `POST /auth/create_admin` público, sem auth | Proteger com dependency `get_current_admin`; ou remover completamente e criar admins via CLI/seed seguro |
| **P0-03** | `auth_router.py:64-66` | Backdoor com senha "admin123" em fallback de exception | Remover fallback inteiro; falhar limpo |
| **P0-04** | `dependencies.py:25-39` | `tenant_id` extraído de header HTTP cleartext sem JWT verification | Substituir por JWT custom claim (`tenant_id` dentro do token); validar assinatura |
| **P0-05** | `init.sql:1-46` | RLS NÃO habilitado no schema usado pelo docker-compose | Habilitar `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` + criar policies; ou consolidar com `001_initial_schema.sql` |
| **P0-06** | `main.py:57-63` | `CORSMiddleware allow_origins=["*"] + allow_credentials=True` (combinação proibida W3C) | Definir lista explícita de origens (`["http://localhost:3000", "https://qdi.tributiq.com.br"]`); manter `allow_credentials=True` |

### Bugs runtime

| ID | Arquivo:linha | Descrição | Ação sugerida |
|---|---|---|---|
| **P0-07** | `src/application/services/consultoria_service.py:44` | `PorteEmpresa.MEDIA` não existe — enum tem `MEDIO` | Trocar `PorteEmpresa.MEDIA` → `PorteEmpresa.MEDIO`; adicionar teste unitário |
| **P0-08** | `src/infrastructure/repositories/supabase_diagnostico_repository.py:54-58` | `await` em método não-awaitable do supabase-py síncrono | Migrar para `create_async_client` (Supabase Async) ou remover `async`/`await` da camada |

### Clean Architecture

| ID | Arquivo:linha | Descrição | Ação sugerida |
|---|---|---|---|
| **P0-09** | `src/application/use_cases/realizar_diagnostico.py:122-128` | Camada Application acessa filesystem (`open(_DEVELOPER/...)`) | Criar port `RagBaseConhecimentoPort` + adapter `FileSystemRagAdapter` em Infrastructure |

### Princípios

| ID | Princípio | Descrição | Ação sugerida |
|---|---|---|---|
| **P0-10** | §10.3 Idempotência | Nenhum POST aceita `Idempotency-Key` | Adicionar middleware de idempotência (cache Redis ou tabela DB) |
| **P0-11** | §10.8 Commits PT-BR | 14/14 commits em inglês | Estabelecer hook `commit-msg` com regex `^(feat\|fix\|chore\|arch\|refactor\|test\|docs)\(qdi[-a-z]*\):` |
| **P0-12** | Schema duplicado | `init.sql` (raiz) e `src/infrastructure/db/001_initial_schema.sql` divergentes | Consolidar em fonte única; introduzir Alembic ou Supabase migrations |

---

## P1 — ALTA PRIORIDADE (18 issues)

### Domain

| ID | Arquivo:linha | Descrição | Ação |
|---|---|---|---|
| P1-01 | `domain/entities/diagnostico.py` | Diagnostico não tem método de fábrica `iniciar()` | Refatorar construção para `Diagnostico.iniciar(empresa, respondente, tenant_id)` |
| P1-02 | `domain/entities/diagnostico.py` | Eventos de domínio mencionados mas não emitidos | Adicionar `_eventos_pendentes: list[DomainEvent]` + `pull_eventos()` |
| P1-03 | `domain/entities/questionario.py:38` | `Pergunta` sem `vigencia_inicio` / `vigencia_fim` | Adicionar campos para honrar §10.2 |

### Application

| ID | Arquivo:linha | Descrição | Ação |
|---|---|---|---|
| P1-04 | `application/use_cases/calcular_score_use_case.py:41-49` | Pesos macro hardcoded | Mover para `domain/value_objects/pesos_dimensao.py` versionado |
| P1-05 | `presentation/api/routers/diagnostico_router.py:170-178` | Pesos retornados pelo `/metodologia` divergem dos pesos reais | Sincronizar via fonte única (P1-04) |
| P1-06 | `application/services/consultoria_service.py:33-37` | Datas hardcoded ("Out/2025", "Nov/2025") já passadas | Calcular dinamicamente baseado em `criado_em + delta` |

### Infrastructure

| ID | Arquivo:linha | Descrição | Ação |
|---|---|---|---|
| P1-07 | `infrastructure/adapters/pdf_generator_weasyprint.py:77` | `print()` em produção | Substituir por `structlog.get_logger().warning(...)` |
| P1-08 | `infrastructure/adapters/storage_supabase.py:36` | `print()` em produção + URL mock retornada silenciosamente | Substituir por logger; em prod, propagar exceção |
| P1-09 | `infrastructure/adapters/storage_supabase.py:32` | `upsert: "true"` permite sobrescrita do PDF (viola WORM) | Configurar bucket com Object Lock; salvar com `upsert: false` + sufixo SHA-256 no path |
| P1-10 | `infrastructure/adapters/storage_supabase.py` | Sem cálculo de SHA-256 do PDF | Calcular `hashlib.sha256(file_bytes).hexdigest()` antes de upload; persistir no banco |
| P1-11 | `infrastructure/adapters/llm_ollama.py` | LLM primário deveria ser Anthropic Claude Sonnet 4.6 | Criar `AnthropicLlmAdapter`; manter Ollama como dev/local |

### Presentation

| ID | Arquivo:linha | Descrição | Ação |
|---|---|---|---|
| P1-12 | `presentation/api/routers/diagnostico_router.py:38-66` | Banco de 3 perguntas hardcoded | Persistir em tabela `perguntas` com `vigencia_*`; criar repository |
| P1-13 | `presentation/api/routers/diagnostico_router.py:209-218` | GET retorna `score=None` sempre | Persistir `ScoreCompleto` em JSONB no banco |
| P1-14 | `presentation/api/dependencies.py:88-90` | `OllamaLlmAdapter` injetado por padrão | Selecionar adapter por env (`LLM_PROVIDER=anthropic\|openai\|ollama`) |
| P1-15 | `presentation/api/routers/auth_router.py:33` | `datetime.utcnow()` deprecated em Py 3.12 | Trocar por `datetime.now(UTC)` |

### Frontend

| ID | Arquivo:linha | Descrição | Ação |
|---|---|---|---|
| P1-16 | `frontend/components/wizard/WizardForm.tsx:20-48` | `MOCK_QUESTIONS` hardcoded no Front | Buscar de `GET /diagnosticos/perguntas?empresa=...` |
| P1-17 | `frontend/lib/api/diagnostico.ts:5` | `MOCK_TENANT_ID` fixo | Pegar do JWT após login (combinado com P0-04) |
| P1-18 | `frontend/components/wizard/WizardForm.tsx:267` | Lista de UFs incompleta | Inserir todas as 27 UFs |

---

## P2 — MÉDIA PRIORIDADE (16 issues)

| ID | Localização | Descrição | Ação |
|---|---|---|---|
| P2-01 | `domain/entities/diagnostico.py` | Falta unicidade `tenant_id × cnpj × dia` | Adicionar invariante + UNIQUE constraint |
| P2-02 | `domain/entities/diagnostico.py` | Sem campo `_versao_otimista` | Adicionar `versao: int = 1` para optimistic locking |
| P2-03 | `application/ports/*` | Mistura `Protocol` (LlmService) e `ABC` (demais) | Padronizar todos como `ABC` |
| P2-04 | `application/use_cases/realizar_diagnostico.py:165-170` | Imports tardios dentro de método | Mover para topo do arquivo |
| P2-05 | `infrastructure/adapters/llm_ollama.py` | Sem retry/circuit breaker | Aplicar `@tenacity.retry(...)` + `pybreaker.CircuitBreaker` |
| P2-06 | `infrastructure/adapters/pdf_generator_weasyprint.py:78` | Mock de PDF dummy mesmo em prod | Distinguir DEV vs PROD via env |
| P2-07 | `infrastructure/adapters/email_smtp.py` | Sem template HTML rico | Criar template Jinja2 alinhado com o PDF |
| P2-08 | `presentation/api/main.py` | Sem instrumentação OpenTelemetry | Inicializar `OTLPSpanExporter` no `lifespan` |
| P2-09 | `presentation/api/main.py` | Healthcheck só de aplicação | Adicionar `/health/live` + `/health/ready` (com check DB) |
| P2-10 | `presentation/api/dependencies.py:42-49` | Cliente Supabase global mutável | Usar `lru_cache(maxsize=1)` em vez de global |
| P2-11 | `tests/integration/test_api.py:45` | Teste usa `porte: "EPP"` (não existe) | Corrigir para `pequeno` |
| P2-12 | `tests/` | Zero testes para `consultoria_service` | Criar `tests/unit/application/test_consultoria_service.py` |
| P2-13 | `tests/` | Zero testes para `auth_router` | Criar `tests/unit/presentation/test_auth_router.py` |
| P2-14 | `tests/` | Sem testes RLS multi-tenant | Criar `tests/integration/test_rls.py` com 5 cenários |
| P2-15 | `Dockerfile` | Imagem final ainda contém `build-essential` | Mover deps de build para stage `builder` apenas |
| P2-16 | `Dockerfile` | Sem usuário não-root | Adicionar `RUN useradd -m appuser && USER appuser` |

---

## P3 — BAIXA / REFINAMENTO (10 issues)

| ID | Localização | Descrição |
|---|---|---|
| P3-01 | `frontend/package.json:18` | `lucide-react@^1.12.0` versão suspeita — verificar |
| P3-02 | `frontend/components/wizard/WizardForm.tsx:102` | `as any` no resolver Zod — perde type safety |
| P3-03 | `frontend/components/wizard/WizardForm.tsx:105` | `window.scrollTo` sem guard SSR |
| P3-04 | `pyproject.toml` | Adicionar `hypothesis` para property-based testing |
| P3-05 | `pyproject.toml` | Adicionar `testcontainers` para integration |
| P3-06 | `pyproject.toml` | `langchain-anthropic` declarado mas não usado |
| P3-07 | `Makefile` | `migrate:` é placeholder — implementar Alembic |
| P3-08 | `docker-compose.yml` | Adicionar serviço `mailhog` (porta 1025) |
| P3-09 | `docker-compose.yml` | Frontend instala deps em runtime — colocar em Dockerfile |
| P3-10 | `INICIAR_APP/iniciar.sh` | Inconsistente com `make dev` — escolher um |

---

## Resumo executivo do registro

```
Total: 56 issues
├── P0 (12) ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  21%
├── P1 (18) ██████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░  32%
├── P2 (16) ████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  29%
└── P3 (10) ██████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  18%
```

**Esforço estimado:**

| Prioridade | Issues | Tempo estimado | Sprint |
|---|---:|---:|---|
| P0 | 12 | 14-18h | **S0.5 Hardening (3 dias)** |
| P1 | 18 | 28-36h | S1 + início S2 |
| P2 | 16 | 18-24h | S2 + S3 |
| P3 | 10 | 8-12h | Backlog/folga |
| **Total** | **56** | **68-90h** | — |

Considerando aceleração 2× IA: **34-45h equivalentes** — cabe folgadamente nas 9 semanas (capacidade 247h).

---

**Autor:** Claude · **Data:** 30/04/2026 · **Próximo:** `03_PLANO_ACAO_S05_HARDENING.md`
