# Análise Técnica Detalhada — 018-QUALIDIAGIQ

| Campo | Valor |
|---|---|
| **Repositório** | `/Users/allan/000-PROJETOS/018-QUALIDIAGIQ` (READ-ONLY) |
| **Commit auditado** | `353ab73` (B2B authentication) |
| **Branch** | `main` (limpa, sem alterações pendentes) |
| **Auditor** | Claude · 30/04/2026 |

---

## 1. Inventário quantitativo

### 1.1 Volumetria

| Métrica | Valor |
|---|---:|
| Arquivos Python em `src/` | 25 (excluindo `__init__.py`) |
| Linhas de código Python | 2.034 |
| Arquivos TS/TSX no Frontend | 18 |
| Linhas de código Frontend | 1.477 |
| Arquivos de teste | 10 |
| Funções de teste | 54 |
| Linhas de teste | 1.135 |
| Razão teste/código (LoC) | 56% (excelente em volume; conteúdo qualitativo abaixo) |
| Commits no histórico | 14 (todos em inglês — viola §10.8) |

### 1.2 Estrutura de pastas

```
src/
├── domain/         (5 arquivos)  — entities + value_objects + repositories (interfaces)
├── application/    (8 arquivos)  — use_cases + ports + services
├── infrastructure/ (10 arquivos) — adapters + repositories + db + pdf + email
└── presentation/   (5 arquivos)  — api + routers + schemas + dependencies
```

**Aderência à Clean Architecture:** estrutura **EM MINÚSCULAS** — diverge do princípio §10.9 da INSTRUCAO_KICKOFF que exige `SRC/DOMAIN/APPLICATION/INFRASTRUCTURE/PRESENTATION/`. **Decisão precisa ser ratificada via ADR.**

---

## 2. Análise camada-a-camada

### 2.1 DOMAIN (Nota 82/100) — pontos fortes

#### O que está sólido

`src/domain/entities/diagnostico.py` está **bem desenhado**:

- Uso correto de `dataclass(frozen=True, slots=True)` para `EmpresaInfo` e `Respondente` (Value Objects imutáveis)
- Invariantes validados em `__post_init__` (CNPJ 14 dígitos, UF 2 chars)
- Enums tipados para `StatusDiagnostico`, `RegimeTributario`, `PorteEmpresa`, `SetorMacro`, `PlanoDiagnostico`
- Método `finalizar()` valida transição de estado e intervalo do score
- Exceção de domínio dedicada (`DiagnosticoNaoFinalizavelError`)
- Documentação extensa em PT-BR com analogia Delphi/Winthor (cumpre §6 da INSTRUCAO_KICKOFF)

`src/domain/value_objects/score.py`:

- `NivelMaturidade.from_score()` corretamente classmethod
- `ScoreNumerico` com `peso_total_aplicado` e `perguntas_consideradas` — vai sustentar auditabilidade futura
- `PercentilSetorial` já preparado para benchmark (Onda 1.1)

#### Pontos de melhoria (Domain)

**D-01 — Falta de Aggregate Root explícito.** `Diagnostico` referencia `Respondente` e `EmpresaInfo` mas não há método de fábrica `Diagnostico.iniciar(...)` que valide invariantes do agregado completo. Em DDD canônico (Eric Evans), o AR é responsável por proteger todos os invariantes do agregado.

**D-02 — Eventos de domínio mencionados mas não emitidos.** A docstring lista `DiagnosticoIniciado`, `DiagnosticoFinalizado`, `DiagnosticoExpirado` mas não há infraestrutura de eventos. Em sistema multi-tenant com integrações futuras (QFI, QMI), eventos são essenciais.

**D-03 — `Diagnostico` não é frozen.** Por design (estado muta), mas isso significa que precisaria de **lock otimista** (versão) para concorrência. Falta campo `_versao_otimista: int`.

**D-04 — Falta de unicidade `tenant_id × cnpj × periodo`.** Não há regra explícita impedindo dois diagnósticos paralelos para o mesmo CNPJ no mesmo dia, no mesmo tenant. Pode gerar duplicidade indesejada quando o front faz retry.

