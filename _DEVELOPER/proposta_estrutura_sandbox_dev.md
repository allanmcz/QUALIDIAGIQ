# Proposta — Estrutura do Sandbox `018-QUALIDIAGIQ` para VS Code + Claude Code

> **Decisão Allan (2026-04-26):** Opção B aprovada — repositório paralelo independente do monorepo principal, mas mantido **dentro de `DIAGNOSTICO_REFORMA_MANUS/`** por enquanto.
> **Status:** scaffold físico criado e pronto para `code .` ou `claude` no diretório.
> **Localização atual:** `DIAGNOSTICO_REFORMA_MANUS/05_PROPOSTA_018_QUALIDIAGIQ/018-QUALIDIAGIQ/`
> **Localização futura (pós-MVP):** `02_PRODUTOS/QDI-DIAGNOSTICO_FISCAL/SRC/` (ADR-004) — promoção condicional após validação.

---

## 1. Resposta Direta

Criei um **scaffold completo** em `018-QUALIDIAGIQ/` com **estrutura Clean Architecture** (Python 3.12 + FastAPI + Next.js + Supabase), **configuração VS Code + Claude Code**, **Docker** pronto para `up -d`, e **stubs de domínio** alinhados ao PRD recomendado em `03_GAP_ANALYSIS_QDI/recomendacoes_prd_qdi.md`. Você pode abrir com `code 018-QUALIDIAGIQ/` ou `claude` e começar a implementar a partir do Sprint 1 (features M01-M03 do MoSCoW).

## 2. Fundamentação & Analogia

Pense neste sandbox como o **ambiente de desenvolvimento de um banco** em uma máquina dedicada — separado do produção (o monorepo `02_PRODUTOS/QDI-DIAGNOSTICO_FISCAL/`) para evitar contaminação de dependências e permitir experimentos rápidos. Quando o módulo se estabilizar, "transportamos" para produção (analogia direta com **Delphi: ambiente RAD local + DLL homologada para o Winthor**).

## 3. Estrutura Criada

```
05_PROPOSTA_018_QUALIDIAGIQ/
├── README.md                                    ← este documento (visão executiva)
├── proposta_estrutura_sandbox_dev.md            ← guia técnico detalhado
└── 018-QUALIDIAGIQ/                              ← scaffold físico real
    ├── README.md                                ← overview do scaffold
    ├── .editorconfig                            ← consistência de editor
    ├── .gitignore                               ← Python + Node + IDE
    ├── .env.example                             ← variáveis de ambiente
    ├── pyproject.toml                           ← Python dependencies + tooling
    ├── Dockerfile                               ← multi-stage build
    ├── docker-compose.yml                       ← Supabase local + API + Web
    ├── Makefile                                 ← atalhos (make dev, make test)
    │
    ├── .vscode/                                 ← config VS Code
    │   ├── settings.json
    │   ├── extensions.json
    │   └── launch.json
    │
    ├── .claude/                                 ← config Claude Code
    │   ├── CLAUDE.md                            ← contexto persistente
    │   └── settings.json
    │
    ├── docs/                                    ← documentação operacional
    │   ├── 00_INDICE.md
    │   ├── 01_arquitetura.md                    ← Clean Arch + diagrama
    │   ├── 02_dominio_qdi.md                    ← entidades + value objects
    │   └── 03_roadmap_sprint_1.md               ← 30 dias detalhados
    │
    ├── src/                                     ← Python backend
    │   ├── domain/                              ← regras de negócio puras
    │   │   ├── entities/diagnostico.py
    │   │   ├── value_objects/score.py
    │   │   └── repositories/diagnostico_repository.py
    │   ├── application/                         ← casos de uso
    │   │   └── use_cases/realizar_diagnostico.py
    │   ├── infrastructure/                      ← adapters, DB, LLM
    │   │   └── repositories/supabase_diagnostico_repository.py
    │   └── presentation/                        ← FastAPI
    │       └── api/main.py
    │
    ├── tests/                                   ← pirâmide de testes
    │   ├── unit/domain/test_diagnostico.py
    │   ├── integration/.gitkeep
    │   └── e2e/.gitkeep
    │
    └── frontend/                                ← Next.js scaffold mínimo
        ├── README.md
        └── (a ser inicializado com `npx create-next-app@14`)
```

