# Handoff P1–P8 (implementação consolidada)

Referência normativa geral do produto: **EC 132/2023**, **LC 214/2025**, **ABNT NBR 17301:2026**.

## P1 — OpenAPI exportável / exemplos

- `POST /diagnosticos/` aceita exemplos Swagger via `Body(openapi_examples=...)`  
  Fonte: `src/presentation/api/openapi_examples.py`
- `POST /normativa/validar-ancora` com os mesmos exemplos.
- `GET /diagnosticos/manifesto-pesos` ganhou `example` no schema (`ManifestoPesosResponse`).

## P2 — CI GitHub Actions

Workflow: `.github/workflows/ci.yml`

- Job **backend:** `pip install -e ".[dev]"`, `ruff`, `mypy src`, `pytest`.
- Job **frontend-e2e:** `npm ci`, `npm run lint`, Playwright apenas Chromium nos testes da pasta `frontend/e2e`.

## P3 — Botão `asChild` sem vazar ao DOM

- `frontend/components/ui/button.tsx` intercepta `asChild` e aplica classes via `cloneElement` no filho único (ex.: `next/link`).
- Props encaminhadas ao `@base-ui/react/button` já não incluem `asChild` inválido no `<button>`.

## P4 — Catálogo 37 × documentação

- `docs/refs/05_QUESTIONARIO_v1.md`: seção inicial e §15 alinhadas a **37 perguntas** (`perguntas_mvp.json` / manifesto **v1-doc-05-full-37**).

## P5 — PDF (M04) checklist com score

- `WeasyPrintPdfGenerator.gerar_pdf_diagnostico` já chama  
  `ConsultoriaService.gerar_checklist(diagnostico, score)` (frentes M07 coerentes com frente anterior).

## P6/P10 — RLS endurecimento documental

- Migração `src/infrastructure/db/migrations/0010_rls_comentarios_documentacao_m10.sql` — somente `COMMENT` em políticas + função `qdi_jwt_tenant_id()`.

## P7 — Dashboard com lista real

- API: `GET /diagnosticos/?limit=&offset=` (JWT), resposta `list[DiagnosticoResumoSchema]`.
- Repo: ordenação por `criado_em` descendente (`SupabaseDiagnosticoRepository.listar_por_tenant`).
- Front: `frontend/lib/api/lista_diagnosticos.ts` + `frontend/app/dashboard/page.tsx` (sem mock).

## P8 — Wizard + normativa (feature flag)

- Variável opcional no front: `NEXT_PUBLIC_WIZARD_NORMATIVA=true`
- Painel no passo 3 chama `POST /normativa/validar-ancora` através de `frontend/lib/api/normativa.ts`.

## Dev Playwright porta 3333

- `frontend/next.config.mjs` usa `allowedDevOrigins` para `127.0.0.1:3333` / `localhost:3333`.