**D-05 — `ScoreCompleto` e `Diagnostico` desconectados.** A entidade `Diagnostico` armazena apenas `score_geral: float | None`, perdendo a riqueza do `ScoreCompleto`. Quando o GET busca, perde-se a discriminação por dimensão (já reconhecido em comentário no router linha 197).

**D-06 — `Pergunta` é frozen mas `peso` é mutável de fato em runtime.** Como `frozen=True`, está OK; mas o peso vem hardcoded. Faltaria `vigencia_inicio: date` e `vigencia_fim: date | None` para honrar §10.2 (versionamento normativo).

---

### 2.2 APPLICATION (Nota 66/100)

#### Análise de `realizar_diagnostico.py`

```python
# linha 122-128 — VIOLAÇÃO CRÍTICA DE CLEAN ARCHITECTURE
import os
caminho_decreto = os.path.join(os.path.dirname(__file__), "../../../_DEVELOPER/_NOVIDADE/00_RESUMO_EXECUTIVO_Decreto_12955.txt")
if os.path.exists(caminho_decreto):
    with open(caminho_decreto, "r", encoding="utf-8") as f:
        base_normativa = f.read()[:4000]
```

**Problemas:**

1. **A camada Application está acessando o sistema de arquivos diretamente.** Isso é trabalho de Infrastructure (adapter de repositório de RAG/conhecimento).
2. O path relativo `../../../_DEVELOPER/...` quebrará dentro do Docker (volume `/app/src` — não existe `_DEVELOPER` no container).
3. O `import os` está dentro do método (deveria estar no topo).
4. Não há cache — a cada diagnóstico relê o arquivo.
5. Truncar em 4000 chars **sem chunking inteligente** desperdiça contexto e perde citações importantes.
6. Não há fallback caso o arquivo não exista — usa string vazia silenciosamente.

#### Análise de `calcular_score_use_case.py`

**Pontos positivos:**
- Algoritmo de média ponderada está matematicamente correto
- Iteração sobre `Dimensao` enum é defensiva (`dict.fromkeys(Dimensao, 0.0)`)
- Arredondamento explícito (2 decimais)

**Pontos críticos:**

```python
# linhas 41-49 — pesos hardcoded
pesos_macro_dimensoes = {
    Dimensao.FISCAL: 1.5,
    Dimensao.TECNOLOGICA: 1.3,
    ...
}
```

vs. router (linhas 169-178):
```python
"pesos_por_dimensao": {
    Dimensao.FISCAL.value: 1.5,
    Dimensao.ESTRATEGICA.value: 1.2,    # <-- DIVERGE
    Dimensao.CONTABIL.value: 1.3,        # <-- DIVERGE
    Dimensao.FINANCEIRA.value: 1.1,      # <-- DIVERGE
    Dimensao.OPERACIONAL.value: 1.0,
    Dimensao.TECNOLOGICA.value: 1.4,    # <-- DIVERGE
    Dimensao.COMPLIANCE_ABNT.value: 1.5, # <-- DIVERGE
}
```

**A-01 — Pesos divergentes em duas localidades:** o `/diagnosticos/metodologia` retorna ao cliente um conjunto de pesos que **não é o usado no cálculo real**. Isto fere o princípio §10.11 (auditabilidade) e gera litígio se um cliente questionar o número.

#### Análise de `consultoria_service.py`

**🔴 BUG RUNTIME CRÍTICO — linha 44:**

```python
if diagnostico.empresa.porte in [PorteEmpresa.GRANDE, PorteEmpresa.MEDIA]:
```

**`PorteEmpresa.MEDIA` não existe** — o enum em `diagnostico.py` linha 65 define `MEDIO = "medio"`. Qualquer chamada para esta função vai disparar `AttributeError: MEDIA` em runtime. Isso significa que o **fluxo principal está quebrado** para qualquer empresa de porte médio ou grande.

