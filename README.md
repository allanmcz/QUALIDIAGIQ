<p align="center">
  <img src="./frontend/public/brand/QDI-NB1-logo-completo.jpg" alt="QualiDiagIQ" width="320" />
</p>
<p align="center"><em>Diagnóstico tributário automatizado para a Reforma do Consumo (EC 132/2023, LC 214/2025)</em></p>

# 018-QUALIDIAGIQ — Sandbox de Desenvolvimento

> **Diagnóstico Tributário Automatizado para a Reforma Tributária do Consumo**
> Módulo do ecossistema **Tributiq** · 6 produtos Quali*IQ · `014-SAAS_REFORMA`
> **Sigla:** QDI
> **Status:** MVP desenvolvido (FastAPI + Next.js 14 + Postgres); usar `docs/operacao/CHECKLIST_GO_LIVE_45MIN.md` para cortes em produção.

---

## 🚀 Quickstart

```bash
# 1. Instalar dependências Python
make install

# 2. Subir ambiente Docker (DB + API + Web)
make dev

# 3. Rodar testes
make test

# 4. Abrir interfaces (portas do docker-compose)
# → API: http://localhost:60000/docs (Swagger)
# → Web: http://localhost:60001 (Next.js)
# → DB:  postgres://postgres:postgres@localhost:60322/postgres
```

### Hooks Git (opcional, recomendado)

Após clonar, para ativar `pre-commit` (audit de segredos + gitleaks quando instalado):

```bash
make install-hooks
# macOS: brew install gitleaks
```

Ver também [`docs/operacao/RUNBOOK_SEGREDO_VAZADO.md`](docs/operacao/RUNBOOK_SEGREDO_VAZADO.md) e [`docs/operacao/GITHUB_SECRET_SCANNING.md`](docs/operacao/GITHUB_SECRET_SCANNING.md).

### Ollama local (recomendações IA no diagnóstico)

