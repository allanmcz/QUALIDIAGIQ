# Checklist — Princípios Não-Negociáveis QDI

| Campo | Valor |
|---|---|
| **Origem** | INSTRUCAO_KICKOFF_QDI.md §10 + system prompt §13 |
| **Data da auditoria** | 30/04/2026 |
| **Score de aderência atual** | 0/12 plenamente · 3/12 parcialmente · 9/12 violados |

---

## Sumário visual

```
P-01 Multi-tenant RLS dia-1               ❌ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0%
P-02 Versionamento normativo              ❌ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0%
P-03 Idempotência (Idempotency-Key)       ❌ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0%
P-04 Imutabilidade WORM + SHA-256         ❌ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0%
P-05 Observabilidade OpenTelemetry        ❌ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0%
P-06 Recusa controlada (score < 0.65)     ❌ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0%
P-07 Citação obrigatória RAG              ❌ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0%
P-08 Commits PT-BR canônico               ❌ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0%
P-09 Pastas em PT-MAIÚSCULAS              ❌ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 0%
P-10 Coverage DOMAIN ≥ 85%                ⚠️  ████████████░░░░░░░░░░░░░░░░░░░░ ~70%
P-11 Score auditável                      ⚠️  ████████████████░░░░░░░░░░░░░░░░  60%
P-12 PDF executivo profissional           ⚠️  ██████████░░░░░░░░░░░░░░░░░░░░░░  40%
```

---

## P-01 · Multi-tenant dia-1 com RLS em 100% das tabelas `qdi.*`

**Status:** ❌ **VIOLADO**

### Evidências

- `init.sql` (raiz, usado pelo docker-compose) **não tem** `ENABLE ROW LEVEL SECURITY`
- `001_initial_schema.sql` tem RLS mas **não é executado**
- `dependencies.py:25-39` extrai `tenant_id` de header HTTP cleartext — qualquer cliente forja
- `dependencies.py:42-49` usa cliente Supabase global compartilhado entre tenants — sem JWT-per-tenant
- Policy `tenant_id = auth.uid()` nunca é avaliada porque não há JWT autenticado (apenas anon key)

### Como remediar

1. Consolidar schema com RLS habilitado (Issue P0-12)
2. Substituir header `X-Tenant-ID` por JWT custom claim (Issue P0-04)
3. Usar `supabase.AsyncClient` com `set_session(jwt)` por request
4. Criar 5 testes de integração que provam isolamento (Issue P2-14)

### Critério de "atendido"

- [ ] 100% das tabelas em `qdi.*` (ou `public` por enquanto) com RLS habilitado
- [ ] Policies cobrem SELECT, INSERT, UPDATE, DELETE
- [ ] JWT carrega `tenant_id` no claim e é setado em `auth.jwt()` antes da query
- [ ] 5 testes de integração comprovam: tenant A não vê dados de tenant B

---

## P-02 · Versionamento normativo (`vigencia_inicio/fim`) em toda regra

**Status:** ❌ **VIOLADO**

### Evidências

- `Pergunta` (`questionario.py:38`) não tem `vigencia_inicio` nem `vigencia_fim`
- Pesos macro em `calcular_score_use_case.py:41-49` hardcoded em código Python
- `consultoria_service.py:33-37` tem datas literais ("Out/2025", "Nov/2025") já no passado em 30/04/2026
- Schema SQL não tem coluna `vigencia_*` em nenhuma tabela

### Como remediar

1. Adicionar `vigencia_inicio: date` e `vigencia_fim: date | None` em `Pergunta`, `Recomendacao`, `Peso`
2. Criar tabela `regras_pesos_dimensao(id, dimensao, peso, vigencia_inicio, vigencia_fim)`
3. Use case lê pesos vigentes na data do diagnóstico, não da data atual
4. Exemplo prático Allan/Oracle: equivale a `WHERE :data_diagnostico BETWEEN VIGENCIA_INI AND NVL(VIGENCIA_FIM, DATE'9999-12-31')`