**Outros pontos:**

- Não recebe `tenant_id` — mesmo `Comitê Tributário Reforma` é sugerido para todos sem segmentação real
- Datas hardcoded ("Out/2025", "Nov/2025") — já no passado em 30/04/2026
- Estado de implantação CBS (Decreto 12.955/2026) é um snapshot — sem versionamento

#### Ports (interfaces)

**Inconsistência metodológica:**

| Port | Estilo |
|---|---|
| `LlmServicePort` | `Protocol` (typing) |
| `PdfGeneratorPort` | `ABC` + `@abstractmethod` |
| `StorageServicePort` | `ABC` + `@abstractmethod` |
| `EmailServicePort` | `ABC` + `@abstractmethod` |
| `DiagnosticoRepository` | `ABC` + `@abstractmethod` |

**A-02 — Padrão Port/Adapter inconsistente.** Use um padrão único — recomendo `ABC` (mais explícito para o Allan vindo do Delphi/interfaces).

---

### 2.3 INFRASTRUCTURE (Nota 58/100)

#### `supabase_diagnostico_repository.py`

**Análise crítica:**

```python
# linha 49 — síncrono dentro de async
self.client.table("diagnosticos").upsert(payload).execute()
```

**I-01 — `salvar` é declarado `async` mas usa client síncrono.** `supabase-py v2.x` tem AsyncClient (`create_async_client`), mas aqui usa síncrono e fingem ser async. Em produção, vai bloquear o event loop.

```python
# linhas 52-59 — busca async com client síncrono
response = (
    await self.client.table("diagnosticos")  # <-- await em chamada síncrona
    .select("*")...
)
```

**I-02 — `await` em método NÃO awaitable.** `supabase-py v2.7+` o `Client` síncrono retorna `APIResponse` direto, não coroutine. Este código gera `TypeError: object APIResponse can't be used in 'await' expression` em runtime real.

**I-03 — Falta tratamento de erro:** sem `try/except` envolvendo `.execute()`. Falhas de rede ou RLS denial vão propagar sem contexto.

#### `pdf_generator_weasyprint.py`

```python
# linhas 71-78
try:
    from weasyprint import CSS, HTML
    return HTML(string=html_out).write_pdf(...)
except Exception as e:
    print(f"Aviso: weasyprint não disponível ({e}). Retornando PDF mockado.")
    return b"%PDF-1.4..."
```

**I-04 — `print()` em produção** (viola anti-padrão §10 da INSTRUCAO_KICKOFF). Deveria ser `structlog`.

**I-05 — Mock silencioso de PDF inválido.** Em prod, retornar bytes inválidos vai explodir no upload Supabase ou no PDF reader do cliente. Deveria propagar erro claro.

**I-06 — Geração síncrona via `asyncio.to_thread`** está correto, mas o tempo de WeasyPrint em ARM (M2 Max) com fontes Pango pode chegar a 2-5s — sem timeout configurável.

#### `storage_supabase.py`

```python
# linhas 35-37 — outro print em produção
except Exception as e:
    print(f"Aviso: Falha ao fazer upload...")
    return f"http://localhost:8000/mock-storage/{file_path}"
```

**I-07 — URL mockada em produção.** Em produção, retornar URL `localhost` é pior do que falhar — vai parar no Supabase mas o cliente recebe URL impossível.

**I-08 — Sem WORM (Write-Once-Read-Many).** `upsert: "true"` permite sobrescrita do PDF — viola princípio §10.4 (imutabilidade WORM com SHA-256).

**I-09 — Sem assinatura SHA-256** dos bytes do PDF antes do upload.

#### `llm_ollama.py`

**I-10 — Modelo Ollama (llama3) é fallback, não primário.** A INSTRUCAO_KICKOFF prevê **Anthropic Claude Sonnet 4.6** como primário e GPT-4o-mini como fallback. Aqui só há Ollama.

**I-11 — Sem retry / circuit breaker.** Apesar de `tenacity` e `pybreaker` estarem nas deps, não são usados aqui.

