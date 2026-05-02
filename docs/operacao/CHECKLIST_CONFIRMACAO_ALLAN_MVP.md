# Checklist — confirmações Allan (MVP / Beta)

> **Versão Git (canónica):** `docs/operacao/CHECKLIST_CONFIRMACAO_ALLAN_MVP.md` — rastreável em PR/release.  
> **Cópia de trabalho opcional:** pode existir espelho local em `_DEVELOPER/CHECKLIST_CONFIRMACAO_ALLAN_02052026.md` (pasta normalmente ignorada pelo Git); ao divergir, **priorizar este ficheiro** no repositório ou sincronizar explicitamente.  
> **Origem analítica:** `_DEVELOPER/_CONCLUIDOS_DEV/ANALISE_DEVELOPER_02052026.md` (interno).  
> **Data baseline checklist:** 2026-05-02  
> **Uso:** marcar **[x]** quando confirmado; preencher campos **Data** e **Notas** onde aplicável. Itens aqui **bloqueiam** ou **orientam** lançamento MVP / Beta — não são delegáveis só a engenharia sem OK explícito do produto.

**Ligações úteis:** decisões D\* — `docs/operacao/DECISOES_PRODUTO_MVP_D1_D5.md` · jurídico MVP — `docs/legal/STATUS_JURIDICO_MVP.md`

---

## 0. Mapa rápido — Quem decide / Quem executa

Legenda breve: **Decide** = quem assina política, critério de “passou/não passou” ou prioridade. **Executa** = quem produz evidência, deploy ou artefacto (podes ser tu em ambos quando tens acesso).

| Sec. | Item (resumo) | Quem decide | Quem executa |
|:----:|---------------|-------------|--------------|
| **1** | P5 — PDF sign-off contábil | Allan (produto); parecer contábil pode ser **próprio Allan** se o processo interno aceitar auto-sign-off formal | Allan ou revisor contábil + registo no `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md` |
| **1** | P5 — ambiente espelho WeasyPrint | Allan (aprova critério “igual a prod”) | Engenharia / Ops — replicação de imagem, env, fontes |
| **1** | P6 — RLS smoke 2 tenants no Supabase **real** | Allan (aceita evidência “passou”) | Quem tem **credenciais Supabase** (Allan ou Ops) — ver runbooks em `docs/operacao/` |
| **1** | Migrações até **0015** no ambiente alvo | Allan (autoriza release/schema) | Allan, Ops ou pipeline — `psql` / `make verify-schema-mvp-strict` |
| **1** | Tag / release MVP + `CHANGELOG_MVP` | Allan (momento e número) | Allan ou CI — git tag, entrada no changelog |
| **2** | Parecer **`/termos`** e **`/privacidade`** | Allan (aceita ou pede revisão) | **Advogado** (externo ou jurídico da casa) |
| **2** | Retenção telefone + alinhamento legal | Allan + **jurídico** (política de dados) | Jurídico (texto) + Eng (campos/API se mudar) |
| **2** | Canal titular / DPO operacional | Allan (aprova contacto público) | Jurídico (copy DPO) + Ops/site (publicação) |
| **3** | **D1** Free / fluxo contínuo vs B2B | **Allan** (**fechado 2026-05-02**) | Eng — `docs/operacao/DECISOES_PRODUTO_MVP_D1_D5.md` § D1 |
| **3** | **D3** Faturamento / setor fino | **Allan** | Eng — se houver novo requisito |
| **3** | **D4** URL canónica produção | **Allan** (assinatura da URL final) | Ops / Eng — DNS, `NEXT_PUBLIC_*`, CORS |
| **3** | **D5** Billing Plus/Pro | **Allan** | Eng / financeiro — gateway quando existir |
| **4** | **M08** revisão editorial (NTs, dispositivos) | Allan (aceita cobertura) | Revisor **interno ou externo** com perfil fiscal/editorial |
| **4** | **M03** manifesto revisto por tributarista | Allan (aceita texto público) | **Advogado / tributarista externo** (recomendado MoSCoW) |
| **4** | **M02** calibração 5 cases | Allan (metodologia e ownership) | Allan domínio + dados; Eng pode instrumentar/importação |
| **5** | PDF aprovado por **3 contadores externos** | Allan (abre convite e critério) | **Três terceiros** (salvo mudança explícita do critério MoSCoW) |
| **5** | Declaração MUST **12/12** para comercial | **Allan** | Interno — sem dependência externa obrigatória |
| **6** | Priorização Beta **S01–S11** | **Allan** | Eng — por item priorizado |
| **7** | GA / COULD **C01, C10, C08…** | **Allan** | Roadmap / Eng conforme escolha |
| **8** | RAG Lexiq obrigatório vs MVP pragmático | **Allan** | Eng — se exigir S02 antes de go-live institucional |
| **8** | LangChain/LangGraph obrigatório vs Ollama-only | **Allan** | Eng — ADR / épico SHOULD conforme decisão |

---

## 1. Gate MVP lançável (operação + qualidade percebida)