### Critério de "atendido"

- [ ] Toda regra de cálculo lê de tabela versionada, nunca de constante
- [ ] Re-rodar o mesmo diagnóstico com `data_referencia` diferente produz scores diferentes (validável)

---

## P-03 · Idempotência (`Idempotency-Key`) em toda rota POST

**Status:** ❌ **VIOLADO**

### Evidências

- `diagnostico_router.py:69` aceita POST sem ler `Idempotency-Key`
- `auth_router.py:38, 70` idem
- Sem middleware de idempotência registrado em `main.py`

### Como remediar

Implementar `IdempotencyMiddleware` (Issue P0-10) — modelo no plano S0.5.

### Critério de "atendido"

- [ ] POST sem `Idempotency-Key` retorna 400
- [ ] POST com `Idempotency-Key` repetida retorna o mesmo body com header `X-Idempotent-Replay: true`

---

## P-04 · Imutabilidade WORM em diagnóstico finalizado (append-only + SHA-256)

**Status:** ❌ **VIOLADO**

### Evidências

- `storage_supabase.py:32` usa `upsert: "true"` — qualquer reupload sobrescreve PDF original
- Sem cálculo de SHA-256 do payload
- Schema `diagnosticos` não tem coluna `hash_sha256` nem `hash_evidencias`
- Tabela não tem trigger de "block UPDATE WHERE status='finalizado'"

### Como remediar

```sql
-- migration que adiciona imutabilidade
ALTER TABLE diagnosticos
  ADD COLUMN hash_sha256 CHAR(64),
  ADD COLUMN finalizado_em_imutavel TIMESTAMPTZ;

CREATE OR REPLACE FUNCTION block_update_finalizado()
RETURNS trigger AS $$
BEGIN
    IF OLD.status = 'finalizado' THEN
        RAISE EXCEPTION 'Diagnóstico finalizado é imutável (WORM)';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_block_update_finalizado
BEFORE UPDATE ON diagnosticos
FOR EACH ROW EXECUTE FUNCTION block_update_finalizado();
```

E no Python, calcular `hashlib.sha256(pdf_bytes + json_score).hexdigest()` no momento da finalização.

### Critério de "atendido"

- [ ] UPDATE em diagnóstico finalizado falha com exceção PostgreSQL
- [ ] Hash SHA-256 persistido e verificável a posteriori
- [ ] Bucket de storage com Object Lock ou versioning ativado

---

## P-05 · Observabilidade OpenTelemetry com `tenant_id` em todo log

**Status:** ❌ **VIOLADO**

### Evidências

- `pyproject.toml` tem `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi` mas **nenhum** import nos arquivos
- `main.py` não inicializa `TracerProvider` nem `OTLPSpanExporter`
- Logs usam `logging` padrão (nem `structlog`) sem `tenant_id` nem `trace_id`
- `print()` ainda em produção (P1-07, P1-08)

### Como remediar

```python
# src/infrastructure/observability/setup.py
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
import structlog

def setup_observability(app: FastAPI) -> None:
    provider = TracerProvider()
    provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=settings.otel_endpoint))
    )
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )
```

E em todo log, injetar contextvars com `tenant_id` via middleware.

### Critério de "atendido"

- [ ] `tenant_id` aparece em 100% dos logs estruturados de request
- [ ] Endpoint `/health` exposto + métricas Prometheus em `/metrics`
- [ ] Trace OTLP exportado para Jaeger/Tempo localmente

---

## P-06 · Recusa controlada (score retriever < 0.65 ⇒ INDEFINIDO)

**Status:** ❌ **VIOLADO**

### Evidências

- Não há `RagBaseConhecimentoPort` (criado apenas no plano S0.5)
- `OllamaLlmAdapter` não retorna score de retriever
- Não há tipo `Recomendacao(status="INDEFINIDO")` no domínio

### Como remediar (plano S1)

