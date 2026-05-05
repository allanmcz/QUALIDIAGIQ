# Handoff — Ciclo Q (pós-marca / pré go-live ampliado)

> **Propósito:** plano **versionado** para a próxima janela de trabalho após identidade visual + OG/Twitter + push (`main`).  
> **Data base:** 2026-05-02  
> **Estado:** **EXECUTADO** em 2026-05-02 (autorização “todos os ciclos” no chat).

---

## 1. Contexto já consolidado no repo

- Identidade Tributiq no Next (tokens, `public/brand`, Header/Footer, PDF `style.css` + logo no template).
- Cartões sociais **1200×630** (`opengraph-image` / `twitter-image`, `next/og`).
- Fallback WeasyPrint com **structlog** (sem `print`).
- Decisão **D2** registada: CNPJ obrigatório (`DECISOES_PRODUTO_MVP_D1_D5.md`).
- Ciclo **P1–P4, P7, P8** técnico fechado no handoff canónico; **P5/P6** e jurídico seguem pendentes de operação/sign-off.

---

## 2. Objetivo do Ciclo Q

1. **Alinhar documentação** ao estado real do código (handoff + changelog).  
2. **Preparar go-live** sem inventar decisão de produto: suporte técnico a **P5** (PDF) e **checklist** a **P6** (RLS), onde couber **sem** substituir homologação humana.  
3. **Escolher UMA** frente de fundação opcional (CNAE M1 **ou** endurecimento deploy/D4), conforme autorização em §8.

**Não é objetivo deste ciclo:** QAI/QFC/QMI, billing real (D5), RAG Lexiq integral, versionamento normativo completo no DB.

---

## 3. Blocos propostos (ordem sugerida)

| ID | Bloco | Entrega verificável | Dono da validação |
|----|--------|---------------------|-------------------|
| **Q1** | **Docs sync** | Atualizar `_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md` (snapshot §4/§7/§12: marca, OG, env `NEXT_PUBLIC_SITE_URL`); linha em `docs/CHANGELOG_MVP.md` se acordado release | Allan / revisor |
| **Q2** | **P5 assistido (técnico)** | Percorrer `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md`: corrigir no template/CSS apenas itens **objetivos** (quebra de página, hierarquia Hn, contraste, footer legal); **não** declarar sign-off contábil no código | Allan (sign-off B1) |
| **Q3** | **P6 checklist (técnico)** | Relatório curto em `docs/operacao/` ou ADR: gaps entre `RUNBOOK_SUPABASE_RLS.md` / `_DEVELOPER/RUNBOOK_SUPABASE_RLS.md` e estado desejado; sem aplicar políticas em prod sem credenciais | Ops / Allan |
| **Q4a** | **Trilha CNAE — milestone 1** | Integrar DDL seed CNAE (`_DEVELOPER/CNAE/sql/`) como migração oficial `0013_*.sql` + `init.sql`/Makefile + nota em handoff **ou** ADR “CNAE pós-MVP” se adiar | Allan |
| **Q4b** | **Trilha deploy — D4** | Documentar `NEXT_PUBLIC_SITE_URL`, CORS e URLs canónicas em `RUNBOOK_DEPLOY_ROLLBACK.md` + snippet `.env.production.example` no frontend (sem segredos) | Allan |

**Regra:** executar **Q1 sempre** se o ciclo for autorizado. **Q2–Q3** conforme tempo. **Q4a XOR Q4b** na mesma janela (evitar dispersão).

---

## 4. Critérios de aceite globais (CI)

Antes de declarar o ciclo fechado:

- [ ] `make lint` + `make format` + `make test` + `make type-check` (quando aplicável ao diff).  
- [ ] `cd frontend && npm run lint && npm run build`.  
- [ ] Sem `print()` novo em fluxo API; sem segredos no diff.  
- [ ] Commits **Conventional Commits PT-BR** (`feat(qdi-*):`, `docs(qdi-docs):`, …).

---

## 5. Riscos e armadilhas

| Risco | Mitigação |
|-------|-----------|
| P5 vira “redesign” sem critério | Só itens rastreáveis ao checklist B1; sign-off contábil fora do PR |
| P6 sem acesso Supabase prod | Q3 vira gap analysis documental apenas |
| CNAE aumenta escopo | Manter M1 = DDL + seed + doc; **sem** wizard autocomplete até milestone 2 |
| Alterar handoff canónico demais | Mudanças factuais + data; não reescrever MoSCoW |

---

## 6. Prompt modelo para agente (após autorização)

```text
Ler _DEVELOPER/HANDOFF_CICLO_Q_2026-05-02.md e executar apenas os blocos autorizados em §8.

Branch: feat/qdi-ciclo-q-20260502 (ou nome acordado).

Escopo fechado: não QAI/QFC/QMI; não billing; não push sem Allan.

Ao terminar: make lint; make format; make test; frontend npm run lint && npm run build.
```

---

## 7. Referências obrigatórias

- `_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md`  
- `_DEVELOPER/HANDOFF_PLANO_MVP_FECHADO.md`  
- `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md`  
- `_DEVELOPER/RUNBOOK_SUPABASE_RLS.md` / `docs/operacao/RUNBOOK_DEPLOY_ROLLBACK.md`  
- `_DEVELOPER/CNAE/README.md` (se Q4a)  
- `docs/operacao/DECISOES_PRODUTO_MVP_D1_D5.md`

---

## 8. Autorização (registro)

| Bloco | Estado |
|-------|--------|
| **Q1** | Feito — `HANDOFF_PROXIMA_SESSAO_QDI.md`, `CHANGELOG_MVP.md` |
| **Q2** | Feito — template PDF + `PDF_HOMOLOGACAO_CHECKLIST_B1.md` |
| **Q3** | Feito — `_DEVELOPER/analises/GAP_ANALYSIS_RLS_P6_2026-05-02.md` |
| **Q4a** | Feito — `0013` + `0014` + `init.sql` |
| **Q4b** | Feito — `RUNBOOK_DEPLOY_ROLLBACK.md`, `frontend/.env.production.example` |

**Chat:** autorização “todos os ciclos” (inclui **Q4a** e **Q4b** na mesma janela).

---

*Fim do plano Ciclo Q.*
