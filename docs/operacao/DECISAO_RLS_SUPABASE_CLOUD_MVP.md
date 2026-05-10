# Decisão — evidência RLS: Docker local (primário) vs Supabase cloud (opcional)

**Contexto (G3 / operações):** em **desenvolvimento e evidência MVP no repo**, o caminho **primário** é **Docker Compose** (`make dev`): Postgres **`127.0.0.1:60322`**, API típica **`http://127.0.0.1:60000`**, gates `make mvp-gate` e `make verify-schema-mvp-strict` com `QDI_POSTGRES_TEST_URL` / `DATABASE_URL` apontando para esse Postgres (mesmas migrações que CI).

**Segunda evidência (opcional):** repetir o mesmo critério num **projeto Supabase gerido** antes do **go-live público**, se quiseres parity documentada com hospedagem real — preencher `EVIDENCIA_RLS_DOIS_TENANTS_TEMPLATE.md` e runbook `_DEVELOPER/RUNBOOK_SUPABASE_RLS.md`.

**Estado:** aguardando marcação **[PROD]** / Allan (dispensa ou aceite da segunda evidência).

| Opção | Descrição |
|-------|-----------|
| **A — MVP técnico no repo** | Baseline: Docker Compose + CI; **não** exige login no dashboard Supabase para fechar P6 automatizado. |
| **B — + Cloud pré-go-live** | Além de A: executar runbook cloud + template de evidência antes de abrir tráfego público. |
| **C — Dispensar cloud** | Aceitar só A **com registo explícito** (data, responsável) na checklist Allan. |

**Decisão registada em:** ___ (data) — referência cruzada `docs/operacao/CHECKLIST_CONFIRMACAO_ALLAN_MVP.md`.
