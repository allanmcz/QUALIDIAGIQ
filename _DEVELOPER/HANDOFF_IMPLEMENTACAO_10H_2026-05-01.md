# Handoff — implementação **10 horas** (pós P1–P4)

> **Propósito:** dar sequência ao ciclo **P** (`_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md` §12.3) com **~10 h** de trabalho focado em **P5–P8** + endurecimento operacional.  
> **Pré-requisito:** P1–P4 entregues (2026-05-01); repo verde (`make test`, `make type-check`, front `npm run build` + E2E).

---

## 1. Mapa de tempo (600 min)

| Bloco | Min | ID | Foco | Entrega verificável |
|-------|-----:|-----|------|----------------------|
| **F** | 120 | **P5** | Homologação **M04** + PDF **WeasyPrint** em ambiente próximo à produção | Checklist Allan assinado ou lista de gaps; PDF gerado com dados reais ou fixture homologada |
| **G** | 120 | **P6** | **Supabase produção** — RLS, roles, smoke multi-tenant | `_DEVELOPER/RUNBOOK_SUPABASE_RLS.md` atualizado + 1 sessão `psql`/dashboard validando isolamento |
| **H** | 180 | **P7** | Dashboard **lista real** (`GET /diagnosticos/`) | Remover mock onde aplicável; estados vazio/erro/loading; alinhado ao JWT |
| **I** | 90 | **P8** | Feature flag **normativa no wizard** (`NEXT_PUBLIC_WIZARD_NORMATIVA`) | Passo opcional chama `POST /normativa/validar-ancora`; teste E2E ou smoke manual documentado |
| **J** | 90 | **Extra** | **OpenAPI export** + observabilidade leve | Alvo `make openapi-export` ou script que grave `openapi.json`; correlacionar `trace_id` em 1 fluxo (doc) |

**Total:** 600 min (**10 h**). Ordem recomendada: **H → F → G → I → J** se o produto precisar de UX lista antes de PDF homologado; caso contrário manter **F → G → H** como no HANDOFF original.

---

## 2. Bloco F — P5 M04 / PDF (~2 h)

**Objetivo:** fechar risco “PDF dummy” do critério auditável §12 (relatório executivo real).

**Tarefas sugeridas:**

1. Rodar `make dev`, criar diagnóstico de teste, gerar PDF via fluxo existente (`pdf_generator_weasyprint`).
2. Conferir template Jinja: marcadores **M04** (`test_pdf_template_m04` já existe — estender se Allan apontar lacunas).
3. Documentar no HANDOFF §10 ou `docs/operacao/` o que falta para **homologação contábil** (assinatura, rodapé, versão normativa).

**Critério de pronto:** PDF abre no Acrobat/browser sem erro; conteúdo coerente com GET diagnóstico; gaps listados se houver.

---

## 3. Bloco G — P6 RLS Supabase prod (~2 h)

**Objetivo:** reduzir risco M10 (hardening DB).

**Tarefas:**

1. Revisar políticas `qdi.*` contra checklist **multi-tenant** (JWT `tenant_id`).
2. Executar smoke: dois tenants — A não vê dados de B (via API ou PostgREST).
3. Atualizar `_DEVELOPER/RUNBOOK_SUPABASE_RLS.md` com comandos exatos e **não** commitar segredos.

**Critério de pronto:** runbook testável + evidência de teste (log anonimizado OK).

---

## 4. Bloco H — P7 Dashboard lista real (~3 h)

**Objetivo:** eliminar mock na lista B2B onde ainda existir; usar **`GET /diagnosticos/`** autenticado.

**Tarefas:**

1. `frontend/app/dashboard/page.tsx` (e hooks): fetch com `Authorization` + `NEXT_PUBLIC_API_URL`.
2. Estados: loading skeleton, empty (“nenhum diagnóstico”), erro de rede (toast ou inline).
3. Opcional: paginação se API expõe `limit`/`offset` (já no router).

**Critério de pronto:** lista reflete dados do tenant logado; E2E smoke dashboard ajustado ou novo teste mínimo.

---

## 5. Bloco I — P8 Wizard normativa (~1,5 h)

**Objetivo:** feature flag **S02 leve** — painel “validar âncora” no wizard.

**Tarefas:**

1. Respeitar `NEXT_PUBLIC_WIZARD_NORMATIVA` em `WizardForm.tsx`.
2. POST `/normativa/validar-ancora` com texto do usuário ou template; exibir `valido` / `motivo_rejeicao`.
3. Não persistir decisão sem ADR (checkbox já é local em M12).

**Critério de pronto:** flag desligada = UX atual; ligada = fluxo funcional sem quebrar wizard-post E2E (mock rotas).

---

## 6. Bloco J — OpenAPI export + observabilidade (~1,5 h)

**Objetivo:** documentação exportável para integradores B2B.

**Tarefas:**

1. Script ou alvo Makefile: `curl`/`httpx` contra `app.openapi()` ou `fastapi openapi` em test — gerar `openapi.json` versionado em `docs/api/` (gitignored opcional) ou artefato CI.
2. Documentar em §9 do HANDOFF como regenerar após mudança de rotas.
3. Revisar 1 endpoint crítico com log estruturado + `trace_id` (se OTEL já ligado em dev).

**Critério de pronto:** comando único reproduzível + README curto.

---

## 7. Regras (iguais ao handoff autônomo)

- Sem **push** sem Allan; commits **pt-BR** `feat(qdi-*):`.
- Sem escopo QAI/QFC/QMI.
- Ao final de cada bloco: `make format && make lint && make test`; se tocou front: `npm run build` e E2E relevante.

---

## 8. Prompt para agente

```
Implemente _DEVELOPER/HANDOFF_IMPLEMENTACAO_10H_2026-05-01.md escolhendo a ordem dos blocos conforme a seção 1.

Leia _DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md §12.3 (P5-P8) e §14 (armadilhas).

Entrega: commits atômicos por bloco; atualizar HANDOFF §12.3 com status ao concluir cada P.
```

---

*Versão 1.0 · 2026-05-01*
