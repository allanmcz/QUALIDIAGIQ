# Plano de execução — handoff 02/05/2026 (fechamento de itens QDI)

> **Propósito:** inventário **auditável** do que falta para fechar o **MVP MoSCoW (12 MUST)** + **gate operacional** declarado em `docs/HANDOFF_PLANO_MVP_FECHADO.md`, mais **extensões Beta/GA** quando Allan decidir ampliar escopo.  
> **Não substitui:** `docs/HANDOFF_PROXIMA_SESSAO_QDI.md` (snapshot vivo); este ficheiro é **plano de trabalho e avaliação**.  
> **Data-base:** 2026-05-02 — inclui migrações até **`0014`** (CNAE), compose **`postgres:16-alpine`**, Ciclo Q executado.

---

## 1. Como ler este plano

| Camada | Significado “fechado” |
|--------|------------------------|
| **MVP técnico** | Código + testes + migrações aplicáveis; sem regressões nos MUST onde já há implementação. |
| **MVP lançável** | MVP técnico + **P5/P6** evidenciados em ambiente alvo + **jurídico mínimo** + decisões **D*** registadas ou explicitamente adiadas com registro. |
| **Beta (SHOULD)** | Funcionalidades MoSCoW camada SHOULD — **não** obrigatórias para declarar MVP fechado no PRD-base. |
| **GA (COULD)** | Nice-to-have / expansão — roadmap pós-validação com cliente pagante. |

**Épicos explicitamente fora do “fechar MVP”** (mantêm-se como backlog ou outros produtos): versionamento normativo completo das **regras de score** em PostgreSQL; RAG Lexiq integral no wizard; billing real (**D5**); QAI, QFC, QMI, RestituIQ (ver `.cursorrules`).

---

## 2. Resumo para avaliação rápida (Allan)

| Área | Situação | Bloqueia MVP lançável? |
|------|----------|-------------------------|
| MUST **M01–M03, M05–M07, M11–M12** | Fortemente implementados | Não (polimento incremental) |
| MUST **M04** PDF | Template + testes; falta **sign-off + produção WeasyPrint** | **Sim**, até critério comercial/auditável |
| MUST **M08** ancoragem legal | Matriz/código parcial; falta **revisão editorial completa** | Depende do critério “auditável” acordado |
| MUST **M09** lead | **D2 fechado:** CNPJ obrigatório (`DECISOES_PRODUTO_MVP_D1_D5.md`). Falta **D1** se quiser Free anónimo | **D1** sim se mudar modelo |
| MUST **M10** RLS | Local/CI OK; **Supabase prod** precisa evidência + migrações até **0014** se usar CNAE | **Sim** para go-live multi-tenant real |
| **P5 / B.2–B.3** | Checklist B.1 existe; caixas produção/sign-off abertas | **Sim** |
| **P6** | Runbook + testes; gap doc **G1–G5**; **verify-schema** sem CNAE automático | **Sim** em parte (evidência prod) |
| **Jurídico** | Textos MVP; parecer externo aberto | **Sim** para uso institucional |
| **Produto D3/D4/D5** | Pendentes registro | **D4** recomendável antes de prod |
| **CNAE lookup API/UI** | Dados **0013/0014** no repo; **sem** fluxo wizard | Não para MVP fechado no plano mestre; sim se Allan definir MUST implícito |
| **Calibração M02** coorte real | Roadmap / não automático | Não para MVP fechado técnico |
| **MoSCoW SHOULD (11)** | Não implementados como produto | Não para MVP |
| **MoSCoW COULD (10)** | Idem | Não para MVP |

---

## 3. Inventário — MVP MoSCoW MUST (M01–M12): o que falta

Cada linha: **ID**, **lacuna restante**, **critério de aceite sugerido**, **artefactos / dono**.