| OK | Item | Documento / evidência | Data | Notas |
|:--:|------|----------------------|------|-------|
| [ ] | **P5 — PDF** sign-off contábil (B.2) | `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md` | | |
| [ ] | **P5 — PDF** ambiente espelho produção WeasyPrint (B.3) | mesmo + `docs/operacao/RUNBOOK_DEPLOY_ROLLBACK.md` | | |
| [ ] | **P6 — RLS** smoke dois tenants no **projeto Supabase real** (não só CI local) | `docs/operacao/RUNBOOK_DEPLOY_ROLLBACK.md` + evidência de execução no projeto; procedimento RLS detalhado pode estar em artefacto Ops | | |
| [ ] | Migrações aplicadas no ambiente alvo até **`0015`** (se usar CNAE + pesos macro DB) | `make verify-schema-mvp-strict` ou SQL equivalente | | |
| [ ] | **Tag / release** MVP + linha em `docs/CHANGELOG_MVP.md` | `docs/HANDOFF_PLANO_MVP_FECHADO.md` §8 | | |

---

## 2. Jurídico e LGPD

| OK | Item | Documento / evidência | Data | Notas |
|:--:|------|----------------------|------|-------|
| [ ] | Parecer externo sobre **`/termos`** e **`/privacidade`** | `docs/legal/STATUS_JURIDICO_MVP.md` | | |
| [ ] | Retenção **telefone respondente** alinhada a texto legal + processo interno | LGPD handoff MVP | | |
| [ ] | Canal titular / DPO operacional | registar contacto público | | |

---

## 3. Decisões de produto (D*)

| OK | ID | Tema | Estado desejado a confirmar | Data | Notas |
|:--:|----|------|----------------------------|------|-------|
| [ ] | **D3** | Faturamento / setor fino | Adiar explícito **ou** novo requisito | | |
| [ ] | **D4** | URL canónica produção | URL final assinada Ops | | Parcial no doc |
| [ ] | **D5** | Billing Plus/Pro | Adiar **ou** escolher gateway/data | | |

**Já fechado (referência):** **D1** (2026-05-02) diagnóstico sem login no início; POST com sessão B2B; opt-in consultor **ou** só — ver `docs/operacao/DECISOES_PRODUTO_MVP_D1_D5.md` § D1 · **D2** CNPJ obrigatório · **D6** M12 persistido — não requer reconfirmação salvo mudança de política.

---

## 4. Conteúdo e conformidade fiscal (M08 / M03 / M02)

| OK | Item | Critério | Data | Notas |
|:--:|------|----------|------|-------|
| [ ] | **M08** revisão editorial completa (NTs, dispositivos em relatório/PDF/checklist) | Cobertura acordada internamente | | |
| [ ] | **M03** manifesto técnico público revisto por advogado tributarista | MoSCoW §8 MUST | | |
| [ ] | **M02** calibração score com **5 cases** (varejo, indústria, serviços, agro, saúde) | MoSCoW §8 MUST | | Processo + ownership dados |

---

## 5. MoSCoW §8 — critérios de aprovação

| OK | Critério | Data | Notas |
|:--:|----------|------|-------|
| [ ] | PDF aprovado por **3 contadores** externos | | |
| [ ] | Declaração interna: MUST **12/12** “fechados produto” para efeito comercial | | Ajustar definição se algum MUST ficar “técnico OK / aguardando parecer” |

---

## 6. Priorização Beta (SHOULD — escolha estratégica)

Preencher **S** (Sim neste trimestre) ou **N** (não agora) — pelo menos uma linha com **S** quando quiseres abrir Beta técnico.

| ID | Feature (resumo) | S / N | Ordem (1=primeiro) | Notas |
|----|------------------|-------|-------------------|-------|
| S01 | LLM plano (Anthropic/API + persona) | | | |
| S02 | RAG Lexiq no wizard | | | |
| S03 | Simulador IBS+CBS+IS | | | |
| S04 | Exposição R$ por gap | | | |
| S05 | Benchmark setorial | | | |
| S06 | ICMS-ST → IBS/CBS | | | |
| S07 | Templates documentos (LLM) | | | |
| S08 | Setorialização varejo profunda | | | |
| S09 | Microlearning Hub | | | |
| S10 | Gating ABNT detalhado (tier) | | | |
| S11 | Cross-sell QFI/QMI | | | |

**Recomendação da análise (não vinculante):** escolher **1–2** itens **S** para o primeiro ciclo Beta (ex.: S02 + S05 ou S01 + provedor cloud).

---

## 7. GA / COULD (só registo — opcional)

| OK | Quer incluir no roadmap 12 meses? | ID | Notas |
|:--:|-----------------------------------|----|-------|
| [ ] | | C01 Winthor | |
| [ ] | | C10 API pública parceiros | |
| [ ] | | C08 White-label | |
| [ ] | Outros C02–C09 (especificar): | | |

---

## 8. Princípios “não negociáveis” vs MVP actual

| OK | Tema | Decisão necessária | Data | Notas |
|:--:|------|-------------------|------|-------|
| [ ] | **RAG Lexiq obrigatório** em respostas fiscais | Aceitar **MVP pragmático** atual (guardrail sem RAG) **ou** exigir S02 antes de go-live institucional | | |
| [ ] | **LangChain/LangGraph** como stack obrigatória no papel | Aceitar Ollama-only até épico SHOULD **ou** impor integração com prazo | | |

---

*Fim — checklist Allan MVP — preencher e arquivar com data da próxima revisão.*
