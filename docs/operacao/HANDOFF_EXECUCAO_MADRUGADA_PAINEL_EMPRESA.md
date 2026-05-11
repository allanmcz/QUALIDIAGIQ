# Handoff — execução noturna (painel empresa + dívida técnica)

**Versão:** 1.0  
**Data:** 2026-05-11  
**Objetivo:** permitir que um agente ou desenvolvedor execute **sem ambiguidade** o restante trabalho acordado (refactor, testes, UX, âncoras), com critérios de aceite e comandos verificáveis.

**Contexto produto (decisões Allan — não reverter sem ADR):**

- Lista empresa: `GET /diagnosticos/?empresa_cnpj=` (filtro server-side, DV válido).
- Painel `/dashboard/empresas/[cnpj]`: grelha + **expandir** linha; **prefetch** em lotes para ranking global + cache.
- **Carregamento ao expandir:** Opção A — se já houver cache do prefetch, não repetir GET.
- **Dois rankings:** global (média por dimensão nos diagnósticos carregados) + por diagnóstico (igual ficha).
- **M12 editável** na expansão (PATCH `checklist-m12-autoconf` + `If-Match`).
- **PDF e retificações** por diagnóstico; **plano** (cronograma) via atalho ao diagnóstico mais recente + âncora `#m06-cronograma-tabela-heading`; **LGPD** tenant → `/dashboard/privacidade`.
- **Limite:** até **10 000** diagnósticos por CNPJ via paginação client-side (`fetchDiagnosticosResumoTodasPaginasPorEmpresa`).

---

## 1. Estado já entregue no repositório (baseline)

| Área | Local principal |
|------|-----------------|
| API filtro CNPJ | `src/presentation/api/routers/diagnostico_core_router.py` — query `empresa_cnpj` |
| Repos | `listar_por_tenant(..., empresa_cnpj=)` — Postgres / Supabase / CI |
| Lista + páginas empresa | `frontend/lib/api/lista_diagnosticos.ts`, `EmpresaDiagnosticosClient.tsx` |
| Painel expandido | `frontend/components/painel/empresa/EmpresaDiagnosticoExpandedPanel.tsx` |
| Utils scores / M12 | `frontend/lib/painel/diagnostico_scores.ts`, `m12_autoconf_utils.ts` |
| GET detalhe tipado | `frontend/lib/api/fetch_diagnostico_detalhe.ts`, `frontend/types/diagnostico_detalhe.ts` |
| Âncora retificações | `frontend/components/painel/RetificacaoDiagnosticoCard.tsx` — `id="diag-retificacoes"` |

**OpenAPI:** após alterações na API, executar na raiz do repo: `make openapi-export`.

---

## 2. Pacotes de trabalho (ordem recomendada)

### P1 — Refactor `DiagnosticoDetalheClient` (duplicação)

**Objetivo:** passar a importar `normalizarM12DoApi`, `m12EstadoInicialVazio`, `m12ValoresSeCompleto`, `rotuloLikertM12`, `M12_NUM_ITENS` de `frontend/lib/painel/m12_autoconf_utils.ts` e funções de score de `frontend/lib/painel/diagnostico_scores.ts` + `corHeat` / `BAR_GAP_COLORS` onde aplicável.

**Aceite:**

- [x] Remover definições duplicadas locais do ficheiro (sem alterar comportamento visual da ficha).
- [x] `npm run lint` e `npx tsc --noEmit` no `frontend/` sem erros.
- [x] Smoke manual rápido: abrir `/dashboard/diagnosticos/[id]` — radar, rankings, heatmap, M12, quadro iguais ao antes. *(Substituído nesta execução por `npm run build` + E2E mock `empresa-painel-expand`; QA visual opcional.)*

**Risco:** regressão em M12/modais — mitigar testando um PATCH M12 após refactor.

---

### P2 — Testes unitários (funções puras)

**Objetivo:** cobrir `aggregateRankingGapsEmpresa` e `rankingGapsFromScore` (e opcionalmente `radarRowsFromScore`).

**Aceite:**

- [x] Adicionar ficheiro de teste onde o projeto já usa Vitest/Jest; **se não existir runner no front**, usar teste Python em `tests/` que invoque lógica espelhada **não é desejável** — preferir configurar **Vitest** mínimo em `frontend/` ou testes E2E apenas (P3).
- [x] Caso Vitest já esteja em `package.json`, comando documentado na secção 4.

**Nota:** Verificar `frontend/package.json` por `vitest` / `jest`. Se **não** houver, priorizar P3 e criar issue técnica para Vitest.

---

### P3 — E2E Playwright (smoke painel empresa)

**Objetivo:** cenário mínimo: sessão painel → navegar para `/dashboard/empresas/<cnpj14>` → clicar **Expandir** → assert texto visível (`Ranking`, `Radar`, ou `Autoconf`).

