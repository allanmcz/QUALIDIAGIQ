# Avaliação concreta — MVP **100%** até **2026-05-05**

> **Data do documento:** 2026-05-03  
> **Base normativa de produto (metodologia):** EC 132/2023, LC 214/2025, ABNT NBR 17301:2026 (aderência como *diferencial* do QDI — o “100%” aqui é **operacional de MVP**, não certificação ABNT).

---

## 1. Duas definições de “100%” (evitar ambiguidade)

| Definição | Significado | Realista até 05-05-2026? |
|-----------|-------------|-------------------------|
| **A — MVP 100% técnico (repositório + ambiente espelho)** | CI verde, `make mvp-gate`, PDF WeasyPrint gerado em ambiente espelho com dados representativos, migrações aplicadas no alvo acordado, RLS dois tenants **comprovado** no mesmo motor PG das migrações (Docker/CI ou Supabase self-hosted equivalente). **Tag Git + linha em `docs/CHANGELOG_MVP.md`.** | **Sim**, se P5 (checklist B1 + evidências) e deploy/espelho forem prioridade absoluta **03–05/05** e decisões D* forem fechadas ou explicitamente adiadas. |
| **B — MVP 100% lançável institucional** | Tudo em **A** **mais:** parecer jurídico formal **`/termos`** + **`/privacidade`**, política retenção telefone/DPO alinhada, **opcional** evidência RLS no projeto Supabase **cloud** (se não dispensada), critérios MoSCoW “comercial” (ex.: **3 contadores externos** no PDF — ver checklist sec. 5) se mantiveres como obrigatório. | **Parcialmente arriscado** em 48–72 h: depende de **advogado** e de **terceiros**; para 05-05 costuma exigir **corte explícito** (“MVP técnico + jurídico mínimo” vs “MVP marketing com 3 pareceres externos”). |

**Recomendação:** para **05-05-2026**, fixar por escrito qual alvo é o **commitment** (**A** ou **B**). O resto deste pacote assume que o mínimo negociável é **A**, com **B** como stretch onde houver capacidade humana.

---

## 2. Estado já consolidado (não reabrir sem regressão)

| Área | Evidência / rasto |
|------|-------------------|
| MoSCoW MUST M01–M12 (código) | `_DEVELOPER/HANDOFF_PROXIMA_SESSAO_QDI.md` §12.2 |
| P1–P4, P7, P8 | Idem §12.3 — **feitos** |
| RLS dois tenants automatizado (Postgres migrações repo) | `make mvp-gate`, `tests/integration/test_mvp_gate_postgres.py` — checklist **[x]** 2026-05-02 |
| Migrações **0015** e **0016** no ambiente alvo | Checklist confirmado Allan |
| LGPD timestamp + WORM (D7) | Migração **0012** + handoff |
| Auditoria catálogo 37×35 (P4) | Script + `docs/operacao/auditoria_catalogo_vs_pr_v1_2026-05-01.md` |

---

## 3. Gaps que **bloqueiam** ou **desqualificam** “100% técnico (A)”

| ID | Gap | Porquê importa | Dono principal | Esforço relativo |
|----|-----|----------------|------------------|------------------|
| **G-P5a** | Checklist **B1** PDF sem itens objetivos fechados + registo no `PDF_HOMOLOGACAO_CHECKLIST_B1.md` | Plano mestre §6 — sem isto não há “MVP fechado” auditável no eixo PDF | Allan (+ Eng espelho) | Médio |
| **G-P5b** | Ambiente **espelho** WeasyPrint (fontes, env, paridade com runbook) sem evidência | B.3 do plano MVP — “PDF real” vs surpresa em prod | Ops / Eng | Médio |
| **G-A1** | **Sem tag** + **sem entrada** `CHANGELOG_MVP` de release | Congelamento A.1 — não há marco Git reprodutível | Allan / release manager | Baixo após decisão de nome |
| **G-D4** | URL canónica **não assinada** (CORS, `NEXT_PUBLIC_*`, DNS) | Risco de quebra silenciosa em wizard/API em prod | Allan + Ops | Baixo a médio |

---

## 4. Gaps que **bloqueiam** “100% institucional (B)”

| ID | Gap | Dono |
|----|-----|------|
| **G-J1** | Parecer **`/termos`** e **`/privacidade`** pendente | Jurídico externo |
| **G-J2** | Retenção telefone + DPO / titular sem texto fechado | Jurídico + Allan |
| **G-MKT** | Critério MoSCoW **3 contadores externos** (sec. 5 checklist) se mantido como MUST comercial | Allan + convites |

---

## 5. Itens “nice to have” que **não** devem atrasar **A** se o prazo for lei

| Item | Nota |
|------|------|
| RLS evidência explícita no **Supabase cloud** | Checklist permite **dispensa explícita** — documentar decisão em `CHECKLIST` + `04_RISCOS_*.md` |
| OTEL export produção | Opcional (plano MVP Fase G) |
| Migrações **0017+** (ex.: **0020** RAG) | Só entram no “100%” se declarares **stack alvo** = branch atual com RAG em prod; caso contrário, corte explícito: “MVP = schema até **0016** + patches operacionais acordados” |

---

## 6. Veredito operacional para **05-05-2026**

1. **Viável com alta probabilidade:** cumprir **Definição A** com foco **P5a/P5b + G-A1 + G-D4** + fecho explícito de **D3/D5** como “adiado” em `DECISOES_PRODUTO_MVP_D1_D5.md` se ainda não houver tempo de implementação.  
2. **Condicional:** **Definição B** depende de **calendário jurídico** e de **terceiros** — não está só nas mãos da engenharia.  
3. **Ação imediata:** abrir `03_CRONOGRAMA_03A05_MAI_2026.md` e marcar **um** responsável por cada linha de **§3** deste ficheiro.

---

*Próximo ficheiro:* [`02_CRITERIOS_ACEITE_EVIDENCIAS.md`](./02_CRITERIOS_ACEITE_EVIDENCIAS.md)
