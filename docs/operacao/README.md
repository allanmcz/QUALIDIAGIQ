# Operação — documentação QDI

Índice dos artefactos em `docs/operacao/` (runbooks, gates MVP, decisões de produto). **Planos de execução e handoffs:** `_DEVELOPER/INDICE_PLANOS_HANDOFF.md` — **plano mestre gate MVP:** `_DEVELOPER/HANDOFF_PLANO_MVP_FECHADO.md`.

## Confirmações produto e gates

| Documento | Uso |
|-----------|-----|
| **[CHECKLIST_CONFIRMACAO_ALLAN_MVP.md](./CHECKLIST_CONFIRMACAO_ALLAN_MVP.md)** | Checklist rastreável (Git): mapa *Quem decide / Quem executa*, P5/P6, jurídico, D\*, M02/M03/M08, Beta. |
| [MVP_CRITERIO_CORTE_E_DECLARACAO_MUST.md](./MVP_CRITERIO_CORTE_E_DECLARACAO_MUST.md) | Template ACT-K01 / ACT-K03 — critério de corte e declaração MUST. |
| [DECISAO_RLS_SUPABASE_CLOUD_MVP.md](./DECISAO_RLS_SUPABASE_CLOUD_MVP.md) | Decisão evidência RLS cloud vs apenas CI (placeholder). |
| [EVIDENCIA_RLS_DOIS_TENANTS_TEMPLATE.md](./EVIDENCIA_RLS_DOIS_TENANTS_TEMPLATE.md) | Template OPS para evidência P6. |
| [DECISOES_PRODUTO_MVP_D1_D5.md](./DECISOES_PRODUTO_MVP_D1_D5.md) | Registro vivo das decisões D1–D5. |
| [FAIXA_FATURAMENTO_AUTODECLARADA.md](./FAIXA_FATURAMENTO_AUTODECLARADA.md) | Faixa de faturamento opcional: slugs, convenção de limites MVP, LGPD, relação com porte. |
| [STATUS_JURIDICO_MVP.md](../legal/STATUS_JURIDICO_MVP.md) | Processo jurídico MVP (termos/privacidade). |
| [HANDOFF_DPO_RIPD_TEMPLATE.md](./HANDOFF_DPO_RIPD_TEMPLATE.md) | Template DPO / RIPD / workshop WORM×LGPD (handoff). |

## Deploy, smoke e schema

| Documento | Uso |
|-----------|-----|
| [CHECKLIST_GO_LIVE_45MIN.md](./CHECKLIST_GO_LIVE_45MIN.md) | Cutover rápido (~45 min): pré-voo, ordem deploy, smoke, rollback express. Inclui execução via `make go-live`. |
| [CORS_PRODUCAO.md](./CORS_PRODUCAO.md) | Variável `CORS_ALLOWED_ORIGINS` e anti-padrão `*` + credentials. |
| [RLS_TABELAS_CHECKLIST_MVP.md](./RLS_TABELAS_CHECKLIST_MVP.md) | Índice de tabelas/políticas RLS (referência às migrações). |
| [POSTS_IDEMPOTENCIA_E_OPENAPI.md](./POSTS_IDEMPOTENCIA_E_OPENAPI.md) | Lista branca de POST com `Idempotency-Key` (diagnosticos*, CNPJ, `/diagnosticos/.../retificacao`). |
| [RUNBOOK_DEPLOY_ROLLBACK.md](./RUNBOOK_DEPLOY_ROLLBACK.md) | Deploy e rollback. |
| [SMOKE_MVP_FECHADO.md](./SMOKE_MVP_FECHADO.md) | Smoke manual e referência ao gate automatizado. |
| [SQL_VERIFICACAO_SCHEMA_MVP.sql](./SQL_VERIFICACAO_SCHEMA_MVP.sql) | Verificação SQL do schema MVP. |
| [`_DEVELOPER/analises/GAP_ANALYSIS_RLS_P6_2026-05-02.md`](../../_DEVELOPER/analises/GAP_ANALYSIS_RLS_P6_2026-05-02.md) | Análise / evidência RLS (P6) — documento de planeamento. |

## Planeamento compliance e PWA (handoff)

| Documento | Uso |
|-----------|-----|
| [PLANO_HANDOFF_JANELA_23H_LGPD_PWA.md](./PLANO_HANDOFF_JANELA_23H_LGPD_PWA.md) | Fatias acionáveis **LGPD técnico + PWA** numa janela curta; liga a ADR-011 e ADR-012. |
| [ROADMAP_HANDOFF_PROGRESSO_SYNC.md](./ROADMAP_HANDOFF_PROGRESSO_SYNC.md) | Espelho versionável do painel do roadmap em `_DEVELOPER/` (Git). |
| [RUNBOOK_DIREITOS_TITULAR_RASCUNHO.md](./RUNBOOK_DIREITOS_TITULAR_RASCUNHO.md) | Runbook art. 18 (processo DPO) + rotas `/privacidade/solicitacoes` e testes `test_privacidade_api`. |
| [OPENAPI_DIFF_INSTRUCOES.md](./OPENAPI_DIFF_INSTRUCOES.md) | Contrato **`docs/api/openapi.generated.json`** (`make openapi-export`), diff opcional contra `/openapi.json`; CI bloqueia drift. |

## PDF e homologação

| Documento | Uso |
|-----------|-----|
| [PDF_HOMOLOGACAO_CHECKLIST_B1.md](./PDF_HOMOLOGACAO_CHECKLIST_B1.md) | Checklist homologação PDF (P5 / M04). |
| [homologacao_pdf_M04.md](./homologacao_pdf_M04.md) | Notas homologação M04. |
| [WEASYPRINT_RUNTIME.md](./WEASYPRINT_RUNTIME.md) | Runtime WeasyPrint. |

## Observabilidade

| Documento | Uso |
|-----------|-----|
| [EVENTOS_NEGOCIO_LOGS.md](./EVENTOS_NEGOCIO_LOGS.md) | Eventos de negócio recomendados + correlação. |
| [OBSERVABILIDADE_TRACE_ID.md](./OBSERVABILIDADE_TRACE_ID.md) | Trace HTTP (`X-Trace-Id`). |
| [OTEL_OTLP_STAGING.md](./OTEL_OTLP_STAGING.md) | OTLP staging (opcional). |

---

Outros ficheiros nesta pasta (auditorias pontuais, notas OpenAPI) mantêm-se como evidência histórica; para onboarding MVP, começar pelo checklist e pelos links acima. **Não** colocar aqui novos planos de sprint ou handoffs de sessão — usar `_DEVELOPER/` (ver [`docs/README.md`](../README.md)).