| ID | Lacuna | Critério de aceite | Dono / refs |
|----|--------|-------------------|---------------|
| **M01** | UX edge cases (`multipla_total`, opções vazias); CNAE no wizard **não** existe | Testes manuais/registrados + opcional E2E; se CNAE obrigatório: campo + API search | Produto + Eng · `docs/HANDOFF_PROXIMA_SESSAO_QDI.md` §5 |
| **M02** | Calibração com dados reais | Processo de coorte + atualização de pesos/notas documentado; `nota_calibracao_m02` revisada | Allan / dados · fora núcleo código |
| **M03** | Polimento | Nenhum gap funcional crítico citado — revisão contínua de copy/links | Produto |
| **M04** | Homologação humana; PDF real em container prod | `PDF_HOMOLOGACAO_CHECKLIST_B1.md`: B.2 sign-off + B.3 checkboxes; sem stub mascarado em prod | Allan + Ops · `HANDOFF_PLANO_MVP_FECHADO.md` Fase B |
| **M05** | E2E lista dashboard mockada no CI (sem backend) | Aceitar como **intencional** OU job integrado opcional | Eng · §7 handoff |
| **M06** | Polimento visual timeline/tabela | Opcional pós-MVP | Produto |
| **M07** | — | Coberto por regras determinísticas; revisão negócio | Produto |
| **M08** | Cobertura editorial todas NTs/dispositivos nas entregas ao cliente | Passagem linha a linha matriz/PDF/checklist | Allan/conteúdo · Fase F plano MVP |
| **M09** | **D1** Free vs B2B logado não decidido | Registro em `DECISOES_PRODUTO_MVP_D1_D5.md` + eventual fluxo técnico | Allan · **D2** já fechado (CNPJ obrigatório) |
| **M10** | RLS + roles **projeto Supabase real**; CNAE **0013/0014** aplicados se usar lookup global | Evidência: runbook + smoke dois tenants + contagens `qdi.cnae_subclasse`=1332 quando aplicável | Ops · `_DEVELOPER/RUNBOOK_SUPABASE_RLS.md`, `docs/operacao/GAP_ANALYSIS_RLS_P6_2026-05-02.md` |
| **M11** | Linkagem pergunta↔pilar no catálogo | Opcional MVP — melhoria contínua | Eng/conteúdo |
| **M12** | — | Persistência + PATCH + WORM — **feito** | — |

---

## 4. Inventário — blocos P1–P8 e operações (Ciclo P / Q)

| Bloco | Estado | O que falta (se houver) |
|-------|--------|-------------------------|
| **P1** OpenAPI | Feito | Export local `make openapi-export` antes de releases relevantes |
| **P2** E2E CI | Verde | Manter; P8 opcional com flag |
| **P3** asChild | Feito | — |
| **P4** Auditoria 37×35 | Script + relatório OK | Refino editorial `docs/refs/05_QUESTIONARIO_v1.md` (não bloqueio código) |
| **P5** M04 | Parcial | **B.2 sign-off**, **B.3** produção (checklist PDF) |
| **P6** M10 | Parcial prod | Executar smoke Supabase real; fechar **G2**: estender `scripts/verify_mvp_schema.py` e/ou `SQL_VERIFICACAO_SCHEMA_MVP.sql` para **CNAE/extensões** |
| **P7** Lista dashboard | App usa GET real | Nada crítico |
| **P8** Wizard normativa | Código + E2E opcional | Habilitar em prod só se produto quiser |
| **Ciclo Q** | Executado | Manter CHANGELOG/handoff sincronizados em releases |

---

## 5. Inventário — gate `HANDOFF_PLANO_MVP_FECHADO.md` §6 (checklist)

Atualizar evidências quando cada caixa for verdadeira no ambiente **alvo**.

- [ ] Migrações até **0012** mínimo em pré-prod/prod; se CNAE: até **0014** — `make verify-schema-mvp` + SQL verificação.
- [ ] **P5** completo: sign-off Allan/contábil + PDF gerado em ambiente espelho produção (WeasyPrint).
- [ ] **P6** completo: isolamento dois tenants **no projeto Supabase real** (não só CI local).
- [ ] **Jurídico:** parecer formal + canal titular/DPO + versão publicada (`docs/legal/STATUS_JURIDICO_MVP.md`).
- [ ] **Retenção telefone respondente:** texto `/privacidade` + processo interno alinhados ao parecer.
- [ ] **A.1:** tag/release + linha datada em `docs/CHANGELOG_MVP.md` (processo).
- [ ] **D1, D3, D4, D5:** registrados (mesmo que “adiado”) em `DECISOES_PRODUTO_MVP_D1_D5.md`.

