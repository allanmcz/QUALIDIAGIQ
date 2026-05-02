# Checklist — confirmações Allan (MVP / Beta)

> **Única fonte no repositório:** este ficheiro (`docs/operacao/CHECKLIST_CONFIRMACAO_ALLAN_MVP.md`). Não há cópia paralela em `_DEVELOPER/` para este checklist.  
> **Origem analítica (interna):** `_DEVELOPER/_CONCLUIDOS_DEV/ANALISE_DEVELOPER_02052026.md` — pasta local de trabalho, não versionada.  
> **Data baseline checklist:** 2026-05-02  
> **Uso:** marcar **[x]** quando confirmado; preencher campos **Data** e **Notas** onde aplicável. Itens aqui **bloqueiam** ou **orientam** lançamento MVP / Beta — não são delegáveis só a engenharia sem OK explícito do produto.

**Ligações úteis:** decisões D\* — `docs/operacao/DECISOES_PRODUTO_MVP_D1_D5.md` · jurídico MVP — `docs/legal/STATUS_JURIDICO_MVP.md`

---

## Resumo: decisões já fechadas (produto / política)

Estas decisões **já foram tomadas** pelo Allan (produto); a engenharia pode assumir como baseline. **Só mudam** com nova decisão explícita de política ou escopo.

| Área | O que ficou decidido | Data | Evidência técnica (rasto) |
|------|----------------------|------|---------------------------|
| Fluxo diagnóstico Free vs B2B | **D1** — sem login obrigatório no início; POST com sessão B2B; opt-in consultor conforme doc | 2026-05-02 | `docs/operacao/DECISOES_PRODUTO_MVP_D1_D5.md` § D1 |
| Identificação empresa | **D2** — CNPJ obrigatório | (doc D*) | mesmo documento |
| M12 checklist | **D6** — persistido conforme desenho | (doc D*) | mesmo documento |
| PDF — captação de lead (bloco explícito) | Mostrar **apenas e-mail e telefone**; sem nome nem cargo nesse bloco | 2026-05-02 | Template `relatorio_diagnostico.html`, fluxo wizard |
| PDF — idioma | **pt-BR** padrão; **en** opcional para rótulos do PDF (`locale_relatorio`); conteúdo dinâmico pode permanecer em PT até tradução completa | 2026-05-02 | Migração **`0016_locale_relatorio_pdf.sql`**, API + wizard |
| PDF — motor | **WeasyPrint** como **único** gerador deste relatório (sem Puppeteer) | 2026-05-02 | `pdf_generator_weasyprint.py`; linha **[x]** na secção 8 |
| LLM em runtime | **LangChain/LangGraph + Ollama** em conjunto (**ADR-007**); fallback HTTP documentado | 2026-05-02 | Secção 8 · variável `QDI_LLM_BACKEND` |
| Schema baseline MVP | Migrações **0015** e **0016** aplicadas no ambiente alvo (CNAE/macros + `locale_relatorio` / WORM PDF) | 2026-05-02 | `init.sql`, `make verify-schema-mvp`, SQL verificação MVP — **estado:** aplicadas (**confirmado Allan**) |

**Distinção importante:** o quadro acima é **decisão de produto/arquitetura**. Continua **pendente de execução/evidência operacional** o que está na **secção 1** (ex.: sign-off contábil P5, espelho WeasyPrint, smoke RLS no Supabase real, tag de release). Migrações **0015** e **0016** já constam como **feitas** na linha correspondente da secção 1.

---

## 0. Mapa rápido — Quem decide / Quem executa

Legenda breve: **Decide** = quem assina política, critério de “passou/não passou” ou prioridade. **Executa** = quem produz evidência, deploy ou artefacto (podes ser tu em ambos quando tens acesso).

