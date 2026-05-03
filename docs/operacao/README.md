# Operação — documentação QDI

Índice dos artefactos em `docs/operacao/` (runbooks, gates MVP, decisões de produto). **Planos de execução e handoffs:** `_DEVELOPER/INDICE_PLANOS_HANDOFF.md` — **plano mestre gate MVP:** `_DEVELOPER/HANDOFF_PLANO_MVP_FECHADO.md`.

## Confirmações produto e gates

| Documento | Uso |
|-----------|-----|
| **[CHECKLIST_CONFIRMACAO_ALLAN_MVP.md](./CHECKLIST_CONFIRMACAO_ALLAN_MVP.md)** | Checklist rastreável (Git): mapa *Quem decide / Quem executa*, P5/P6, jurídico, D\*, M02/M03/M08, Beta. |
| [DECISOES_PRODUTO_MVP_D1_D5.md](./DECISOES_PRODUTO_MVP_D1_D5.md) | Registro vivo das decisões D1–D5. |
| [FAIXA_FATURAMENTO_AUTODECLARADA.md](./FAIXA_FATURAMENTO_AUTODECLARADA.md) | Faixa de faturamento opcional: slugs, convenção de limites MVP, LGPD, relação com porte. |
| [STATUS_JURIDICO_MVP.md](../legal/STATUS_JURIDICO_MVP.md) | Processo jurídico MVP (termos/privacidade). |

## Deploy, smoke e schema

| Documento | Uso |
|-----------|-----|
| [RUNBOOK_DEPLOY_ROLLBACK.md](./RUNBOOK_DEPLOY_ROLLBACK.md) | Deploy e rollback. |
| [SMOKE_MVP_FECHADO.md](./SMOKE_MVP_FECHADO.md) | Smoke manual e referência ao gate automatizado. |
| [SQL_VERIFICACAO_SCHEMA_MVP.sql](./SQL_VERIFICACAO_SCHEMA_MVP.sql) | Verificação SQL do schema MVP. |
| [`_DEVELOPER/analises/GAP_ANALYSIS_RLS_P6_2026-05-02.md`](../../_DEVELOPER/analises/GAP_ANALYSIS_RLS_P6_2026-05-02.md) | Análise / evidência RLS (P6) — documento de planeamento. |

## PDF e homologação

| Documento | Uso |
|-----------|-----|
| [PDF_HOMOLOGACAO_CHECKLIST_B1.md](./PDF_HOMOLOGACAO_CHECKLIST_B1.md) | Checklist homologação PDF (P5 / M04). |
| [homologacao_pdf_M04.md](./homologacao_pdf_M04.md) | Notas homologação M04. |
| [WEASYPRINT_RUNTIME.md](./WEASYPRINT_RUNTIME.md) | Runtime WeasyPrint. |

## Observabilidade

| Documento | Uso |
|-----------|-----|
| [OBSERVABILIDADE_TRACE_ID.md](./OBSERVABILIDADE_TRACE_ID.md) | Trace HTTP (`X-Trace-Id`). |
| [OTEL_OTLP_STAGING.md](./OTEL_OTLP_STAGING.md) | OTLP staging (opcional). |

---

Outros ficheiros nesta pasta (auditorias pontuais, notas OpenAPI) mantêm-se como evidência histórica; para onboarding MVP, começar pelo checklist e pelos links acima. **Não** colocar aqui novos planos de sprint ou handoffs de sessão — usar `_DEVELOPER/` (ver [`docs/README.md`](../README.md)).
