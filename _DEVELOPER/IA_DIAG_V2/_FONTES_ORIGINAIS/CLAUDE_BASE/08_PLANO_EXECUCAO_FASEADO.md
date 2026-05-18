# 08 — PLANO COMPLETO DE EXECUÇÃO (5 Sprints × 1 semana)

> **Objetivo:** plano executável dia-a-dia para construir do zero a infraestrutura de memória e contexto Ollama para o QDI.

---

## Resumo Visual

```
SPRINT 0 (½ semana) — Leitura e Setup
SPRINT 1 (1 semana) — Infra + Persona (Camada 1)
SPRINT 2 (1 semana) — RAG Lexiq (Camada 2)
SPRINT 3 (1 semana) — Adapter + LLM Router + Testes
SPRINT 4 (1 semana) — Schema do código + Memória conversacional (Camadas 3+4)
SPRINT 5 (1 semana) — Benchmark + Tuning + Integração wizard

Total: ~5,5 semanas de trabalho efetivo (em ritmo ~3h/dia)
```

---

## Premissas

| Premissa | Valor |
|----------|-------|
| Ritmo de estudo do Allan | ~3h/dia, 5 dias/semana (sextas 17h estratégico, domingo OFF) |
| Hardware | M2 Max 64 GB |
| OS | macOS Sonoma+ |
| Modelo Ollama | Qwen 2.5 14B Q4_K_M |
| Stack permitida | apenas a canônica QDI (sem libs novas sem ADR) |
| Critério de "concluído" | testes passando + commit + atualização da documentação |

---

# 🧭 SPRINT 0 — Leitura e Setup (½ semana, ~6h)

**Meta:** controlador entende a arquitetura proposta antes de implementar.

### Dia 1 (~2h)
- [ ] Ler `README.md` desta pasta
- [ ] Ler `00_VISAO_GERAL.md` (arquitetura 4 camadas)
- [ ] Ler `01_ESCOLHA_MODELO_BASE.md` (justificativa Qwen)
- [ ] Decidir: aceita Qwen 2.5 14B ou prefere alternativa?

### Dia 2 (~2h)
- [ ] Ler `02_MODELFILE_QDI_MENTOR.modelfile`
- [ ] Ler `03_RAG_LEXIQ_ESTRATEGIA.md`
- [ ] Ler `04_ADAPTER_OLLAMA_PROVIDER.md`

### Dia 3 (~2h)
- [ ] Ler `05_INDEXACAO_DOMINIO.md`
- [ ] Ler `06_CHECKPOINTER_LANGGRAPH.md`
- [ ] Ler `07_INFRA_DOCKER_LOCAL.md`
- [ ] Ler `12_FONTES_LOCAIS_OLLAMA.md` (onde colocar PDFs/MDs)
- [ ] **Go/No-Go:** decidir se segue para Sprint 1 ou ajusta arquitetura

**Entregável Sprint 0:** decisão registrada em `_DEVELOPER/IA_DIAG_AVANCADO/ADR-IA-001-arquitetura-4-camadas.md`.

---

# 🚀 SPRINT 1 — Infra + Persona (Camada 1) | ~15h

**Meta:** Ollama rodando localmente + persona QDI ativa via Modelfile + smoke test passando.

### Segunda (~3h)
- [ ] **Instalar OrbStack** (se ainda não tiver): `brew install --cask orbstack`
- [ ] **Instalar Ollama:** `brew install ollama && brew services start ollama`
- [ ] **Validar instalação:** `ollama --version` retorna ≥ 0.5.0
- [ ] **Baixar modelos** (~14 GB, deixar rodando):
  ```bash
  ollama pull qwen2.5:14b-instruct-q4_K_M
  ollama pull nomic-embed-text
  ```

### Terça (~3h)
- [ ] **Criar estrutura de pastas:**
  ```bash
  mkdir -p /Users/allan/000-PROJETOS/018-QUALIDIAGIQ/_DEVELOPER/IA_DIAG_AVANCADO/SCRIPTS
  mkdir -p /Users/allan/.qdi-ia-local/{pgvector-data,jaeger-data}
  ```
- [ ] **Copiar `02_MODELFILE_QDI_MENTOR.modelfile`** para a pasta acima
- [ ] **Compilar modelo customizado:**
  ```bash
  cd /Users/allan/000-PROJETOS/018-QUALIDIAGIQ/_DEVELOPER/IA_DIAG_AVANCADO
  ollama create qdi-mentor -f 02_MODELFILE_QDI_MENTOR.modelfile
  ```