Itens já tratados no repo (não repetir trabalho): LGPD aceite **0012**, **X-Trace-Id**, smoke automatizado `make mvp-gate`, runbook deploy/rollback.

---

## 6. Inventário — dados e engenharia (além do gate clássico)

| Item | Descrição | Esforço relativo | Bloqueia MVP? |
|------|-----------|------------------|---------------|
| **CNAE — API read-only** | `GET` search/autocomplete sobre `qdi.cnae_subclasse` ou view (JWT + tenant conforme desenho) | Médio | Não, salvo decisão produto |
| **CNAE — UI wizard** | Campo CNAE + validação + opcional descrição | Médio | Idem |
| **verify_mvp_schema + CNAE** | Contagens 1332; extensões `pg_trgm`/`pgcrypto`; opcional flag `--strict-cnae` | Baixo–médio | Não; reduz risco P6 |
| **Versionamento normativo score** | Tabelas regra com `vigencia_*`; sem hardcode | Alto (ADR + migrações) | Declarado fora MVP fechamento plano mestre |
| **OpenTelemetry export prod** | Além de trace HTTP — exporters configurados | Médio | Não (opcional G.2) |
| **Tipos pergunta não cobertos** | `NotImplementedError` em `src/domain/entities/questionario.py` se tipo novo aparecer | Baixo | Garantir catálogo só usa tipos suportados |
| **Acessibilidade** | axe / checklist manual incremental | Baixo contínuo | Não |

---

## 7. Inventário — MoSCoW SHOULD (Beta): fechar “todos os itens” além do MVP

Se Allan avaliar **roadmap Beta**, estas são as **11** features SHOULD do PRD (`docs/refs/02_MOSCOW_FEATURES.md`) — **nenhuma** está fechada como produto completo no núcleo atual:

| ID | Feature | Entregável típico |
|----|---------|-------------------|
| **S01** | LLM plano de ação | Use case + adapter Anthropic + guardrails Lexiq |
| **S02** | RAG Lexiq no wizard | Pipeline retriever + citação obrigatória + UX |
| **S03** | Simulador IBS+CBS+IS | Motor cenários + UI + base normativa versionada |
| **S04** | Exposição em R$ por gap | Modelo financeiro + dados |
| **S05** | Benchmark setorial | Agregações anónimas multi-tenant + UI |
| **S06** | ICMS-ST → IBS/CBS | Regras + narrativa |
| **S07** | Templates documentos (LLM) | Geração + revisão humana |
| **S08** | Setorialização varejo | Perguntas condicionais + catálogo |
| **S09** | Microlearning Hub | Links/integração |
| **S10** | Gating ABNT detalhado | Relatório aderência + remediação |
| **S11** | Cross-sell QFI/QMI | CTAs + métricas |

**Estimativa global SHOULD:** da ordem de **~61 dias-dev** no PRD (referência; recalibrar por sprint).

---

## 8. Inventário — MoSCoW COULD (GA)

10 features em `docs/refs/02_MOSCOW_FEATURES.md` (Winthor, Protheus, white-label, API pública parceiros, etc.). Fechamento só após Beta estável e decisão comercial.

---

## 9. Ordem de execução recomendada (para minimizar retrabalho)

```text
1. Ops: migrações 0014 em prod + verify-schema estendido (P6/G2)
2. Ops + Allan: smoke RLS dois tenants no Supabase real (P6)
3. Allan + Ops: P5 PDF sign-off + container WeasyPrint produção (M04)
4. Jurídico externo + ajuste páginas /privacidade /termos + CHANGELOG
5. Produto: D1, D3, D4, D5 → registrar decisões (mesmo “adiado”)
6. Conteúdo: M08 revisão completa
7. Eng (opcional MVP+): API CNAE + campo wizard
8. Roadmap: escolher 1–2 SHOULD para Beta (S01/S02 ou S05 conforme estratégia)
```