**I-12 — Sem citação RAG.** O LLM gera texto livre sobre o decreto, sem mecanismo de citação verificável (sem `evidencia_lexiq` que o §10.7 exige).

#### Schemas SQL

**🔴 CRÍTICO — Dois schemas divergentes:**

| Aspecto | `init.sql` (raiz) | `src/infrastructure/db/001_initial_schema.sql` |
|---|---|---|
| RLS habilitado? | **NÃO** ❌ | SIM ✅ |
| Coluna `plano` | SIM | NÃO |
| Coluna `empresa_porte` tipo | `VARCHAR(50)` | `TEXT` |
| Constraint check status | ausente | presente |
| Tabela `admins` | SIM | NÃO |

**I-13 — Qual é a fonte da verdade?** O `docker-compose.yml` linha 23 monta o `init.sql` da raiz como entrypoint do PostgreSQL — então **na prática RLS não está habilitado em ambiente de dev**. O `001_initial_schema.sql` é código-morto.

---

### 2.4 PRESENTATION (Nota 52/100)

#### `auth_router.py` — vulnerabilidades graves

```python
# linha 10
SECRET_KEY = "qualidiagiq-super-secret-key-dev"
```

**P-01 — 🔴 SECRET HARDCODED.** Mesmo se for "dev", está versionado no Git. Atacante extrai do GitHub e forja JWTs válidos. **Bloqueador absoluto antes de qualquer commit público.**

```python
# linha 33 — Python 3.12 deprecated warning
expire = datetime.utcnow() + (expires_delta or ...)
```

**P-02 — `datetime.utcnow()` está deprecated** em Python 3.12. Usar `datetime.now(UTC)`.

```python
# linhas 69-84
@router.post("/create_admin")
async def create_admin(request: AdminCreate):
    """Rota para criar usuário admin. Em prod deveria ser protegida!"""
```

**P-03 — 🔴 ENDPOINT PÚBLICO QUE CRIA ADMIN.** Sem autenticação. Sem rate limit. Sem CSRF. Qualquer um na internet faz `POST /auth/create_admin` e vira root do sistema. Crítico.

```python
# linhas 64-66 — fallback por igualdade de string
if request.email == "allan@tributolab.com.br" and request.password == "admin123":
    access_token = create_access_token(...)
```

**P-04 — Backdoor por igualdade direta de senha.** Mesmo "admin123" é uma senha trivial que viola política mínima.

#### `dependencies.py` — RLS quebrado

```python
def get_tenant_id(x_tenant_id: ...) -> UUID:
    if not x_tenant_id:
        raise HTTPException(...)
    return UUID(x_tenant_id)
```

**P-05 — `tenant_id` vem de header HTTP cleartext.** Qualquer cliente forja `X-Tenant-ID: <uuid-de-outro-tenant>` e acessa dados alheios. **Isto inviabiliza completamente o multi-tenant.**

```python
def get_supabase_client() -> Client:
    global _supabase_client  # <-- mutável global
    if _supabase_client is None:
        url = os.environ.get("SUPABASE_URL", "http://127.0.0.1:60000")
        key = os.environ.get("SUPABASE_KEY", "dummy_key")
        _supabase_client = create_client(url, key)
    return _supabase_client
```

**P-06 — Cliente Supabase global compartilhado entre tenants.** Significa que **mesmo a chave** do cliente é compartilhada — não há JWT-per-tenant. Combinado com P-05, **RLS é placebo**: a policy `tenant_id = auth.uid()` nunca é avaliada porque não há JWT autenticado.

**P-07 — `dummy_key` como default.** Em desenvolvimento vai gerar erro silencioso obscuro.

**P-08 — Sem `lru_cache` na fábrica.** A cada request o FastAPI tenta criar — mitigado pelo global, mas é antipattern.

#### `main.py` — CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**P-09 — `allow_origins=["*"]` + `allow_credentials=True`** é uma combinação **proibida pelo W3C CORS spec**. Browsers modernos rejeitam essa configuração. Nunca funcionará com cookies/JWT.