- [ ] **Smoke test 1 — Persona:**
  ```bash
  ollama run qdi-mentor "Apresente-se em 5 frases, mencionando os 10 princípios do QDI."
  ```
  Critério: resposta cita pelo menos 5 princípios, em PT-BR, com tom técnico.

### Quarta (~3h)
- [ ] **Copiar `docker-compose.yml`, `init.sql`, `Makefile`** para a pasta `IA_DIAG_AVANCADO/`
- [ ] **Subir stack:** `make ollama-up`
- [ ] **Validar Adminer:** abrir http://localhost:8080, conectar em `pgvector / qdi / devdev / qdi_rag`
- [ ] **Validar pgvector:** rodar no Adminer:
  ```sql
  SELECT extversion FROM pg_extension WHERE extname = 'vector';
  ```
  Deve retornar versão ≥ 0.7.

### Quinta (~3h)
- [ ] **Criar `.env`** com variáveis do `07_INFRA_DOCKER_LOCAL.md`
- [ ] **Smoke test 2 — Embedding:**
  ```bash
  curl http://localhost:11434/api/embeddings \
    -d '{"model": "nomic-embed-text", "prompt": "Lei Complementar 214/2025"}'
  ```
  Critério: retorna vetor com 768 floats.
- [ ] **Smoke test 3 — Conexão Python:**
  ```python
  import asyncpg, asyncio
  async def t():
      conn = await asyncpg.connect("postgresql://qdi:devdev@localhost:5433/qdi_rag")
      print(await conn.fetchval("SELECT version()"))
  asyncio.run(t())
  ```

### Sexta (~3h) — Revisão estratégica
- [ ] **Documentar Sprint 1:** criar `_DEVELOPER/IA_DIAG_AVANCADO/REPORTS/SPRINT_01_RELATORIO.md`
- [ ] **Commit:** `feat(qdi-ia): sprint 1 — infra local Ollama + Modelfile QDI ativo`
- [ ] **Decisão estratégica:** segue Sprint 2 ou ajusta persona?

**Entregável Sprint 1:**
- Ollama instalado e rodando ✅
- Modelo `qdi-mentor` compilado ✅
- pgvector + Adminer + Jaeger no ar ✅
- 3 smoke tests passando ✅

---

# 📚 SPRINT 2 — RAG Lexiq (Camada 2) | ~22h

**Meta:** base normativa do QDI indexada no pgvector com retrieval híbrido funcionando.

### Segunda (~4h)
- [ ] **Organizar fontes Lexiq** em `dominio_fiscal/` (ver `12_FONTES_LOCAIS_OLLAMA.md`)
- [ ] **Verificar PDFs:** LC 214/2025, EC 132/2023, LC 227/2026 estão na pasta
- [ ] **Criar script `SCRIPTS/ingestao_lexiq.py`** (esqueleto do `03_RAG_LEXIQ_ESTRATEGIA.md`)
- [ ] **Instalar dependências:**
  ```bash
  pip install langchain langchain-community pymupdf asyncpg structlog tenacity
  ```

### Terça (~4h)
- [ ] **Implementar ingestão LC 214/2025**
- [ ] **Validar 5 chunks aleatórios** via Adminer
- [ ] **Testar busca semântica simples** (sem fusion ainda):
  ```sql
  SELECT documento, artigo, conteudo
  FROM qdi_rag.lexiq_chunks
  ORDER BY embedding <=> (SELECT embedding FROM qdi_rag.lexiq_chunks LIMIT 1)
  LIMIT 5;
  ```

### Quarta (~4h)
- [ ] **Implementar ingestão EC 132/2023 e LC 227/2026**
- [ ] **Implementar ingestão NT 2025.002**
- [ ] **Implementar ingestão pareceres PT-001 a PT-011**

### Quinta (~4h)
- [ ] **Implementar ingestão tabelas** (cClassTrib, cCredPres, CST, NCM)
- [ ] **Validar volume final:** `SELECT documento, COUNT(*) FROM qdi_rag.lexiq_chunks GROUP BY 1`
  - LC_214_2025: ~2000 chunks
  - NT_2025_002: ~800 chunks
  - Pareceres: ~150 chunks
  - Tabelas: ~750 chunks (1 por código)

### Sexta (~3h) — Tuning
- [ ] **Implementar retrieval híbrido** (RRF fusion, ver `03_RAG_LEXIQ_ESTRATEGIA.md`)
- [ ] **Criar 10 golden questions** sobre LC 214/2025
- [ ] **Medir Recall@8**
- [ ] **Documentar Sprint 2:** `REPORTS/SPRINT_02_RELATORIO.md`
- [ ] **Commit:** `feat(qdi-ia): sprint 2 — RAG Lexiq tributária indexada (~3700 chunks)`