## 4. Stack Técnica Confirmada

| Camada | Tecnologia | Por quê |
|--------|-----------|---------|
| **Backend** | Python 3.12 + FastAPI 0.115 + Pydantic v2 | Stack padrão Tributiq (`project_014_saas_reforma.md`) |
| **Frontend** | Next.js 14 (App Router) + Tailwind + shadcn/ui | Maturidade SaaS B2B; alinhado com `web-artifacts-builder` skill |
| **Database** | Supabase (PostgreSQL 16 + RLS + pgvector) | Multi-tenant nativo + base vetorial para RAG |
| **IA / LLM** | Anthropic Claude + LangChain + LangGraph | RAG sobre Lexiq versionada |
| **PDF** | WeasyPrint | Python-native, evita Puppeteer |
| **Container** | Docker + OrbStack (M2 Max) | Stack já validada |
| **Test** | pytest + Playwright | Cobertura unit + e2e |
| **Lint/Format** | ruff + black + mypy | Padrão Python moderno |
| **CI** | GitHub Actions | Quando promovido para `02_PRODUTOS/` |

## 5. Configurações Específicas Criadas

### 5.1. VS Code (`.vscode/`)
- **`settings.json`**: Python interpreter `.venv`, formatter ruff, organize imports on save, EditorConfig respect
- **`extensions.json`**: lista recomendada (Python, Pylance, Ruff, Docker, REST Client, Tailwind CSS IntelliSense, Mermaid Preview)
- **`launch.json`**: 3 perfis de debug (FastAPI dev, pytest current file, pytest all)

### 5.2. Claude Code (`.claude/`)
- **`CLAUDE.md`**: contexto persistente — perfil Allan, stack, padrões Clean Architecture, **link cruzado para o PRD** (`03_GAP_ANALYSIS_QDI/recomendacoes_prd_qdi.md`), MoSCoW resumido, regras editoriais (PT-BR técnico)
- **`settings.json`**: instruções de comportamento (sempre Clean Arch, sempre testes ao gerar código, citação base legal nos comentários quando relevante)

### 5.3. Docker (`docker-compose.yml`)
- **3 serviços iniciais:**
  - `db` — Supabase Postgres + pgvector
  - `api` — FastAPI hot-reload (volumes mounts)
  - `web` — Next.js dev server (hot-reload)
- Rede `qdi-network` interna

### 5.4. Makefile (atalhos rápidos)
```makefile
make install      # cria .venv + instala deps
make dev          # docker-compose up -d
make test         # pytest com cobertura
make lint         # ruff check
make format       # black + ruff format
make migrate      # supabase migration up
make down         # docker-compose down
```

## 6. Como Iniciar o Desenvolvimento

### Caminho 1 — VS Code com Claude Code
```bash
cd /Users/allan/GD_TRIBUTOLAB/014-SAAS_REFORMA/DIAGNOSTICO_REFORMA_MANUS/05_PROPOSTA_018_QUALIDIAGIQ/018-QUALIDIAGIQ
code .
# No VS Code, instalar extensões recomendadas (popup automático)
# Cmd+Shift+P → "Python: Select Interpreter" → ./.venv/bin/python
```

### Caminho 2 — Claude Code direto
```bash
cd /Users/allan/GD_TRIBUTOLAB/014-SAAS_REFORMA/DIAGNOSTICO_REFORMA_MANUS/05_PROPOSTA_018_QUALIDIAGIQ/018-QUALIDIAGIQ
claude
# Claude Code carrega automaticamente .claude/CLAUDE.md como contexto
```