---

## 10. Critério final “todos os itens MVP fechados”

Para declarar **MVP MoSCoW + gate plano** encerrado:

1. Tabela da **secção 3** sem lacunas **bloqueantes** (M04, M10 prod, M09/D1 se aplicável, M08 se auditoria exigir 100% cobertura legal).  
2. **Secção 5** com todas as caixas assinaladas com evidência (links, datas, ambiente).  
3. `docs/CHANGELOG_MVP.md` com release datado ou tag `mvp-*` referenciada.

Para declarar **MoSCoW completo incluindo SHOULD/COULD**: além do acima, implementar e validar **secções 7 e 8** (projeto multi-fase).

---

## 11. Documentos de referência cruzada

| Documento | Uso |
|-----------|-----|
| `docs/HANDOFF_PROXIMA_SESSAO_QDI.md` | Estado vivo do produto |
| `docs/HANDOFF_PLANO_MVP_FECHADO.md` | Fases A–G e gate §6 |
| `docs/refs/02_MOSCOW_FEATURES.md` | MUST/SHOULD/COULD/WONT |
| `docs/operacao/DECISOES_PRODUTO_MVP_D1_D5.md` | D1–D5 |
| `docs/legal/STATUS_JURIDICO_MVP.md` | Jurídico |
| `docs/operacao/PDF_HOMOLOGACAO_CHECKLIST_B1.md` | P5 |
| `docs/operacao/GAP_ANALYSIS_RLS_P6_2026-05-02.md` | P6/CNAE |
| `docs/operacao/RUNBOOK_DEPLOY_ROLLBACK.md` | D4 deploy |
| `docs/CHANGELOG_MVP.md` | Registro de releases |

---

---

## 12. Execução técnica — sessão agente (2026-05-02)

| Item plano (refs §4–§6) | Estado após execução |
|-------------------------|---------------------|
| **§6 G2** — `verify-schema` + CNAE | **Feito:** `scripts/verify_mvp_schema.py` com `--strict-cnae` / `QDI_VERIFY_SCHEMA_STRICT_CNAE`; alvo **`make verify-schema-mvp-strict`**; `SQL_VERIFICACAO_SCHEMA_MVP.sql` estendido. |
| **§6 inventário** — API CNAE read-only | **Feito:** `GET /referencia/cnae/subclasses` (Bearer JWT, Postgres via `DATABASE_URL`). |
| **§6 inventário** — UI wizard CNAE | **Feito:** datalist + debounce no passo 2 (`WizardForm`). |
| **§5 gate** — decisões D1/D3/D4/D5 | **Feito em doc:** `DECISOES_PRODUTO_MVP_D1_D5.md` (adiamentos explícitos / D4 parcial). |
| **§5 gate** — migrações prod / P5 PDF sign-off / P6 Supabase real / jurídico | **Não automatizável aqui** — permanecem com Allan / Ops / assessoria (evidência externa). |
| **§7 SHOULD Beta (S01–S11)** | **Fora do escopo desta sessão** (~61 dias-dev PRD); não implementado. |
| **§8 COULD GA** | Idem. |
| **§3 M08** editorial completo | Conteúdo — Allan/conteúdo. |
| **§3 M02** calibração coorte | Dados/processo — não código. |

**Comandos novos:** `make verify-schema-mvp-strict`.

**Próximo passo humano:** checklist `PDF_HOMOLOGACAO_CHECKLIST_B1.md` (B.2/B.3); smoke dois tenants no projeto Supabase de produção; parecer jurídico (`docs/legal/STATUS_JURIDICO_MVP.md`).

---

*Fim do plano handoff 02/05/2026 — `_DEVELOPER/PLANO_EXECUCAO_HANDOFF_02052026.md`*