### Sábado (~3h) — Folga ou tuning de chunking se Recall@8 < 80%

**Entregável Sprint 2:**
- ~3700 chunks indexados ✅
- Retrieval híbrido (semântico + lexical) funcionando ✅
- 10 golden questions com Recall@8 ≥ 85% ✅

---

# 🔌 SPRINT 3 — Adapter + LLM Router + Testes | ~18h

**Meta:** código `OllamaProvider` em `src/infrastructure/` integrado ao FastAPI do QDI.

### Segunda (~4h)
- [ ] **Criar `SRC/DOMAIN/PORTS/LLM_PROVIDER.PY`** (Protocol do `04_ADAPTER_OLLAMA_PROVIDER.md`)
- [ ] **Criar `SRC/DOMAIN/EXCEPTIONS.PY`** (exceções `LLMUnavailableError`, `RecusaControladaError`, `CitacaoInvalidaError`)
- [ ] **Testes unitários do domain** (apenas tipos + exceções)

### Terça (~4h)
- [ ] **Criar `SRC/INFRASTRUCTURE/ADAPTERS/LLM/OLLAMA_PROVIDER.PY`** (do `04_ADAPTER_OLLAMA_PROVIDER.md`)
- [ ] **Testes unitários** com mock do `httpx.AsyncClient`
- [ ] **Validar princípio #6** (recusa controlada) e **princípio #7** (citação obrigatória)

### Quarta (~4h)
- [ ] **Criar `SRC/INFRASTRUCTURE/ADAPTERS/LLM/LLM_ROUTER.PY`** (ADR-09)
- [ ] **Integrar ao FastAPI:** criar dependency `get_llm_router()`
- [ ] **Criar rota de teste** `/api/v1/ia/chat` que usa o router

### Quinta (~3h)
- [ ] **Teste integração end-to-end:**
  ```bash
  curl -X POST http://localhost:8006/api/v1/ia/chat \
    -H "Content-Type: application/json" \
    -d '{
      "pergunta": "Como classificar uma venda interestadual?",
      "tenant_id": "11111111-1111-1111-1111-111111111111"
    }'
  ```
- [ ] Validar que resposta contém citação de evidências

### Sexta (~3h) — Revisão estratégica
- [ ] **Cobertura ≥ 85%** em `SRC/DOMAIN/` e `SRC/INFRASTRUCTURE/ADAPTERS/LLM/`
- [ ] **Documentar ADR-09 final** em `docs/adrs/ADR-009-llm-router.md`
- [ ] **Documentar Sprint 3:** `REPORTS/SPRINT_03_RELATORIO.md`
- [ ] **Commit:** `feat(qdi-ia): sprint 3 — OllamaProvider + LLMRouter integrados`

**Entregável Sprint 3:**
- Port `LLMProvider` definida no domain ✅
- `OllamaProvider` implementado e testado ✅
- `LLMRouter` com seleção por ambiente ✅
- Rota REST `/api/v1/ia/chat` funcional ✅

---

# 🧠 SPRINT 4 — Camadas 3 e 4 (Código + Conversacional) | ~18h

**Meta:** Ollama "conhece" o código QDI + lembra de sessões anteriores.

### Segunda-Terça (~6h) — Camada 3 (Indexação do código)
- [ ] **Criar `SCRIPTS/indexar_dominio.py`** (do `05_INDEXACAO_DOMINIO.md`)
- [ ] **DDL da tabela `qdi_rag.codigo_chunks`**
- [ ] **Indexar primeiro lote:** `SRC/DOMAIN/` (entities, value objects, ports)
- [ ] **Indexar segundo lote:** `SRC/APPLICATION/` (use cases)
- [ ] **Indexar `docs/refs/` e `docs/adrs/`**
- [ ] **Validar:** ~500 chunks no banco
- [ ] **Hook Git:** instalar `.git/hooks/post-commit`

