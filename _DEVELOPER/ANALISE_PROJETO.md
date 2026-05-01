# Análise técnica do repositório QualiDiagIQ (snapshot)

Última revisão sintética focada em arquitetura, dependências externas e riscos de operação — complementa o PRD em `docs/refs/`.

## Visão macro (Clean Architecture)

```
src/domain          → Entidades puras (Diagnostico, Pergunta, enums, score VO)
src/application     → Casos de uso + serviços (ConsultoriaService, PDF orchestration conceitual)
src/infrastructure  → Supabase repos, loaders JSON, adapters (LLM, e-mail, WeasyPrint, storage)
src/presentation  → FastAPI, schemas Pydantic v2, middleware idempotência, routers
```

Dependências válidas apenas **para dentro**. O frontend Next.js espelha o contrato HTTP (JWT + Idempotency-Key onde aplicável).

## Stack verificável

| Camada | Escolhas |
| ------ | -------- |
| API | FastAPI, structlog opcional via deps, lifespan para idempotência |
| Persistência | Supabase Postgres + RLS; adapter assíncrono com `asyncio.to_thread` |
| PDF | WeasyPrint + Jinja2 (`src/infrastructure/templates`) |
| Web | Next.js 14 App Router, Tailwind, componentes tipo shadcn, Base UI buttons |
| Testes | pytest + pytest-asyncio; Playwright apenas no frontend |

## Endpoints públicos versus autenticados

- **Públicos (sem Bearer):** `GET /health`, `GET /diagnosticos/metodologia`, `GET /diagnosticos/manifesto-pesos`, `GET /diagnosticos/questionario`, `POST /normativa/validar-ancora`.
- **Autenticados:** `POST /diagnosticos/`, `GET /diagnosticos/` (lista resumida), `GET/PATCH /diagnosticos/{id}` conforme routers.

Confirme CORS (`settings.cors_origins_list`) em deploy real.

## Riscos e dívidas técnicas (honestidade operacional)

1. **Idempotência** depende do middleware + Postgres configurado conforme migrações 0007–0008; ambiente novo sem migrações quebra comportamento esperado pela API.
2. **Cliente Supabase Python síncrono** encapsulado em thread — suficiente para MVP; para throughput alto revisar pooling ou HTTP2 nativo async.
3. **Guardrail Lexiq** em `normativa_router` é heurística; produção deve evoluir para RAG Lexiq conforme roadmap Tributiq.
4. **Dashboard cliente** só carrega dados com JWT válido browser-side; SSO corporativo não modelado aqui.

## Próximo investimento recomendado (fora deste snapshot)

- Testes contratados de OpenAPI contra esquema exportado (`/openapi.json`) no CI.
- Job E2E com API Docker real opcional ao invés só de mocks (mais lentos, maior fidelidade).
- Seeds normativos versionados externamente quando LC 225/2026 ganhar texto estável .

## Base legal produto

Avaliações e metodologia públicas referenciam **LC 214/2025** (previsibilidade do contribuinte) e **ABNT NBR 17301:2026** (compliance tributário estruturado em PDCA).