```python
# domain/value_objects/recomendacao.py
from enum import Enum

class StatusRecomendacao(Enum):
    DEFINIDA = "definida"
    INDEFINIDO = "indefinido"  # quando retriever score < 0.65

@dataclass(frozen=True, slots=True)
class Recomendacao:
    texto: str
    status: StatusRecomendacao
    evidencias: tuple[Evidencia, ...]
    score_retriever_medio: float

    def __post_init__(self):
        if self.status == StatusRecomendacao.DEFINIDA and self.score_retriever_medio < 0.65:
            raise ValueError("Recomendação DEFINIDA exige retriever score ≥ 0.65")
```

### Critério de "atendido"

- [ ] Quando retriever score médio < 0.65, sistema retorna `Recomendacao(status=INDEFINIDO)` com mensagem honesta
- [ ] Cliente vê na UI badge "Não foi possível classificar com segurança" ao invés de resposta inventada

---

## P-07 · Citação obrigatória RAG (sem `evidencia_lexiq` ⇒ HTTP 422)

**Status:** ❌ **VIOLADO**

### Evidências

- `OllamaLlmAdapter.gerar_recomendacao()` retorna `str` livre — sem citações estruturadas
- Não há tipo `Evidencia(art, paragrafo, vigencia, fonte)`
- API não tem validação 422 para resposta sem evidências

### Como remediar

```python
# domain/value_objects/evidencia.py
@dataclass(frozen=True, slots=True)
class Evidencia:
    fonte: str  # "LC 214/2025"
    artigo: str  # "art. 26"
    paragrafo: str | None  # "§ 3º"
    inciso: str | None
    texto_citado: str  # quote literal
    vigencia_inicio: date
    score_retriever: float

# application/use_cases/realizar_diagnostico.py
if not recomendacao.evidencias:
    raise HTTPException(
        status_code=422,
        detail={"erro": "RECOMENDACAO_SEM_EVIDENCIA", "principio_violado": "§10.7"}
    )
```

### Critério de "atendido"

- [ ] Toda `Recomendacao` com status DEFINIDA tem ≥ 1 `Evidencia`
- [ ] PDF cita literalmente o artigo (`art. 26, § 3º LC 214/2025`)
- [ ] Cliente pode clicar na citação e ler o trecho original

---

## P-08 · PT-BR canônico em commits

**Status:** ❌ **VIOLADO**

### Evidências

14/14 commits do histórico em inglês:

```
353ab73 feat: implement B2B authentication system...
cd5075e feat: remove plan restriction for AI recommendations...
4b7dcd9 feat: implement B2B dashboard...
ea28a8c feat: implement AI-driven recommendations...
8154d42 feat: add console logging...
7d449a1 fix: update E2E CNPJ...
9c8bf13 fix: prevent form submission...
0a07022 test: add Playwright E2E testing...
572d7bf feat: add shell script...
8ff3062 feat: implement wizard diagnostic flow...
57657b0 feat: implement PDF generation...
c28b871 feat: initialize Next.js frontend...
162e68b feat: implement PDF generation, storage...
a7942c5 Initial commit
```

### Como remediar

Hook `commit-msg` (Issue P0-11) já desenhado no plano S0.5.

**Atenção:** **não reescrever histórico de commits já no remoto** (`git push origin main` já feito) sem combinar com Allan. O hook impede commits FUTUROS — passado fica como aprendizado.

### Critério de "atendido"

- [ ] Hook `commit-msg` rejeita mensagens fora do padrão
- [ ] Próximos 10 commits 100% em PT-BR com escopo `qdi-*`

---

## P-09 · Pastas em PT-MAIÚSCULAS (`SRC/DOMAIN/APPLICATION/...`)

**Status:** ❌ **VIOLADO** (mas ambíguo)

### Evidências

Estrutura atual em **minúsculas**:

```
src/domain/
src/application/
src/infrastructure/
src/presentation/
```

### Análise crítica

Esse princípio **diverge** da convenção idiomática Python (PEP 8: pacotes em minúsculas). Sigo recomendando **revisitar a decisão**:

