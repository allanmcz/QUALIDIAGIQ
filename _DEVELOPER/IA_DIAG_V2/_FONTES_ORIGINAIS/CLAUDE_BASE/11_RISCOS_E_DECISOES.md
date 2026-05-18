# 11 — Matriz de Riscos e ADRs Candidatos

> **Objetivo:** mapear riscos técnicos da introdução do Ollama no ecossistema QDI e propor decisões arquiteturais (ADRs) candidatas.

---

## 1. Matriz de Riscos

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|---------------|---------|-----------|
| R-01 | Qwen 2.5 alucina cClassTrib | Alta | Alto | Threshold ≥ 0.65 + citação obrigatória + recusa controlada |
| R-02 | Latência > 30s no M2 Max | Média | Médio | Fallback para Llama 8B; reduzir num_ctx |
| R-03 | RLS conflita com LangGraph | Baixa | Alto | Configurar `app.current_tenant_id` no pool de conexão |
| R-04 | OCR ruim em PDFs antigos | Média | Médio | Pipeline `ocrmypdf` pré-ingestão |
| R-05 | Embeddings nomic perdem recall em jargão jurídico | Média | Alto | Plano B: migrar para bge-m3 (1024 dim) |
| R-06 | Volume pgvector cresce além do previsto | Baixa | Médio | Particionamento por documento + arquivamento |
| R-07 | Ollama trava em consultas longas | Baixa | Alto | Retry exponencial + timeout 120s + circuit breaker |
| R-08 | Modelfile vira "monstro" difícil de manter | Média | Médio | Limitar a 8 KB; versionar em Git; ADR para mudanças |
| R-09 | Divergência Ollama vs Claude no wizard | Alta | Alto | Benchmark contínuo + LLM Router com fallback |
| R-10 | Hooks Git de reindexação lentos | Média | Baixo | Reindexação incremental apenas dos arquivos modificados |
| R-11 | Dependência do OrbStack para infra local | Baixa | Médio | Alternativa documentada: Docker Desktop ou Colima |
| R-12 | Atualização da LC 214/2025 invalida ingestão | Alta | Alto | Versionamento normativo (vigencia_inicio/fim) já está no schema |
| R-13 | M2 Max em modo low-power degrada performance | Baixa | Médio | Documentar requisitos: notebook em AC, "Alto desempenho" |
| R-14 | Memória paramétrica do modelo "vaza" persona errada | Baixa | Alto | Smoke tests no CI a cada nova versão do Modelfile |

---

## 2. ADRs Candidatos

A introdução do Ollama exige formalização de decisões via ADR (Architecture Decision Records). Sugestão de ADRs a criar:

### ADR-IA-001 — Adoção do Qwen 2.5 14B como LLM local

**Status:** Proposto
**Contexto:** Necessidade de desenvolvimento e prototipagem sem custo de API.
**Decisão:** Adotar Qwen 2.5 14B Instruct Q4_K_M como modelo padrão local.
**Consequências:**
- (+) Custo zero em dev
- (+) Paridade arquitetural com produção via LLM Router
- (-) Latência maior que Claude
- (-) Acurácia 5-15% inferior em casos complexos

### ADR-IA-002 — Estrutura da Lexiq em `dominio_fiscal/`

**Status:** Proposto
**Contexto:** Fontes Lexiq estavam dispersas; precisamos de organização canônica.
**Decisão:** Pasta `dominio_fiscal/` na raiz do projeto com subpastas `legislacao/`, `notas_tecnicas/`, `pareceres/`, `tabelas/`, `jurisprudencia/`.
**Consequências:**
- (+) Fonte única e versionada
- (+) Caminho padronizado para scripts de ingestão
- (-) Repositório Git fica pesado (mitigar com Git LFS para PDFs)

### ADR-IA-003 — Embedding model padrão: nomic-embed-text

**Status:** Proposto
**Contexto:** Escolha entre nomic-embed-text (768d) e bge-m3 (1024d).
**Decisão:** nomic-embed-text para Onda 1.0; reavaliar para bge-m3 se Recall@8 < 80%.
**Consequências:**
- (+) Menor footprint (300 MB vs 1.2 GB)
- (+) Menor latência (~5 ms/chunk)
- (-) Pode ter recall inferior em jargão jurídico