**Aceite:**

- [x] Novo spec em `frontend/e2e/` ou pasta existente do projeto.
- [x] Usar dados/seeds já usados noutros e2e (mesmo tenant/CNPJ de teste) — **não** hardcodar secrets.
- [x] `npm run test:e2e` (ou comando existente) documentado abaixo.

**Se ambiente noturno não tiver API:** marcar teste `@skip` ou `test.fixme` com comentário PT-BR.

---

### P4 — UX: estado «agregação global em curso»

**Objetivo:** em `EmpresaDiagnosticosClient.tsx`, quando `diagnosticos.length > 0` mas `Object.keys(detalhesPorId).length < diagnosticos.length`, mostrar linha discreta: *«A consolidar ranking global… (N/M diagnósticos)»*.

**Aceite:**

- [x] Desaparece quando prefetch completa ou mostra aviso se `prefetchErro`.
- [x] Não bloquear interação (expandir linha continua a funcionar).

---

### P5 — Âncora LGPD na ficha do diagnóstico

**Objetivo:** alinhar retificações: adicionar `id="diag-privacidade-lgpd"` (ou nome estável) ao wrapper do `PrivacidadeDiagnosticoCard` na ficha; opcionalmente segundo botão na expansão empresa: *«LGPD deste diagnóstico»* → `/dashboard/diagnosticos/{id}#diag-privacidade-lgpd`.

**Aceite:**

- [x] Scroll com `scroll-mt-*` coerente com header fixo se existir.
- [x] Link na expansão opcional — só se P1 não atrasar.

---

## 3. Fora de escopo neste handoff (não implementar sem novo ADR)

- Novo endpoint backend só para scores agregados.
- Quadro de implantação completo dentro da expansão.
- Alterar regra ADR-013 / CNPJ opcional.

---

## 4. Comandos obrigatórios antes de declarar concluído

Na **raiz** do monorepo (backend):

```bash
make lint
make format
make test
make type-check   # quando mexer em Python
make openapi-export   # se alterar routers/schemas FastAPI
```

No **`frontend/`**:

```bash
npm run lint
npx tsc --noEmit
npm run test:unit   # Vitest — funções puras em lib/painel/diagnostico_scores.test.ts
npm run build       # recomendado antes de merge
```

E2E (se infraestrutura disponível):

```bash
cd frontend && npm run test:e2e
```

---

## 5. Critério de merge (gate)

- [x] Todos os pacotes P1–P5 pretendidos para esta madrugada estão **marcados** na checklist deste doc (copiar para PR).
- [x] CI verde ou justificativa escrita (ex.: E2E skipped por falta de stack).
- [x] Commit mensagem PT-BR: `feat(qdi-front): …` / `refactor(qdi-front): …` / `test(qdi-test): …` conforme `.cursor/rules/commits-pt-br.mdc`.

---

## 6. Referências rápidas

| Tema | Ficheiro |
|------|----------|
| Lista API empresa | `frontend/lib/api/lista_diagnosticos.ts` |
| Prefetch + grelha | `frontend/app/dashboard/empresas/[cnpj]/EmpresaDiagnosticosClient.tsx` |
| Expansão | `frontend/components/painel/empresa/EmpresaDiagnosticoExpandedPanel.tsx` |
| Ficha completa (refactor alvo) | `frontend/app/dashboard/diagnosticos/[id]/DiagnosticoDetalheClient.tsx` |
| LGPD dashboard | `frontend/app/dashboard/privacidade/page.tsx` |

---

## 7. Contacto / decisões

- Decisões de produto travadas na conversa **2026-05-11** (expandir, prefetch, rankings duplos, M12, links PDF/retificações vs plano/LGPD).
- Dúvidas de escopo: **parar** e não inventar — registar em ADR ou perguntar Allan.

---

**Fim do handoff.** Quem executar durante a madrugada deve atualizar este ficheiro com **data**, **executor** e **commit SHA** na secção 2 após cada pacote fechado.

---

## 8. Registo de execução (2026-05-10)

| Campo | Valor |
|-------|-------|
| Data | 2026-05-10 |
| Executor | Cursor Agent (handoff P1–P5) |
| Commit | `79b1c4a4229344724c10b1f417f7e47efc1f0e2e` |

Comandos executados na validação: `make lint`, `make format`, `make test`, `make type-check`; no `frontend/`: `npm run test:unit`, `npm run lint`, `npx tsc --noEmit`, `npm run build`, `npx playwright test e2e/empresa-painel-expand.spec.ts`.

**Pós-handoff (2026-05-10, commit `3eb0932`):** job `frontend-e2e` no CI passou a executar `npm run test:unit`; E2E `empresa-painel-expand` cobre também o atalho «LGPD deste diagnóstico» (mock não intercepta `/dashboard/diagnosticos/…` para não quebrar o RSC do Next).