| Sec. | Item (resumo) | Quem decide | Quem executa |
|:----:|---------------|-------------|--------------|
| **1** | P5 — PDF sign-off contábil | Allan (produto); parecer contábil pode ser **próprio Allan** se o processo interno aceitar auto-sign-off formal | Allan ou revisor contábil + registo no `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md` |
| **1** | P5 — ambiente espelho WeasyPrint | Allan (aprova critério “igual a prod”) | Engenharia / Ops — replicação de imagem, env, fontes |
| **1** | P6 — RLS smoke 2 tenants no Supabase **real** | Allan (aceita evidência “passou”) | Quem tem **credenciais Supabase** (Allan ou Ops) — ver runbooks em `docs/operacao/` |
| **1** | Migrações schema MVP até **0016** (incl. `locale_relatorio`; **0015** CNAE/macros onde aplicável) — **estado:** **0015** e **0016** aplicadas | Allan (autoriza release/schema) | Allan, Ops ou pipeline — `psql` / `make verify-schema-mvp-strict` · `scripts/verify_mvp_schema.py` |
| **1** | Tag / release MVP + `CHANGELOG_MVP` | Allan (momento e número) | Allan ou CI — git tag, entrada no changelog |
| **2** | Parecer **`/termos`** e **`/privacidade`** | Allan (aceita ou pede revisão) | **Advogado** (externo ou jurídico da casa) |
| **2** | Retenção telefone + alinhamento legal | Allan + **jurídico** (política de dados) | Jurídico (texto) + Eng (campos/API se mudar) |
| **2** | Canal titular / DPO operacional | Allan (aprova contacto público) | Jurídico (copy DPO) + Ops/site (publicação) |
| **3** | **D1** Free / fluxo contínuo vs B2B | **Allan** (**fechado 2026-05-02**) | Eng — `docs/operacao/DECISOES_PRODUTO_MVP_D1_D5.md` § D1 |
| **3** | **D3** Faturamento / setor fino | **Allan** | Eng — se houver novo requisito |
| **3** | **D4** URL canónica produção | **Allan** (assinatura da URL final) | Ops / Eng — DNS, `NEXT_PUBLIC_*`, CORS |
| **3** | **D5** Billing Plus/Pro | **Allan** | Eng / financeiro — gateway quando existir |
| **3** | PDF — **captação de lead** no relatório (bloco explícito) | **Allan** (**fechado 2026-05-02**) | Eng — apenas **e-mail + telefone** no bloco lead do PDF; nome/cargo fora desse bloco |
| **3** | PDF — **idioma** relatório | **Allan** (**fechado 2026-05-02**) | Eng — **pt-BR** padrão + **en** (labels EN; conteúdo dinâmico pode permanecer PT até tradução completa); campo `locale_relatorio`, migração **0016** |
| **3** | PDF — **motor de geração** | **Allan** (**fechado 2026-05-02**) | Eng — **WeasyPrint** único (sem Puppeteer) |
| **4** | **M08** revisão editorial (NTs, dispositivos) | Allan (aceita cobertura) | Revisor **interno ou externo** com perfil fiscal/editorial |
| **4** | **M03** manifesto revisto por tributarista | Allan (aceita texto público) | **Advogado / tributarista externo** (recomendado MoSCoW) |
| **4** | **M02** calibração 5 cases | Allan (metodologia e ownership) | Allan domínio + dados; Eng pode instrumentar/importação |
| **5** | PDF aprovado por **3 contadores externos** | Allan (abre convite e critério) | **Três terceiros** (salvo mudança explícita do critério MoSCoW) |
| **5** | Declaração MUST **12/12** para comercial | **Allan** | Interno — sem dependência externa obrigatória |
| **6** | Priorização Beta **S01–S11** | **Allan** | Eng — por item priorizado |
| **7** | GA / COULD **C01, C10, C08…** | **Allan** | Roadmap / Eng conforme escolha |
| **8** | RAG Lexiq obrigatório vs MVP pragmático | **Allan** | Eng — se exigir S02 antes de go-live institucional |
| **8** | LangChain/LangGraph + Ollama (stack conjunta) | **Allan** (**fechado 2026-05-02**) | Eng — **ADR-007**; default API LangGraph+ChatOllama; ``QDI_LLM_BACKEND=http_ollama`` fallback |

---

## 1. Gate MVP lançável (operação + qualidade percebida)