#### `diagnostico_router.py`

**P-10 — Banco de perguntas hardcoded** em função `_get_banco_perguntas()` com **3 perguntas** apenas. Promessa: 25-40 ou 35.

**P-11 — Sem `Idempotency-Key`** no POST `/diagnosticos/`. Princípio §10.3 violado.

**P-12 — `from uuid import uuid4` dentro de loop** (linha 110). Anti-padrão.

**P-13 — `dummy diagnostico_id`** atribuído à `Resposta` (linha 113). É descartado depois mas polui o domínio.

**P-14 — Endpoint GET retorna `score=None` sempre** (linha 214) — comentado pelo próprio autor. Significa que o **dashboard nunca mostra o score do diagnóstico que ele mesmo criou** depois de F5.

**P-15 — Geração síncrona de checklist no GET** (linhas 204-207). Stateless, mas inconsistente: dois GETs do mesmo recurso retornam exatamente o mesmo checklist gerado em código — não há persistência. Significa que **mudanças no `consultoria_service` retroagem em diagnósticos antigos**, violando WORM.

---

### 2.5 FRONTEND (Nota 70/100)

#### `package.json`

**F-01 — Dependências fora da stack canônica:**

| Esperado pela INSTRUCAO_KICKOFF | Encontrado |
|---|---|
| Next.js 15 | Next.js **14.2.35** (uma major atrás) |
| tRPC | **ausente** — usa `fetch` cru |
| `@anthropic-ai/sdk` (no front?) | presente — **antipattern**: chamar LLM direto do navegador expõe API key |

**F-02 — `lucide-react@^1.12.0`** está incorreta. A biblioteca está em `^0.x` (a 1.x não existe ainda). Provavelmente quebra `npm install` em algum ambiente.

#### `WizardForm.tsx`

```tsx
// linhas 19-48 — MOCK_QUESTIONS
const MOCK_QUESTIONS = [
  { id: "11111111-...", label: "Sua empresa possui...", options: [...] },
  { id: "22222222-...", label: "Como é feita a apuração...", options: [...] },
  { id: "33333333-...", label: "A empresa já iniciou...", options: [...] },
];
```

**F-03 — Frontend tem o próprio "banco" de perguntas hardcoded** com IDs em sincronia frágil com o backend. Em qualquer ajuste, dessincroniza. Deveria vir de endpoint `/diagnosticos/perguntas?empresa=...`.

**F-04 — Apenas 3 perguntas, 3 opções cada.** O mesmo gap-30+ do backend.

```tsx
// linha 102
const isStepValid = await trigger(fieldsToValidate as any);
```

**F-05 — `as any` no resolver Zod** — perde benefício do type safety.

```tsx
// linhas 105
window.scrollTo({ top: 0, behavior: 'smooth' });
```

**F-06 — Sem guard `typeof window !== 'undefined'`** — em SSR pode quebrar.

#### `lib/api/diagnostico.ts`

```typescript
const MOCK_TENANT_ID = "00000000-0000-0000-0000-000000000001";
```

**F-07 — Tenant ID fixo no Frontend.** Combinado com P-05 (header cleartext), prova que **multi-tenant não foi implementado** — todo cliente que usa o front cai no mesmo tenant.

**F-08 — Sem CSRF / sem JWT.** Apenas o header `X-Tenant-ID`.

#### `lib/schemas/wizard.ts`

```typescript
porte: z.enum(["micro", "pequeno", "medio", "grande", "enterprise"], { ... })
```

**F-09 — Sincronização manual de enums** entre Python (`PorteEmpresa.MEDIO = "medio"`) e Zod. Sem geração automática (OpenAPI codegen, por exemplo). Risco de drift.

**F-10 — Lista de UFs incompleta no select** (linha 267 do WizardForm: `{/* Outros UFs omitidos por brevidade */}`). Funcionário em outro estado não consegue concluir wizard.

---