### Caminho 3 — Docker primeiro, código depois
```bash
make install    # primeira vez
make dev        # sobe DB + API + Web
# Acessa http://localhost:8000/docs (Swagger) e http://localhost:3000 (Next.js)
```

## 7. Sprint 1 Sugerido (30 dias × 3h/dia)

Conforme `02_PLANO_EXECUCAO_DUAL_TRACK.md` (arquivado em `99_ARQUIVO/EVOLUCOES/2026-04_DUAL_TRACK/`) e o MoSCoW de `03_GAP_ANALYSIS_QDI/matriz_decisao_features_qdi.md`:

| Semana | Foco | Features |
|--------|------|----------|
| **S1** | Setup + Domain | M02 (motor de score) — entities + value objects + tests |
| **S2** | Application + Infra | M01 (wizard) + M11 (eixos ABNT) — use cases + repositories |
| **S3** | Presentation | M07 (recomendações) + M03 (pesos transparentes) — API endpoints |
| **S4** | Output + Lead | M04 (PDF) + M09 (lead magnet) — WeasyPrint + capture form |

**Saída esperada do Sprint 1:** API funcional com fluxo completo de questionário → score → relatório PDF (sem IA ainda — vem no Sprint 4).

## 8. Decisão Crítica — Promoção para Monorepo

Quando promover de `018-QUALIDIAGIQ/` para `02_PRODUTOS/QDI-DIAGNOSTICO_FISCAL/SRC/`?

**Critérios de promoção (todos obrigatórios):**

- [ ] MVP funcional com 12 features MUST implementadas
- [ ] Cobertura de testes domain layer ≥ 80%
- [ ] Validação com 5 contadores externos (qualitativa)
- [ ] Pelo menos 10 diagnósticos completados em ambiente piloto
- [ ] Score calibrado contra cases de referência
- [ ] ADR-009 (Modelo de Score do QDI) redigida e aceita

**Quando esses 6 critérios estiverem atendidos, executar:**
```bash
# No Mac (sandbox Cowork não opera Git em GD_TRIBUTOLAB)
cd /Users/allan/GD_TRIBUTOLAB/014-SAAS_REFORMA
git mv DIAGNOSTICO_REFORMA_MANUS/05_PROPOSTA_018_QUALIDIAGIQ/018-QUALIDIAGIQ/src/* \
       02_PRODUTOS/QDI-DIAGNOSTICO_FISCAL/SRC/
# + ajustar imports + remover scaffold legado
```

**Até lá**, o sandbox segue como repositório paralelo Git próprio (`git init` dentro de `018-QUALIDIAGIQ/`).

## 9. Riscos e Mitigações

| Risco | Mitigação |
|-------|-----------|
| Drift entre sandbox e topologia ADR-004 | Critério de promoção formal + ADR-009 antes de migrar |
| Dependências do sandbox conflitando com outros produtos | Sandbox tem `pyproject.toml` próprio, ambientes isolados |
| Allan iniciar Sprint 1 sem PRD oficial completo | `recomendacoes_prd_qdi.md` é input suficiente para começar; PRD oficial pode evoluir em paralelo |
| Sandbox crescer demais e ficar inviável de migrar | Manter scope MVP estrito (12 MUST); revisar promoção a cada 30 dias |

## 10. Próximo Passo Sugerido

1. Verificar o scaffold criado: `ls -la 018-QUALIDIAGIQ/`
2. Abrir VS Code: `code 018-QUALIDIAGIQ/`
3. Ler `018-QUALIDIAGIQ/.claude/CLAUDE.md` para entender o contexto pré-carregado
4. Ler `018-QUALIDIAGIQ/docs/03_roadmap_sprint_1.md`
5. Iniciar Sprint 1, Semana 1 — implementar `domain/entities/diagnostico.py` + tests

> **Lembrete:** o scaffold criado é **referência/protótipo**. Ele tem stubs mínimos para você (e o Claude Code) começar imediatamente, mas não está executável de ponta a ponta. As primeiras 8 horas de Sprint 1 serão para validar o ambiente e completar o boilerplate.