### Quarta-Quinta (~8h) — Camada 4 (Checkpointer)
- [ ] **Instalar `langgraph` e `langgraph-checkpoint-postgres`**
- [ ] **DDL das tabelas `qdi_langgraph.checkpoints` e `qdi_langgraph.mensagens`**
- [ ] **Habilitar RLS multi-tenant** (princípio #1)
- [ ] **Criar `SRC/APPLICATION/WIZARDS/WIZARD_DIAGNOSTICO.PY`** (esqueleto do `06_CHECKPOINTER_LANGGRAPH.md`)
- [ ] **Implementar nós:** acolhimento, caracterizar_empresa
- [ ] **Teste:** iniciar sessão, fechar terminal, retomar — checkpoint persiste

### Sexta (~4h) — Revisão
- [ ] **Cobertura ≥ 85%** mantida
- [ ] **Documentar Sprint 4**
- [ ] **Commit:** `feat(qdi-ia): sprint 4 — camadas 3 e 4 (código indexado + checkpointer)`

**Entregável Sprint 4:**
- ~500 chunks de código indexados ✅
- Hook Git reindexando automaticamente ✅
- Wizard com Checkpointer persistente ✅
- RLS multi-tenant ativo ✅

---

# 🎯 SPRINT 5 — Benchmark + Tuning + Integração | ~18h

**Meta:** sistema validado contra Claude, com benchmark publicável.

### Segunda-Terça (~6h)
- [ ] **Criar `SCRIPTS/golden_questions.py`** com 50 perguntas:
  - 20 sobre LC 214/2025 (CBS, IBS, regimes)
  - 10 sobre cClassTrib específicos
  - 10 sobre arquitetura QDI (referenciam código indexado)
  - 10 sobre fluxos de wizard
- [ ] **Rodar contra Ollama + Claude** (dual run)
- [ ] **Calcular métricas:** acurácia, recall, citação válida, latência

### Quarta (~4h)
- [ ] **Tuning de chunking** se Recall < 90%
- [ ] **Tuning de threshold** se citação inválida > 5%
- [ ] **Tuning de temperatura** se respostas instáveis

### Quinta (~4h)
- [ ] **Integrar Ollama ao wizard real do QDI** (substituir mock)
- [ ] **Teste end-to-end:** 1 diagnóstico completo de empresa fictícia

### Sexta (~4h) — Encerramento
- [ ] **Relatório final** em `REPORTS/CONCLUSAO_IA_DIAG_AVANCADO.md`:
  - Métricas finais
  - Comparativo Ollama vs Claude
  - Custo evitado em USD
  - Próximos passos sugeridos (Onda 1.1)
- [ ] **Atualizar `CLAUDE.md` do projeto** com referência ao novo provider
- [ ] **Commit final:** `feat(qdi-ia): sprint 5 — sistema validado, Ollama integrado ao wizard`

**Entregável Sprint 5:**
- 50 golden questions executadas ✅
- Métricas documentadas ✅
- Wizard QDI rodando com Ollama em dev ✅
- ADR-IA-001 atualizada com aprendizados ✅

---

## Matriz de Riscos × Mitigação por Sprint

| Sprint | Risco | Probabilidade | Mitigação |
|--------|-------|---------------|-----------|
| 1 | Ollama não roda em M2 Max | Baixa | Apple Silicon é oficialmente suportado |
| 2 | PDFs com OCR ruim | Média | Re-OCR com `ocrmypdf` se necessário |
| 2 | Recall < 80% | Média | Trocar embeddings nomic → bge-m3 |
| 3 | Latência > 30s | Média | Reduzir num_ctx ou trocar para Llama 8B |
| 4 | RLS quebra LangGraph | Baixa | Configurar `app.current_tenant_id` no pool |
| 5 | Ollama alucina cClassTrib | Alta | Reforçar prompt + threshold mais alto |

---

## Critérios de Sucesso Globais

Ao final do Sprint 5, o sistema deve atender:

- [ ] **Disponibilidade:** Ollama responde em < 30s no p95
- [ ] **Acurácia tributária:** ≥ 85% nas 30 perguntas jurídicas
- [ ] **Acurácia arquitetural:** ≥ 90% nas 10 perguntas sobre código
- [ ] **Citação RAG:** 100% das respostas com evidência válida
- [ ] **Custo:** USD 0,00 em desenvolvimento
- [ ] **Compatibilidade:** trocar `provider=ollama` → `provider=anthropic` sem mudança de uso-case
- [ ] **Documentação:** todos os 12 arquivos de IA_DIAG_AVANCADO atualizados com aprendizados

---

## Próximas Ondas (Pós-Sprint 5)

| Onda | Objetivo | Esforço estimado |
|------|----------|------------------|
| 1.1 | Fine-tuning leve do Qwen com pareceres | 2 semanas |
| 1.2 | Streaming de respostas no wizard | 1 semana |
| 1.3 | Cache semântico (respostas frequentes) | 1 semana |
| 2.0 | Ollama em produção como provider secundário | 4 semanas |
| 2.1 | Migração para servidor dedicado (HostDime) | 2 semanas |