1. Instale o [Ollama](https://ollama.com) no Mac e deixe o serviço rodando (porta **11434**).
2. Baixe o modelo configurado em `OLLAMA_MODEL`, por exemplo: `ollama pull llama3`.
3. **Onde a API roda importa para a URL:**
   - **`make dev` (API dentro do Docker):** o `docker-compose.yml` já define `OLLAMA_BASE_URL=http://host.docker.internal:11434` para falar com o Ollama no host — não use `127.0.0.1` aí (dentro do container isso não é a sua máquina).
   - **uvicorn no host** (sem container da API): use `OLLAMA_BASE_URL=http://127.0.0.1:11434` no `.env`.

Se o Ollama não estiver disponível, o fluxo de diagnóstico segue com mensagem amigável de fallback na recomendação IA.

**Stack default:** **LangGraph + LangChain (`ChatOllama`)** contra o servidor Ollama — ver **ADR-007**.  
Env opcional: **`QDI_LLM_BACKEND=http_ollama`** — força chamada REST direta (adapter legado `llm_ollama.py`).  
**`OLLAMA_TIMEOUT_SECONDS`** (default `30`) aplica-se ao cliente LangChain ou ao `httpx`, conforme o backend.

**RAG-light (opcional):** com **`DATABASE_URL`** síncrono + **`OPENAI_API_KEY`**, a API usa **`PgvectorBaseNormativaAdapter`** (`qdi_rag.documento_normativo`, migração **0020**). Threshold de similaridade: **`QDI_RAG_SIMILARITY_THRESHOLD`** (default no código em `settings.py`). Ingestão baseline: `PYTHONPATH=. python scripts/ingestao_rag_baseline.py` (fontes em `scripts/normativos_baseline/*.txt`).

### OpenTelemetry (traços)

Ative com **`OTEL_TRACING_ENABLED=true`** e aponte **`OTEL_EXPORTER_OTLP_ENDPOINT`** para um collector OTLP/HTTP (porta típica **4318**, path `/v1/traces`). Exemplo local com [otelcol](https://opentelemetry.io/docs/collector/) em Docker:

```yaml
# excerpt docker-compose.collector.yml — apenas ilustrativo
services:
  otel-collector:
    image: otel/opentelemetry-collector:latest
    command: ["--config=/etc/otelcol.yaml"]
    ports:
      - "4318:4318"
```

Variáveis lidas em runtime: `OTEL_TRACING_ENABLED`, `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS` (formato `chave=valor,chave2=valor2`). Ver `src/infrastructure/config/settings.py`.

### CORS em produção

Use **`CORS_ALLOWED_ORIGINS`** (lista CSV explícita de origens permitidas). **Nunca** `*` com cookies/credentials. Detalhe operacional: [`docs/operacao/CORS_PRODUCAO.md`](docs/operacao/CORS_PRODUCAO.md).

## 📂 Estrutura do Projeto

```
018-QUALIDIAGIQ/
├── .cursorrules                ← Regras Cursor (todas as camadas)
├── .cursor/
│   └── rules/                  ← Rules MDC específicas
│       ├── python-clean-architecture.mdc
│       ├── qdi-domain-context.mdc
│       └── communication-style.mdc
├── .claude/
│   ├── CLAUDE.md               ← Contexto persistente (Claude Code)
│   ├── PROMPT_DIA_1.md         ← Prompt acionável Sprint 1 Dia 1
│   └── settings.json
├── .vscode/                    ← Config VS Code
├── docs/                       ← Produto, operação, changelog (ver docs/README.md)
│   ├── README.md               ← Mapa da documentação versionada
│   ├── 01_arquitetura.md       ← Clean Architecture + Mermaid
│   ├── 02_dominio_qdi.md       ← Entidades, value objects
│   └── refs/                   ← 7 documentos da Discovery (snapshot)
│       ├── 01_PRD_BASE.md
│       ├── 02_MOSCOW_FEATURES.md
│       ├── 03_GAP_ANALYSIS.md
│       ├── 04_METODOLOGIA.md
│       ├── 05_QUESTIONARIO_v1.md   ⭐ banco de 35 perguntas
│       ├── 06_MATRIZ_COMPETITIVA.md
│       └── 07_ESTRATEGIA_GERAL.md
├── _DEVELOPER/                 ← Planos de execução, handoffs (`INDICE_PLANOS_HANDOFF.md`; git add -f)
│   └── 03_roadmap_sprint_1.md  ← Plano dia-a-dia Sprint 1 (30 dias)
├── src/                        ← Backend Python (Clean Architecture)
│   ├── domain/                 ← Regras de negócio puras
│   ├── application/            ← Casos de uso
│   ├── infrastructure/         ← Adapters (Supabase, Ollama/LLM, WeasyPrint)
│   └── presentation/           ← API FastAPI
├── tests/                      ← pytest (unit + integration + e2e)
├── frontend/                   ← Next.js 14 — wizard, painel e páginas institucionais
├── pyproject.toml              ← Dependências Python + tooling
├── Dockerfile                  ← Multi-stage build
├── docker-compose.yml          ← DB + API + Web
└── Makefile                    ← Atalhos (make help)
```

## 🛠️ Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12 + FastAPI 0.115 + Pydantic v2 |
| Frontend | Next.js 14 + Tailwind + shadcn/ui |
| DB | Supabase (PostgreSQL 16 + RLS + pgvector) |
| IA / LLM | **LangGraph + LangChain ChatOllama** + servidor **Ollama** (default dev — ADR-007) · Claude/API produção (ADR-003) · fallback **`QDI_LLM_BACKEND=http_ollama`** |
| PDF | WeasyPrint |
| Container | Docker + OrbStack (M2 Max) |
| Test | pytest + pytest-asyncio + Playwright |
| Lint/Format | ruff + black + mypy strict |

## 🎯 Diferenciais Competitivos

1. **Profundidade quantitativa real** — simulador CBS+IBS+IS por SKU
2. **IA / LLM com RAG** sobre Lexiq versionada
3. **Integração ERP nativa** (Winthor → TOTVS → SAP) — único do mercado
4. **Aderência ABNT NBR 17301:2026** — janela exclusiva (~12 meses)
5. **Benchmark setorial anônimo** — vantagem multi-tenant SaaS

## 💼 Tiers do Produto

| Tier | Preço | Para quem |
|------|-------|-----------|
| **Free** | R$ 0 | Lead magnet — toda PME |
| **Plus** | R$ 297/mês | CFO de PME (R$ 5M-R$ 100M) |
| **Pro** | R$ 997/mês | Empresa média (R$ 100M-R$ 500M) com ERP |
| **Enterprise** | Sob consulta | Escritórios contábeis, consultorias, ICs |

## 🤖 Como Iniciar com Cursor

O Cursor lê **automaticamente** `.cursorrules` + `.cursor/rules/*.mdc` ao abrir o projeto. Você só precisa:

1. Abrir o projeto: `cursor .`
2. Confirmar instalação das extensões recomendadas (popup automático)
3. Iniciar conversa: *"Vamos começar o Sprint 1 Dia 1 conforme `_DEVELOPER/03_roadmap_sprint_1.md`"*

O Cursor já tem contexto completo de:
- Persona dual (Mentor + Arquiteto + Pair Programmer + Instrutor)
- Stack obrigatória (Python 3.12 + FastAPI + Pydantic v2 + Supabase)
- Clean Architecture (4 camadas estritas)
- Padrões editoriais (PT-BR + base legal citada)
- Domínio (Reforma Tributária + ABNT NBR 17301)
- Fora de escopo (QAI, QFC, QMI, RestituIQ — outros módulos)

## 🤖 Como Iniciar com Claude Code

```bash
claude
# Cole o conteúdo de .claude/PROMPT_DIA_1.md na primeira mensagem
```

O Claude Code lê automaticamente `.claude/CLAUDE.md` ao abrir o projeto.

## 📅 Roadmap Sprint 1 (30 dias × 3h/dia)

| Semana | Foco | Features (MoSCoW) |
|--------|------|--------------------|
| **S1** | Setup + Domain | M02 (motor de score) |
| **S2** | Application + Infra | M01 (wizard) + M11 (eixos ABNT) |
| **S3** | Presentation | M07 (recomendações) + M03 (pesos transparentes) |
| **S4** | Output + Lead | M04 (PDF) + M09 (lead magnet) |

**Saída esperada:** API funcional com fluxo questionário → score → relatório PDF.

Detalhes em [`_DEVELOPER/03_roadmap_sprint_1.md`](_DEVELOPER/03_roadmap_sprint_1.md).

## ⚙️ Comandos `make`

```bash
make help            # lista todos os comandos
make install         # cria .venv + instala deps
make dev             # sobe Docker (DB + API + Web)
make test            # roda testes com cobertura
make qa-backend      # lint + mypy + pytest (gate release backend)
make lint            # lint com ruff
make format          # black + ruff format
make type-check      # mypy strict
make migrate         # SQL em src/infrastructure/db/migrations/*.sql no Postgres do `docker compose` (db)
make down            # para Docker
make clean           # limpa .pyc, caches
make frontend-init   # inicializa Next.js (uma vez)
```

### Teste completo local (script)

Ver pasta **[INICIAR_APP/](INICIAR_APP/)** — `./INICIAR_APP/iniciar-app.sh help` (deps, backend, integration, frontend, `full`).

## 🔐 Variáveis de Ambiente

Copie `.env.example` para `.env` e preencha:

```bash
cp .env.example .env
# Edite .env com:
# - OLLAMA_BASE_URL + OLLAMA_MODEL (recomendações IA — subir Ollama local)
# - SUPABASE_URL + chaves (se usar Cloud)
# - SMTP_* para envio de e-mails
# - ANTHROPIC_* quando integrar adapter de produção (ADR-003)
```

## 📚 Documentação

| Doc | Tempo de leitura | Quando consultar |
|-----|-------------------|--------------------|
| [`docs/refs/01_PRD_BASE.md`](docs/refs/01_PRD_BASE.md) | 15 min | Antes de redigir PRD oficial |
| [`docs/refs/02_MOSCOW_FEATURES.md`](docs/refs/02_MOSCOW_FEATURES.md) | 10 min | Para validar escopo |
| [`docs/refs/05_QUESTIONARIO_v1.md`](docs/refs/05_QUESTIONARIO_v1.md) | 20 min | **Essencial** para wizard |
| [`docs/refs/04_METODOLOGIA.md`](docs/refs/04_METODOLOGIA.md) | 15 min | Para implementar use case |
| [`docs/01_arquitetura.md`](docs/01_arquitetura.md) | 10 min | Entender Clean Architecture |
| [`docs/02_dominio_qdi.md`](docs/02_dominio_qdi.md) | 10 min | Entender entidades |
| [`_DEVELOPER/03_roadmap_sprint_1.md`](_DEVELOPER/03_roadmap_sprint_1.md) | 10 min | Plano dia-a-dia |

## 🚫 Fora de Escopo

Estas funcionalidades pertencem a **outros módulos** do ecossistema Tributiq — não implementar aqui:

- Apuração CBS/IBS contínua → **QAI** (QualiApuraIQ)
- Split payment orquestrador → **QFC** (QualiFinCredIQ)
- Auditoria contínua de motores tributários → **QMI** (QualiMixIQ)
- Defesa de autos de infração → fora do ecossistema
- Recuperação ativa de créditos pré-CBS → **RestituIQ** (fora do escopo Reforma)

## 📜 Licença

Proprietary © 2026 Tributiq. Todos os direitos reservados.

## 👤 Mantenedor

**Allan Marcio** — `allanmcz@gmail.com`
Analista de Sistemas + Contador
20+ anos em Delphi + Oracle + ERP Winthor (PC Sistemas/TOTVS)

---

**Próximo passo imediato:**

```bash
# Abrir no Cursor
cursor /Users/allan/GD_TRIBUTOLAB/018-QUALIDIAGIQ
# Ou no VS Code
code /Users/allan/GD_TRIBUTOLAB/018-QUALIDIAGIQ
```

E iniciar o Sprint 1 Dia 1 com pair programming via Cursor (regras carregadas automaticamente) ou Claude Code (cole `PROMPT_DIA_1.md`).