### 2.6 TESTES (Nota 60/100)

#### Análise quantitativa

- **54 funções de teste** em **10 arquivos**
- Cobertura por tipo:
  - Unit (Domain): test_diagnostico, test_questionario, test_score → **bem coberto**
  - Unit (Application): test_calcular_score_use_case, test_gerar_questionario_adaptativo → **OK**
  - Unit (Infrastructure): test_pdf_generator, test_supabase_repository → **superficial**
  - Unit (Presentation): test_api → **leve**
  - Integration: test_api → **um arquivo apenas**
  - E2E: test_diagnostico_flow → **um arquivo + Playwright separado**

#### Pontos críticos

**T-01 — Cobertura `fail_under = 80`** (pyproject.toml:60) é menor que o exigido pelos princípios (DOMAIN ≥ 85%).

**T-02 — `tests/integration` usa o `app` real** mas sem testcontainers (anti-padrão §10 da INSTRUCAO_KICKOFF: "Mock de DB em integration tests"). Os testes que fazem `POST /diagnosticos/` vão tentar Supabase real.

**T-03 — Teste `test_criar_diagnostico_sem_tenant`** (integration) usa `porte: "EPP"` que **não existe no enum** — esse teste só passa porque o middleware barra antes (status 401).

**T-04 — Sem teste para `consultoria_service`** — exatamente onde está o bug `PorteEmpresa.MEDIA`.

**T-05 — Sem teste de RLS multi-tenant.** O critério de aceitação §14 exige "5 testes integration RLS". Não há nenhum.

**T-06 — Sem teste para `auth_router`.** Login JWT, criação de admin — zero cobertura.

**T-07 — Sem teste de propriedade (property-based) para o motor de score.** Math-heavy code beneficiaria de Hypothesis.

---

### 2.7 CONFIGURAÇÃO / DEVOPS (Nota 68/100)

#### `pyproject.toml`

**Pontos positivos:**
- Python 3.12 declarado
- Stack moderna correta (FastAPI, Pydantic v2, SQLAlchemy 2)
- Lint agressivo (ruff com regras completas)
- mypy strict habilitado
- Coverage configurado

**Pontos a melhorar:**

**C-01 — `langchain-anthropic` declarado mas adapter LLM é Ollama** — deps não usadas

**C-02 — `pybreaker` esperado (anti-padrão menciona) mas não está nas deps**

**C-03 — `testcontainers` ausente** — necessário para integration tests sérios

#### `Dockerfile`

**Pontos positivos:**
- Multi-stage build
- HEALTHCHECK nativo
- Deps de sistema corretas para WeasyPrint (Pango, Cairo)
- `PYTHONUNBUFFERED=1` (boa prática)

**Pontos a melhorar:**

**C-04 — Imagem final ainda contém deps de build** (`build-essential`) porque vem de `base`. Pode-se reduzir 200-300 MB usando `python:3.12-slim` puro no estágio final.

**C-05 — Sem `USER` não-root.** Container roda como root — boa prática moderna é criar `appuser`.

**C-06 — `_DEVELOPER/` não está no contexto** mas `realizar_diagnostico.py` tenta lê-lo (Issue P-08 acima).

#### `docker-compose.yml`

**C-07 — Porta 60322 para Postgres + porta 60000 para API** — diverge da INSTRUCAO_KICKOFF (porta backend 8006). Decisão precisa de ADR.

**C-08 — Frontend `web` instala dependências em runtime** (linha 56) — anti-pattern que deixa o startup lento.

**C-09 — Sem service `mailhog`/`mailpit`** apesar do `email_smtp.py` esperar porta 1025.

#### `Makefile`

Sólido, comandos certos. Apenas:

**C-10 — `migrate:` é placeholder** — sem ferramenta de migração real (Alembic? Supabase CLI?).

#### `INICIAR_APP/iniciar.sh`

Script simples. Funciona localmente mas:

**C-11 — Não usa Docker.** Subir backend via `make dev` (que roda compose) + frontend nativo é inconsistente.

