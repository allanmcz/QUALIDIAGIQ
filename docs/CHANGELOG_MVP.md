# Changelog — fechamento MVP QualiDiagIQ

Registro de entregas orientadas ao **MVP fechado** (ver `_DEVELOPER/HANDOFF_PLANO_MVP_FECHADO.md`).  
Versões internas podem usar data `YYYY-MM-DD` até adoção de semver de produto.

---

## [Unreleased]

- **Jurídico (2026-05-07):** parecer formal arquivado em `docs/legal/` (`PARECER JURÍDICO - QualiDiagIQ_7242.pdf`); `STATUS_JURIDICO_MVP.md` atualizado; **aprovação produto** da minuta `/termos` e `/privacidade` registada; pasta `docs/legal/` versionada (`.gitignore`); checklist Allan — parecer + aprovação produto.
- **DPO (2026-05-07):** secção pública `#dpo` em `/privacidade`, helper `frontend/lib/legal/dpoPublic.ts`, env `NEXT_PUBLIC_LGPD_DPO_*`, link no rodapé, `docker-compose` serviço `web` com e-mail de exemplo.
- **Plano `FALTA_IMPLEMENTAR.md` (2026-05-04) — entregas [ENG]:** documentação operacional (`CORS_PRODUCAO`, checklist RLS, idempotência/OpenAPI, eventos de log, template evidência RLS, decisão Supabase cloud); CI **auditoria segredos** (`scripts/audit_secrets.sh`); `scripts/export_manifesto_pesos_md.py` + `docs/refs/MANIFESTO_PESOS_EXPORTADO.md`; fixture `tests/fixtures/calibracao_m02_casos.json` + teste estrutural; testes `test_llm_ollama_adapter_http.py`; README CORS; painel diagnósticos com `aria-live` em estados; handoff com migrações até **0027**. Itens **[OPS]/[EXT]/[PROD]** (P5 PDF, P6 cloud, jurídico, tag Git) permanecem humanos.
- **MVP-D (2026-05-05):** handoff cenário **demo local** — [`_DEVELOPER/MVP_05052026/HANDOFF_PLANO_EXECUCAO_MVP_05052026.md`](../_DEVELOPER/MVP_05052026/HANDOFF_PLANO_EXECUCAO_MVP_05052026.md) executado; gates `make test`, `make mvp-gate`, `make verify-schema-mvp-strict`; subset **`PDF_HOMOLOGACAO_CHECKLIST_B1`** MVP-D; roteiro **`_DEVELOPER/MVP_05052026/07_ROTEIRO_DEMO.md`**; `HANDOFF_PROXIMA` §12.3 + `SMOKE_MVP_FECHADO` registo. **Sem** tag semver (opcional cenário D).
- **IA:** stack **LangGraph + LangChain (`langchain-ollama` ChatOllama) + servidor Ollama** como default da recomendação no diagnóstico (**ADR-007**); fallback ``QDI_LLM_BACKEND=http_ollama`` (REST legado).

---

## [1.0.0] — MVP QualiDiagIQ — 2026

**Momento:** ano **2026** · **Número de release:** **1.0** (semver da tag: **`v1.0.0`**).  
Alinha ao checklist Allan — secção 1 (tag/release MVP + changelog).

### Resumo executivo do baseline nomeado

- **Handoff plano 02/05/2026 (execução técnica agente):** `GET /referencia/cnae/subclasses` (JWT + `DATABASE_URL`); wizard com datalist autocomplete CNAE; **`make verify-schema-mvp-strict`** / `--strict-cnae` no script; SQL MVP bloco CNAE opcional; decisões **D1/D3/D5** registadas como adiadas; **D4** parcial. Itens só humanos/externos permanecem: sign-off PDF **P5**, smoke Supabase real **P6**, jurídico, **M08** editorial, Beta SHOULD/COULD.
- **Produção:** aplicar migrações até **0015** para pesos macro em DB (ou **0014** se CNAE + **0012** mínimo conforme operação); evidência: **`make verify-schema-mvp`** ou **`make verify-schema-mvp-strict`** + contagens `qdi.cnae_subclasse` (1332) quando CNAE ativo; smoke **Supabase** conforme runbook RLS e `_DEVELOPER/analises/GAP_ANALYSIS_RLS_P6_2026-05-02.md`.
- **P5:** sign-off humano no checklist PDF após revisão visual em ambiente com WeasyPrint (ajustes técnicos Ciclo Q já no template/CSS).

### 2026-05-02 — Ciclo Q (handoff autorizado)

- **CNAE:** migrações **`0013_cnae_referencia.sql`** e **`0014_cnae_seed_dados.sql`**; `init.sql` atualizado.
- **PDF:** síntese executiva com `page-break-inside: avoid`; disclaimer reforçado; margens `@page`.
- **Deploy/D4:** `RUNBOOK_DEPLOY_ROLLBACK.md` (URLs Next); `frontend/.env.production.example`.
- **P6:** relatório de gaps RLS `_DEVELOPER/analises/GAP_ANALYSIS_RLS_P6_2026-05-02.md`.
- **Docs:** `_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md` sincronizado; `PDF_HOMOLOGACAO_CHECKLIST_B1.md` nota técnica Ciclo Q.

### Adicionado (ferramenta ops)

- `scripts/verify_mvp_schema.py` + alvo **`make verify-schema-mvp`** — checagem somente leitura de colunas **0011/0012**, RLS e `qdi_jwt_tenant_id`.
- `docs/operacao/SQL_VERIFICACAO_SCHEMA_MVP.sql` — mesmo contrato via SQL Editor Supabase.

### Pós-Ciclo Q — backlog autónomo 02/05/2026 (engenharia)

- Migração **`0015`** (pesos macro `qdi.normativa_score_macro_dimensao`); `init.sql`; endpoints metodologia/manifesto com Postgres quando `DATABASE_URL`; CI `verify-schema-mvp-strict`; Ollama `OLLAMA_TIMEOUT_SECONDS`; ADR-006 deps IA; pilares **Q-ABNT-*** no catálogo; E2E `wizard-edge-cases`; `docs/operacao/` versionado no Git.

---

## 2026-05-01 — Gate checklist §6 (automação repo)

### Adicionado

- CI em branches **`release/**`** e tags **`v*`**, **`mvp-*`**.
- **`make mvp-gate`**: smoke API MVP + testes Postgres (`schema` **0012**, RLS dois tenants).
- `docs/legal/STATUS_JURIDICO_MVP.md` — processo jurídico vs parecer externo.
- Marker pytest **`mvp_gate`** e documentação cruzada (`SMOKE_MVP_FECHADO.md`, `PDF_HOMOLOGACAO_CHECKLIST_B1.md`, `_DEVELOPER/HANDOFF_PLANO_MVP_FECHADO.md` §6).

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

Entregas anteriores (M03–M12, P1–P4, idempotência, WORM, M12 PATCH, etc.) permanecem descritas em `_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md` e commits do repositório.