### ADR-IA-004 — Persistência conversacional via LangGraph PostgresCheckpointer

**Status:** Proposto
**Contexto:** Necessidade de retomar sessões multi-dia do wizard.
**Decisão:** Usar `AsyncPostgresSaver` do LangGraph no mesmo pgvector da Lexiq.
**Consequências:**
- (+) Reuso de infra
- (+) RLS multi-tenant nativo
- (-) Acopla Wizard a Postgres (mas é nossa stack canônica)

### ADR-IA-005 — Retrieval híbrido (RRF) sobre busca puramente semântica

**Status:** Proposto
**Contexto:** Consultas tributárias frequentemente buscam termos exatos (ex: "cClassTrib 040101").
**Decisão:** Combinar busca semântica (HNSW) + lexical (pg_trgm) via Reciprocal Rank Fusion.
**Consequências:**
- (+) Recall significativamente superior em queries técnicas
- (-) Latência ligeiramente maior (~50 ms extra)
- (-) Complexidade SQL maior

### ADR-IA-006 — Reindexação automática do código via Git hook

**Status:** Proposto
**Contexto:** Camada 3 precisa refletir o estado atual do código.
**Decisão:** Hook `post-commit` chama `indexar_dominio.py --incremental`.
**Consequências:**
- (+) Camada 3 sempre atualizada
- (-) Atraso de ~2-5s ao final do commit
- (-) Hook não funciona em commits pelo GitHub UI (aceitável; só dev local)

---

## 3. Decisões Já Tomadas Implicitamente

Estas decisões estão embutidas na arquitetura proposta e merecem formalização posterior:

1. **Ollama nativo, não containerizado** — para aproveitar Apple Metal
2. **pgvector em container Docker** — para isolamento e reprodutibilidade
3. **Schemas separados:** `qdi_rag`, `qdi_langgraph`, `qdi_observability`
4. **Princípios não-negociáveis QDI são imutáveis** — não há trade-off
5. **Allan controla todo commit/push** — agente nunca executa Git sem confirmação

---

## 4. Pontos de Decisão Pendentes (Aguardam Allan)

| Pergunta | Opções | Recomendação |
|----------|--------|--------------|
| Qual modelo local? | Qwen 14B / Llama 8B / Mistral 22B | Qwen 14B |
| Qual embedding? | nomic / bge-m3 | nomic (começar) |
| Ollama ou MLX? | Ollama (mais simples) / MLX (mais rápido) | Ollama |
| Usar Git LFS para PDFs? | Sim / Não | Sim (PDFs > 10 MB) |
| Sprint inicial | Sprint 0 (leitura) / Sprint 1 (mão na massa) | Sprint 0 |
| Quem mantém Modelfile? | Allan apenas / Agente Claude | Allan (controle de persona) |

---

## 5. Critérios para "Voltar Atrás" (Rollback)

Quando devemos abandonar Ollama e seguir só com Claude?

- [ ] Se acurácia < 70% após Sprint 5 (Qwen + bge-m3 + tuning completo)
- [ ] Se latência p95 > 60s após otimizações
- [ ] Se Ollama travar > 5x/dia em uso normal
- [ ] Se manutenção do Modelfile consumir > 4h/sprint
- [ ] Se Allan considerar o ganho de custo (USD 0 → USD ~20/mês de Claude API em dev) **não compensar** o overhead operacional

Se 2+ critérios forem disparados, **rollback** para Claude-only em dev (decisão estratégica de produto).

---

## 6. Como Atualizar Esta Documentação

A cada Sprint executado:
1. Mover riscos materializados de "Probabilidade Alta" para a seção de "Lições aprendidas"
2. Atualizar status dos ADRs (Proposto → Aceito / Rejeitado / Superseded)
3. Adicionar novos riscos descobertos
4. Versionar em Git com commit: `arch(qdi-ia): atualizar matriz de riscos pós-sprint N`
