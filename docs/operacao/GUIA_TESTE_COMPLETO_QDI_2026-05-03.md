# Guia de teste completo — QualiDiagIQ (sessão única)

> **Data:** 2026-05-03  
> **Objetivo:** validar **API**, **Postgres** (migrações + RAG opcional), **Next.js** e **fluxos críticos** (wizard, idempotência, dashboard M05/M06/M12) num mesmo dia, com comandos copy-paste.  
> **Não cobre:** sign-off PDF Allan, smoke Supabase cloud de produção, decisões M09/M02 (ver `docs/operacao/CHECKLIST_CONFIRMACAO_ALLAN_MVP.md`).

---

## 0. Pré-requisitos

| Requisito | Verificação |
|-----------|-------------|
| Docker (OrbStack / Docker Desktop) | `docker version` |
| Node 20+ | `node -v` |
| Python 3.12+ e venv do projeto | `make install` (uma vez) |
| Ollama local (opcional — recomendações IA) | `curl -s http://127.0.0.1:11434/api/tags` |

Portas padrão deste repositório (`make dev`): **API 60000**, **Web 60001**, **Postgres 60322**.

---

## 1. Arranque do ambiente

```bash
cd /caminho/018-QUALIDIAGIQ
make down
make dev
```

Aguarde a API responder:

```bash
curl -sSf http://127.0.0.1:60000/health | head -c 200
```

Migrações (se o volume DB for novo ou após pull com SQL novo):

```bash
make migrate
```

---

## 2. Qualidade backend (obrigatório antes de PR / release)

```bash
make format
make lint
make type-check
make test
make test-domain
make audit-secrets
make audit-catalogo
```

**Gate schema** (com Postgres local do compose; ajuste URL se necessário):

```bash
export QDI_POSTGRES_TEST_URL='postgresql://postgres:postgres@127.0.0.1:60322/postgres'
QDI_VERIFY_SCHEMA_STRICT_CNAE=1 python scripts/verify_mvp_schema.py
QDI_VERIFY_SCHEMA_RAG=1 python scripts/verify_mvp_schema.py
```

---

## 3. RAG-light opcional (pgvector + OpenAI)

Só se tiver `OPENAI_API_KEY` e `DATABASE_URL` síncrono configurados na API.

```bash
PYTHONPATH=. OPENAI_API_KEY=sk-... DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:60322/postgres \
  python scripts/ingestao_rag_baseline.py
```

Dry-run (sem API nem DB write):

```bash
PYTHONPATH=. python scripts/ingestao_rag_baseline.py --dry-run
```

---

## 4. OpenTelemetry (opcional)

Ver [`OTEL_QUICKSTART_LOCAL.md`](./OTEL_QUICKSTART_LOCAL.md). Exemplo mínimo no `.env` da API:

```bash
OTEL_TRACING_ENABLED=true
OTEL_SERVICE_NAME=qualidiagiq-api-dev
OTEL_EXPORTER_OTLP_ENDPOINT=http://127.0.0.1:4318
```

Reinicie a API após alterar `.env`.

---

## 5. Frontend — build e lint

```bash
cd frontend
npm ci
npm run lint
npm run build
```

---

## 6. Playwright (E2E)

Na **raiz** do repositório, com Next a subir automaticamente (porta 3333 por defeito):

```bash
cd frontend
npm run test:e2e
```

Cenários relevantes ao handoff **2026-05-03**:

| Ficheiro | O quê |
|----------|--------|
| `e2e/wizard-edge-cases.spec.ts` | Múltipla sem rótulos, **catálogo `multipla_total` inválido**, voltar entre passos |
| `e2e/wizard-post.spec.ts` | Contrato wizard → POST |
| `e2e/smoke.spec.ts` | Smoke rápido |
| `e2e/a11y-critical.spec.ts` | Axe em rotas críticas |

E2E integrado (API real + Postgres — requer env; ver `frontend/README.md`):

```bash
PLAYWRIGHT_INTEGRATED=1 npm run test:e2e:integrado
```

---

## 7. Testes manuais no browser (checklist curto)

1. **Landing / wizard anónimo:** `http://127.0.0.1:60001/wizard` — preencher lead, LGPD, perfil, responder perguntas; se catálogo mockado com erro, ver mensagem **Catálogo incompleto** (E2E cobre caso sintético).
2. **Login na plataforma:** `http://127.0.0.1:60001/login` — credenciais de dev conforme `.env` / seed do projeto.
3. **Dashboard lista:** `/dashboard` — lista diagnósticos.
4. **Detalhe M05/M06/M12:** `/dashboard/diagnosticos/{id}` — radar, ranking de gaps, cronograma + timeline, checklist ABNT com **If-Match** ao marcar itens.
5. **Metodologia pública:** `/metodologia` e API `GET /diagnosticos/metodologia` + `manifesto-pesos` (com `DATABASE_URL` na API para ler **0015**).
6. **Idempotência:** repetir `POST /diagnosticos/` com mesmo `Idempotency-Key` e Bearer — segunda resposta com header `X-Idempotent-Replay: true` (testes automatizados em `tests/unit/presentation/test_idempotency_middleware.py`).

---

## 8. Swagger / contratos

- `http://127.0.0.1:60000/docs` — validar schemas e headers (`Authorization`, `Idempotency-Key` em POST).

---

## 9. Referências cruzadas

| Documento | Uso |
|-----------|-----|
| [`HANDOFF_PROXIMA_SESSAO_QDI.md`](../../_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md) | Estado técnico completo |
| [`RUNBOOK_DEPLOY_ROLLBACK.md`](./RUNBOOK_DEPLOY_ROLLBACK.md) | Release e rollback |
| [`SMOKE_MVP_FECHADO.md`](./SMOKE_MVP_FECHADO.md) | Smoke operacional |
| [`HANDOFF_PLANO_EXECUCAO_2026-05-03.md`](../../_DEVELOPER/_CONCLUIDOS_DEV/HANDOFF_PLANO_EXECUCAO_2026-05-03.md) | Plano HANDOFF executado (arquivo em `_DEVELOPER/_CONCLUIDOS_DEV/`) |

---

*Fim do guia — bom teste.*
