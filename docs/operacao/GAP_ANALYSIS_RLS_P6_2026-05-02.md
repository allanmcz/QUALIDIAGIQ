# Gap analysis — RLS / multi-tenant (P6) vs estado do repositório

> **Data:** 2026-05-02  
> **Ciclo:** Q (autorizado Allan) — documento **somente leitura / planeamento**; não substitui execução no projeto Supabase real.

---

## 1. Escopo coberto no código local

| Artefacto | Conteúdo |
|-----------|----------|
| `0002_schema_core.sql` | `public.diagnosticos`, `public.admins` |
| `0003_rls_policies.sql` | RLS em `diagnosticos` via `public.qdi_jwt_tenant_id()` e role `authenticated` |
| `0010_rls_comentarios_documentacao_m10.sql` | Comentários SQL (auditoria) |
| `0013_cnae_referencia.sql` | Schema `qdi.*` — tabelas CNAE + `v_cnae_completo`; RLS **global**: SELECT para `authenticated` em dados de referência; escrita `service_role`; log filtra por `tenant_id` em JWT |
| `0014_cnae_seed_dados.sql` | Carga CNAE 2.3 (validação de contagens) |

---

## 2. Gaps identificados (produção Supabase)

| # | Gap | Risco | Ação sugerida |
|---|-----|-------|----------------|
| G1 | **Duas superfícies RLS:** `public.diagnosticos` (tenant obrigatório) vs `qdi.cnae_*` (referência partilhada) | Baixo para vazamento tenant-a-tenant nos CNAEs (são globais); médio se cliente esperar “tudo isolado por tenant” sem entender modelo | Documentar no onboarding: CNAE é lookup global; diagnósticos permanecem tenant-scoped |
| G2 | **`verify-schema-mvp` / SQL_VERIFICACAO_SCHEMA_MVP** — cobertura CNAE | Fechado no repo (2026-05-02): `make verify-schema-mvp-strict`, flag `--strict-cnae` / env `QDI_VERIFY_SCHEMA_STRICT_CNAE`; SQL MVP com bloco opcional pós-núcleo | Rodar strict em deploy quando 0013/0014 ativos |
| G3 | **JWT claims:** CNAE log usa `request.jwt.claims` → `tenant_id`; alinhado a `0003` mas **não** usa `qdi_jwt_tenant_id()` | Baixo — mesma convenção de claim; divergência futura se renomear função | Manter claims canónicos; considerar VIEW wrapper só se padronizar |
| G4 | **`SECURITY DEFINER` em `fn_importar_cnae_subclasses`** | Médio — revisar GRANT apenas `service_role` (já no DDL); nunca expor a `authenticated` | Auditoria Supabase: pesquisar funções DEFINER em projetos prod |
| G5 | **Bases já criadas** antes de 0013/0014 | Alto se ignorado — CNAE ausente | `make migrate` ou aplicar SQL manualmente na ordem numérica |

---

## 3. Paridade com `_DEVELOPER/RUNBOOK_SUPABASE_RLS.md`

O runbook foca **`public.diagnosticos`** e smoke dois tenants — **continua válido** como teste principal P6. Após 0013:

- Acrescentar à evidência de deploy: `SELECT COUNT(*) FROM qdi.cnae_subclasse` esperado **1332** (pós-seed).
- Confirmar `CREATE EXTENSION pg_trgm` e `pgcrypto` permitidos no projeto (política Supabase).

---

## 4. Próximo passo operacional (fora deste PR)

Checklist curto antes de go-live:

1. Migrações até **0014** aplicadas no projeto alvo.  
2. `verify-schema-mvp` + contagens CNAE (opcional novo assert).  
3. Smoke dois tenants **inalterado** em `diagnosticos`.  
4. Registro de evidência (data, ambiente, versão migrações Git).

---

*Fim do gap analysis P6.*