#### Git / commits

**C-12 — Todos os 14 commits em inglês.** Viola §10.8: "PT-BR canônico em commits — `feat(qdi):`". Exemplo concreto:

```
353ab73 feat: implement B2B authentication system with login page, JWT support, and database schema initialization
```

Deveria ser:

```
353ab73 feat(qdi-auth): implementar autenticação B2B com JWT, login e schema DB
```

---

## 3. Aderência aos 12 princípios não-negociáveis

| # | Princípio | Status | Evidência |
|---|---|:---:|---|
| 1 | Multi-tenant dia-1 com RLS | ❌ | RLS quebrado por P-05/P-06 + init.sql sem RLS |
| 2 | Versionamento normativo (`vigencia_inicio/fim`) | ❌ | Pesos hardcoded em código, sem `vigencia_*` |
| 3 | Idempotência em POST | ❌ | Sem `Idempotency-Key` (P-11) |
| 4 | Imutabilidade WORM + SHA-256 | ❌ | Storage com upsert (I-08) e sem hash |
| 5 | Observabilidade OpenTelemetry com `tenant_id` | ❌ | Deps presentes mas zero instrumentação |
| 6 | Recusa controlada (score < 0.65) | ❌ | Sem retriever, sem threshold |
| 7 | Citação obrigatória RAG (sem `evidencia_lexiq` ⇒ 422) | ❌ | LLM Ollama sem citação verificável (I-12) |
| 8 | PT-BR canônico em commits | ❌ | 14/14 commits em inglês (C-12) |
| 9 | Pastas em PT-MAIÚSCULAS | ❌ | Estrutura em minúsculas (`src/`, `domain/`, etc.) |
| 10 | Coverage DOMAIN ≥ 85% | ⚠️ | `fail_under=80`, falta medir DOMAIN específico |
| 11 | Score auditável | ⚠️ | Estrutura existe (`peso_total_aplicado`) mas pesos divergem (A-01) |
| 12 | PDF executivo profissional | ⚠️ | Existe template mas mock-fallback retorna PDF vazio (I-05) |

**Score de aderência: 0/12 plenamente atendidos · 3/12 parcialmente · 9/12 violados**

---

## 4. Pontos fortes consolidados

Apesar das críticas, há fundações boas que devem ser **preservadas**:

1. **Domain bem desenhado** — invariantes, value objects imutáveis, exceções tipadas
2. **Estrutura de pastas Clean Architecture correta** (apenas o caso das letras)
3. **Documentação interna em PT-BR técnico-formal** com analogias Delphi/Winthor — alinhada à persona
4. **pyproject.toml tooling-first** — ruff agressivo, mypy strict, pytest com coverage
5. **Dockerfile multi-stage com WeasyPrint funcional**
6. **Frontend Next.js + Tailwind + shadcn estruturado** com schemas Zod
7. **Volume de testes** (54 funções) já forma uma base
8. **`docs/refs/` curados** (PRD, MoSCoW, Gap Analysis) já no repositório

---

## 5. Conclusão

O projeto `018-QUALIDIAGIQ` é um **MVP funcional rudimentar** que representa cerca de **40-50% do trabalho técnico esperado** para o lançamento de 30/jun/2026, **mas** com pelo menos **8 issues de severidade P0** que se não resolvidas tornam a Onda 1.0 **insegura ou impossível** de defender em uma demo com cliente sério.

A **camada Domain** é a parte mais madura e merece ser usada como fundação. As demais camadas precisam de **refatoração arquitetural significativa** antes da S1.

**Recomendação principal:** intercalar uma **Sprint S0.5 de Hardening** (3 dias úteis, ~16h) entre hoje e o início efetivo da S1 em 04/05/2026 para resolver os P0 e estabelecer ADRs estruturais. Detalhes em `03_PLANO_ACAO_S05_HARDENING.md`.

---

**Autor:** Claude · **Data:** 30/04/2026 · **Próximo documento:** `02_REGISTRO_ISSUES.md`
