# Riscos, dependências e decisões — MVP **2026-05-05**

---

## 1. Matriz de riscos (top 5)

| ID | Risco | Prob. | Impacto | Mitigação |
|----|-------|-------|---------|-----------|
| R1 | Parecer jurídico não chega a tempo | Média | Alto para **definição B** | Fixar **definição A** como corte; jurídico em paralelo com data **pós-05-05** |
| R2 | Espelho WeasyPrint difere de prod (fontes/CSS) | Média | Médio | Checklist B1 + captura de versões pip/apt; mesmo `Dockerfile` da API |
| R3 | Scope creep (RAG, billing, novas migrations) | Média | Alto | **Congelamento** explícito — só P0 até tag |
| R4 | URL/CORS mal configurados em prod | Baixa | Alto | D4 com checklist mínimo + teste wizard em URL real |
| R5 | Exigência implícita de “12/12 MUST comercial” sem calibração M02 | Baixa | Médio | Separar **MVP técnico** de **MUST comercial** no `CHECKLIST` sec. 5 |

---

## 2. Decisões pendentes (D*) — o que precisa de linha escrita

| ID | Tema | Opções aceitáveis para 05-05 |
|----|------|------------------------------|
| **D3** | Faturamento / setor fino | Implementar mínimo **ou** “adiado” com data |
| **D4** | URL canónica | Lista final de origens CORS + `NEXT_PUBLIC_SITE_URL` |
| **D5** | Billing | “Adiado pós-MVP” explícito (sem gateway em prod) |

**Registo:** `docs/operacao/DECISOES_PRODUTO_MVP_D1_D5.md`.

---

## 3. Dependências externas

| Fornecedor | Entrega | Bloqueia |
|------------|---------|----------|
| Advogado | Parecer termos/privacidade | **Definição B** |
| Ops / cloud | Credenciais Supabase + migrate | **P6 cloud** (opcional) |
| Terceiros (contadores) | 3 pareceres PDF | **Critério comercial** sec. 5 checklist |

---

## 4. Residuos aceitáveis pós-05-05 (documentar, não esconder)

- Tradução completa EN em blocos dinâmicos do PDF (já admitido como parcial pelo produto).  
- M08 revisão editorial profunda (conteúdo fiscal) — desde que não haja erro normativo grave identificado pelo revisor interno.  
- E2E dashboard com mock no CI (já documentado como intencional no handoff).

---

*Prompt agente:* [`05_PROMPT_AGENTE_FECHO_MVP.md`](./05_PROMPT_AGENTE_FECHO_MVP.md)
