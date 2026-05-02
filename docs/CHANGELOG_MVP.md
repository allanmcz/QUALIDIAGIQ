# Changelog — fechamento MVP QualiDiagIQ

Registro de entregas orientadas ao **MVP fechado** (ver `docs/HANDOFF_PLANO_MVP_FECHADO.md`).  
Versões internas podem usar data `YYYY-MM-DD` até adoção de semver de produto.

---

## [Unreleased]

- **Handoff plano 02/05/2026 (execução técnica agente):** `GET /referencia/cnae/subclasses` (JWT + `DATABASE_URL`); wizard com datalist autocomplete CNAE; **`make verify-schema-mvp-strict`** / `--strict-cnae` no script; SQL MVP bloco CNAE opcional; decisões **D1/D3/D5** registadas como adiadas; **D4** parcial. Itens só humanos/externos permanecem: sign-off PDF **P5**, smoke Supabase real **P6**, jurídico, **M08** editorial, Beta SHOULD/COULD.
- **Produção:** aplicar migrações até **0014** (ou **0012** mínimo se CNAE adiado); evidência: **`make verify-schema-mvp`** ou **`make verify-schema-mvp-strict`** + contagens `qdi.cnae_subclasse` (1332); smoke **Supabase** conforme runbook RLS e `docs/operacao/GAP_ANALYSIS_RLS_P6_2026-05-02.md`.
- **P5:** sign-off humano no checklist PDF após revisão visual em ambiente com WeasyPrint (ajustes técnicos Ciclo Q já no template/CSS).

### 2026-05-02 — Ciclo Q (handoff autorizado)

- **CNAE:** migrações **`0013_cnae_referencia.sql`** e **`0014_cnae_seed_dados.sql`**; `init.sql` atualizado.
- **PDF:** síntese executiva com `page-break-inside: avoid`; disclaimer reforçado; margens `@page`.
- **Deploy/D4:** `RUNBOOK_DEPLOY_ROLLBACK.md` (URLs Next); `frontend/.env.production.example`.
- **P6:** relatório de gaps RLS `GAP_ANALYSIS_RLS_P6_2026-05-02.md`.
- **Docs:** `HANDOFF_PROXIMA_SESSAO_QDI.md` sincronizado; `PDF_HOMOLOGACAO_CHECKLIST_B1.md` nota técnica Ciclo Q.

### Adicionado (ferramenta ops)

- `scripts/verify_mvp_schema.py` + alvo **`make verify-schema-mvp`** — checagem somente leitura de colunas **0011/0012**, RLS e `qdi_jwt_tenant_id`.
- `docs/operacao/SQL_VERIFICACAO_SCHEMA_MVP.sql` — mesmo contrato via SQL Editor Supabase.

---

## 2026-05-01 — Gate checklist §6 (automação repo)

### Adicionado

- CI em branches **`release/**`** e tags **`v*`**, **`mvp-*`**.
- **`make mvp-gate`**: smoke API MVP + testes Postgres (`schema` **0012**, RLS dois tenants).
- `docs/legal/STATUS_JURIDICO_MVP.md` — processo jurídico vs parecer externo.
- Marker pytest **`mvp_gate`** e documentação cruzada (`SMOKE_MVP_FECHADO.md`, `PDF_HOMOLOGACAO_CHECKLIST_B1.md`, `HANDOFF_PLANO_MVP_FECHADO.md` §6).

### Alterado

- `MockRepository` (e2e): `listar_por_tenant`, `buscar_por_id` com isolamento por tenant, stubs de PATCH PDF/M12.
- `test_pdf_template_m04.py`: assert do marcador **`M04_SECAO: tecnico_detalhamento_dimensoes`**.
- `DECISOES_PRODUTO_MVP_D1_D5.md`: registro de sincronização do baseline MVP.

---

## 2026-05-01 — LGPD persistido + observabilidade HTTP + WORM aceite

### Adicionado

- Migração **`0012_aceite_lgpd_e_worm.sql`**: coluna `aceite_termos_privacidade_em`; função WORM granular estendida para bloquear mutação do aceite após `finalizado`.
- Contrato API: `IniciarDiagnosticoRequest.aceite_termos_privacidade` (obrigatório `true`); resposta `DiagnosticoResponse.aceite_termos_privacidade_em`.
- Domínio: `Diagnostico.registrar_aceite_termos_privacidade` + uso em `RealizarDiagnostico`.
- Front: `postDiagnostico` envia o payload completo (inclui aceite) para o POST.
- Middleware **`TraceContextMiddleware`**: header `X-Trace-Id` (entrada opcional, saída sempre); `expose_headers` no CORS.
- Documentação operacional do plano MVP: `docs/operacao/SMOKE_MVP_FECHADO.md`, `PDF_HOMOLOGACAO_CHECKLIST_B1.md`, `RUNBOOK_DEPLOY_ROLLBACK.md`, `OBSERVABILIDADE_TRACE_ID.md`, `DECISOES_PRODUTO_MVP_D1_D5.md`.

### Alterado

- `init.sql`: inclusão da migração **0012**.
- Política de privacidade MVP: bullet específico sobre **telefone do respondente** (retenção alinhada ao diagnóstico).

---

## Histórico anterior (consolidado)

Entregas anteriores (M03–M12, P1–P4, idempotência, WORM, M12 PATCH, etc.) permanecem descritas em `docs/HANDOFF_PROXIMA_SESSAO_QDI.md` e commits do repositório.