| OK | Item | Documento / evidência | Data | Notas |
|:--:|------|----------------------|------|-------|
| [ ] | **P5 — PDF** sign-off contábil (B.2) | `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md` | | |
| [ ] | **P5 — PDF** ambiente espelho produção WeasyPrint (B.3) | mesmo + `docs/operacao/RUNBOOK_DEPLOY_ROLLBACK.md` | | |
| [ ] | **P6 — RLS** smoke dois tenants no **projeto Supabase real** (não só CI local) | `docs/operacao/RUNBOOK_DEPLOY_ROLLBACK.md` + evidência de execução no projeto; procedimento RLS detalhado pode estar em artefacto Ops | | |
| [x] | Migrações aplicadas no ambiente alvo até **`0016`** (**0015** CNAE + pesos macro; **0016** `locale_relatorio` + WORM) | `make verify-schema-mvp-strict`, `docs/operacao/SQL_VERIFICACAO_SCHEMA_MVP.sql` | 2026-05-02 | **0015** e **0016** aplicadas no ambiente alvo (confirmado Allan). Revalidar após novo ambiente ou restore. |
| [ ] | **Tag / release** MVP + linha em `docs/CHANGELOG_MVP.md` | `docs/HANDOFF_PLANO_MVP_FECHADO.md` §8 | | |

---

## 2. Jurídico e LGPD

| OK | Item | Documento / evidência | Data | Notas |
|:--:|------|----------------------|------|-------|
| [ ] | Parecer externo sobre **`/termos`** e **`/privacidade`** | `docs/legal/STATUS_JURIDICO_MVP.md` | | |
| [ ] | Retenção **telefone respondente** alinhada a texto legal + processo interno | LGPD handoff MVP | | **Eng (2026-05-02):** telefone pode aparecer no **bloco lead do PDF** junto com e-mail; política de retenção continua a exigir parecer jurídico. |
| [ ] | Canal titular / DPO operacional | registar contacto público | | |

---

## 3. Decisões de produto (D*)

| OK | ID | Tema | Estado desejado a confirmar | Data | Notas |
|:--:|----|------|----------------------------|------|-------|
| [ ] | **D3** | Faturamento / setor fino | Adiar explícito **ou** novo requisito | | |
| [ ] | **D4** | URL canónica produção | URL final assinada Ops | | Parcial no doc |
| [ ] | **D5** | Billing Plus/Pro | Adiar **ou** escolher gateway/data | | |

**Já fechado (referência):** ver tabela **«Resumo: decisões já fechadas»** no início deste documento — inclui **D1**, **D2**, **D6** e PDF (lead, idioma, WeasyPrint). Detalhe normativo D\* continua em `docs/operacao/DECISOES_PRODUTO_MVP_D1_D5.md`.

**Complemento PDF (mesmo pacote de decisão 2026-05-02):**

- **Lead no PDF:** bloco explícito = **só e-mail e telefone**; nome/cargo **fora** desse bloco; dados completos no fluxo/API conforme modelo **atual**.
- **Idioma:** **pt-BR** por defeito; **en** para rótulos do PDF; matriz/checklist/cronograma dinâmicos podem seguir em PT até tradução.
- **Motor:** **WeasyPrint** único para este artefacto.

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

## 8. Princípios “não negociáveis” vs MVP atual

| OK | Tema | Decisão necessária | Data | Notas |
|:--:|------|-------------------|------|-------|
| [ ] | **RAG Lexiq obrigatório** em respostas fiscais | Aceitar **MVP pragmático** atual (guardrail sem RAG) **ou** exigir S02 antes de go-live institucional | | |
| [x] | **LangChain/LangGraph** + **Ollama** em conjunto | **Decidido (2026-05-02):** runtime default API — ver **ADR-007** (``LangGraphOllamaLlmAdapter``) | 2026-05-02 | Fallback HTTP: ``QDI_LLM_BACKEND=http_ollama`` |
| [x] | **WeasyPrint** como gerador único do PDF de diagnóstico | **Decidido (2026-05-02)** — sem motor paralelo Puppeteer para este relatório | 2026-05-02 | Homologação operacional continua em P5 (B.2/B.3) |

---

*Fim — checklist Allan MVP — preencher e arquivar com data da próxima revisão.*