- **Argumento PRÓ minúsculas (atual):** PEP 8, IDEs, autoimport, ferramentas (mypy, pytest) tratam maiúsculas como classes
- **Argumento PRÓ maiúsculas (princípio):** alinha com ADR-004 do ecossistema Tributiq; reforça que cada camada é "estrutural"

### Recomendação

**Manter minúsculas e atualizar a INSTRUCAO_KICKOFF + ADR-001** com a justificativa. Caso Allan insista nas maiúsculas, fazer rename completo + ajustar imports automatizadamente.

### Critério de "atendido"

- [ ] Decisão formalizada em ADR (revisão da §10.9)
- [ ] Filesystem coerente com a decisão

---

## P-10 · Coverage DOMAIN ≥ 85%

**Status:** ⚠️ **PARCIALMENTE** (~70% estimado)

### Evidências

- `pyproject.toml:60` define `fail_under = 80` (geral, não DOMAIN específico)
- Bons testes em `test_score.py`, `test_diagnostico.py`, `test_questionario.py`
- Sem teste para alguns métodos de domain (eg. `Diagnostico.anexar_relatorio`)

### Como remediar

```toml
# pyproject.toml
[tool.coverage.report]
fail_under = 80

[[tool.coverage.report.exclude_lines]]
# ...

# Adicionar gate específico para DOMAIN no Makefile:
test-domain-coverage:
    pytest tests/unit/domain --cov=src/domain --cov-fail-under=85
```

### Critério de "atendido"

- [ ] CI bloqueia merge se DOMAIN coverage < 85%
- [ ] DOMAIN coverage HOJE ≥ 85%

---

## P-11 · Score 0-100 sempre auditável

**Status:** ⚠️ **PARCIALMENTE** (60%)

### Pontos positivos

- `ScoreNumerico` tem `peso_total_aplicado` e `perguntas_consideradas`
- Algoritmo de média ponderada determinístico
- Cliente recebe pesos por dimensão na resposta

### Pontos negativos

- Pesos macro divergem entre `calcular_score_use_case.py:41-49` e `diagnostico_router.py:170-178` (Issue A-01)
- `score_por_dimensao` não persiste no banco (só `score_geral`)
- Não há "trilha" — sequência exata de respostas + pesos aplicados não fica auditável após o evento

### Como remediar

Persistir `ScoreCompleto` em coluna `JSONB` no banco + log de auditoria com hash.

### Critério de "atendido"

- [ ] Cliente pode pedir "explique meu score 87" e sistema reconstrói matematicamente
- [ ] Trilha imutável (WORM) com timestamp + pesos vigentes na data

---

## P-12 · PDF executivo profissional

**Status:** ⚠️ **PARCIALMENTE** (40%)

### Pontos positivos

- WeasyPrint configurado
- Template Jinja2 + CSS dedicado em `infrastructure/templates/`

### Pontos negativos

- Mock fallback retorna PDF vazio em produção (I-05)
- 8-12 páginas planejadas mas template atual provavelmente curto
- Sem gráficos Plotly integrados (esperado pela INSTRUCAO_KICKOFF)
- Sem identidade visual Tributiq (logo, paleta, tipografia)

### Como remediar

- Sprint S3 dedicada (já no cronograma)
- Validar render em M2 Max ARM (risco R-3 da minha análise prévia)

---

## Roteiro de monitoramento

| Princípio | Quando re-auditar |
|---|---|
| P-01 a P-08 | Final da S0.5 (04/05) — esperado: 0/8 violados |
| P-09 | Final da S1 (15/05) — esperado: decidido em ADR |
| P-10 | Final da S2 (29/05) — esperado: ≥85% |
| P-11 | Final da S3 (12/06) — esperado: trilha completa |
| P-12 | Final da S4 (30/06) — esperado: PDF aprovado por 5 contadores piloto |

---

**Autor:** Claude · **Data:** 30/04/2026 · **Próxima auditoria:** 04/05/2026 (pós-S0.5)
