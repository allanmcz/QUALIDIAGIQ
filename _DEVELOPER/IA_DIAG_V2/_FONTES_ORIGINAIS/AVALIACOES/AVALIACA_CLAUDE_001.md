# AVALIACA_CLAUDE_001 — Crítica Técnica da Proposta IA_DIAG_AVANCADO

> Avaliação da sugestão do Claude para memória, contexto, RAG, Ollama, pgvector, indexação de código e LangGraph Checkpointer no QDI.

**Data:** 2026-05-17  
**Avaliador:** Codex  
**Escopo:** documentos `00` a `12` da pasta `IA_DIAG_AVANCADO`  
**Veredito resumido:** proposta tecnicamente rica, mas ambiciosa demais para adoção direta; deve virar roadmap incremental, com correções de aderência ao estado real do QDI.

---

## 1. Resposta Direta

A proposta do Claude é boa como **arquitetura-alvo**, especialmente nas quatro camadas de memória: Modelfile, RAG normativo, indexação do código e memória conversacional. Porém, ela mistura visão futura com implementação imediata, assume alguns caminhos ainda não validados no repositório atual e cria risco de overengineering se for seguida literalmente.

Minha recomendação: **não executar o plano de 5 sprints como está**. Use-o como material de referência, extraindo primeiro apenas três entregas: memória supervisionada, catálogo de fontes e benchmark mínimo.

---

## 2. Pontos Fortes

| Ponto | Avaliação |
|---|---|
| Modelo em 4 camadas | Excelente como mapa mental. Separa persona, fatos, código e histórico. |
| RAG com citação obrigatória | Alinha bem com o princípio QDI: sem evidência válida, sem resposta normativa. |
| pgvector local | Coerente com Supabase/PostgreSQL + pgvector e reduz divergência entre dev e produção. |
| Golden questions | Muito bom. Sem benchmark, o Ollama vira opinião, não ferramenta controlada. |
| Riscos e ADRs candidatos | Boa maturidade arquitetural. Ajuda Allan a decidir, não apenas executar. |
| Separação Ollama como provider | Correto em Clean Architecture: Ollama deve ficar em infrastructure/adapters. |
| Preservação de fontes locais | Documento `12_FONTES_LOCAIS_OLLAMA.md` acerta ao dizer que Ollama não lê disco diretamente; precisa de pipeline. |

Analogia Oracle: a proposta acerta ao tratar o Ollama como engine, e não como banco de dados. O conhecimento precisa passar por ETL, índice e consulta controlada.

---

## 3. Pontos Críticos

### 3.1 O plano presume mais "zero" do que o projeto realmente tem

O plano fala em criar `LLMProvider`, router, OllamaProvider e integração do zero. Mas o repositório atual já possui camada de LLM em `src/infrastructure/adapters`, `src/infrastructure/llm`, router e testes relacionados a Ollama/LangGraph.

**Risco:** duplicar infraestrutura já existente ou criar uma segunda arquitetura paralela.

**Correção recomendada:** antes de implementar qualquer arquivo do documento `04_ADAPTER_OLLAMA_PROVIDER.md`, fazer inventário do que já existe:

```text
src/infrastructure/adapters/llm_ollama.py
src/infrastructure/adapters/llm_langgraph_ollama.py
src/infrastructure/adapters/llm_anthropic.py
src/infrastructure/adapters/llm_openai.py
src/infrastructure/llm/adapters/
tests/unit/infrastructure/
```

---

### 3.2 Inconsistência de paths: `SRC/DOMAIN` vs `src/domain`

A proposta usa repetidamente `SRC/DOMAIN`, `SRC/APPLICATION`, etc. O projeto atual usa:

```text
src/domain
src/application
src/infrastructure
src/presentation
```

O `AGENTS.md` também define `src/` em minúsculo.

**Risco:** scripts de indexação, documentação e prompts ensinarem caminhos errados ao agente.

**Correção recomendada:** trocar todos os exemplos para minúsculo:

```text
src/domain
src/application
src/infrastructure
src/presentation
```

---

### 3.3 Modelo base escolhido precisa de validação local real

Claude recomenda `qwen2.5:14b-instruct-q4_K_M`. Isso é plausível, mas ainda é uma hipótese. No ambiente atual já apareceram variações como `qwen2.5-coder:7b`, `qwen2.5-coder:14b`, `llama3.2`, `gemma3:12b`, além de diferença entre cliente/servidor Ollama.

**Risco:** gastar uma sprint inteira em modelo antes de validar latência, qualidade e estabilidade.

**Correção recomendada:** rodar primeiro benchmark curto com 3 modelos disponíveis:

```text
qwen2.5-coder:7b
qwen2.5-coder:14b
llama3.2:latest ou llama3:latest
```

Critério mínimo:

| Métrica | Gate inicial |
|---|---:|
| Resposta PT-BR coerente | 100% em 5 perguntas |
| Arquitetura QDI correta | >= 80% |
| Latência aceitável | p95 < 30s |
| Não travar em prompt curto | obrigatório |

---

### 3.4 Embedding `nomic-embed-text` não deve substituir automaticamente `mxbai-embed-large`

Claude recomenda `nomic-embed-text` por ser leve. Só que no ambiente local já existe `mxbai-embed-large`, e nossa documentação anterior apontou esse modelo como opção natural para embeddings locais.

**Risco:** trocar modelo de embedding sem prova de recall no domínio tributário.

**Correção recomendada:** tratar `nomic`, `mxbai` e `bge-m3` como candidatos. A decisão deve sair de Recall@K em perguntas reais, não de premissa.

---

### 3.5 Threshold fixo `0.65` é prematuro

A proposta usa `score >= 0.65` como corte para resposta válida. A ideia é boa, mas o número é arbitrário antes do benchmark.

**Risco:** recusar respostas úteis ou aceitar respostas fracas dependendo do modelo de embedding, métrica e chunking.

**Correção recomendada:** calibrar threshold por categoria:

| Tipo de fonte | Threshold inicial sugerido |
|---|---:|
| Código indexado | calibrar com perguntas C |
| Legislação artigo específico | mais rigoroso |
| Aula/anotação | mais conservador |
| Busca híbrida lexical + semântica | usar score combinado validado |

O valor `0.65` pode ficar como default provisório, não como princípio final.

---

### 3.6 RAG Lexiq completo é grande demais para o primeiro passo

O plano propõe LC 214, EC 132, LC 227, NT, pareceres, cClassTrib, cCredPres, CST e NCM. Isso é arquitetura-alvo, mas como primeiro ciclo é grande demais.

**Risco:** gastar semanas em ingestão antes de provar que a recuperação funciona.

**Correção recomendada:** começar com um corpus piloto:

```text
AGENTS.md
docs/refs/01_PRD_BASE.md
docs/refs/02_MOSCOW_FEATURES.md
docs/refs/03_GAP_ANALYSIS.md
1 fonte legal oficial curta ou recorte controlado da LC 214/2025
```

Depois evoluir para Lexiq completa.

---

### 3.7 Checkpointer LangGraph é valioso, mas não deve entrar antes do RAG mínimo

Memória episódica com LangGraph/Postgres é útil para wizard multi-turno. Porém, sem RAG e benchmark estáveis, ela adiciona complexidade operacional cedo demais.

**Risco:** persistir histórico ruim, resposta ruim e estado ruim com aparência de "memória inteligente".

**Correção recomendada:** adiar Camada 4. Primeiro validar:

1. Modelfile.
2. Contexto supervisionado.
3. RAG mínimo.
4. Benchmark.
5. Só então checkpointer.

---

### 3.8 Há conflitos com decisões/documentos atuais do QDI

Exemplos:

| Tema | Proposta Claude | Estado/documentos atuais |
|---|---|---|
| Paths | `SRC/DOMAIN` | Projeto usa `src/domain` |
| Runtime IA | fala em ADR-09 | docs atuais mencionam ADR-007, ADR-021/022 em pontos de operação |
| Frontend | Next.js 15 + tRPC | AGENTS.md fala Next.js 15; docs atuais ainda citam Next.js 14 em `docs/01_arquitetura.md`; tRPC não aparece como obrigatório no AGENTS.md |
| Provider | criar do zero | já há adapters LLM no repositório |
| Pasta fonte | `dominio_fiscal/` | precisa decisão explícita; hoje `docs/refs` e `_DEVELOPER/_LEGISLACAO` já existem |

**Correção recomendada:** criar um ADR curto antes de mover qualquer coisa:

```text
ADR-IA-001 — Estratégia Local Ollama/RAG para QDI
Status: Proposto
Decisão: fasear adoção sem duplicar infraestrutura existente
```

---

## 4. Validação Jurídica e Fontes

Eu verifiquei rapidamente fontes oficiais do Planalto para bases legais centrais:

- LC 214/2025 existe e institui IBS, CBS e IS.
- LC 227/2026 existe e trata do Comitê Gestor do IBS, processo administrativo do IBS e alterações na LC 214/2025.
- EC 132/2023 está incorporada à Constituição e aparece em fonte oficial do Planalto.

Ainda assim, a proposta do Claude deve ser ajustada para não tratar qualquer PDF local como fonte normativa válida sem metadados.

**Regra recomendada para o QDI:**

```text
Fonte legal oficial > norma técnica > parecer interno > aula > anotação pessoal.
```

Conteúdo de aula deve virar fonte tipo `C`, não fonte primária.

---

## 5. Crítica por Documento

| Documento | Nota | Crítica |
|---|---:|---|
| `00_VISAO_GERAL.md` | 8/10 | Excelente visão, mas deve ser lida como arquitetura-alvo. |
| `01_ESCOLHA_MODELO_BASE.md` | 6/10 | Boa matriz, mas contém métricas presumidas; precisa benchmark local real. |
| `02_MODELFILE_QDI_MENTOR.modelfile` | 6/10 | Rico, mas grande e com alguns conflitos de stack/path. Deve ser enxugado. |
| `03_RAG_LEXIQ_ESTRATEGIA.md` | 8/10 | Boa estratégia de chunking; precisa começar por corpus piloto. |
| `04_ADAPTER_OLLAMA_PROVIDER.md` | 5/10 | Arquiteturalmente correto, mas ignora adapters já existentes no projeto. |
| `05_INDEXACAO_DOMINIO.md` | 7/10 | Boa ideia; corrigir paths e evitar hook Git automático cedo demais. |
| `06_CHECKPOINTER_LANGGRAPH.md` | 7/10 | Valioso para wizard, mas entra depois de RAG e benchmark. |
| `07_INFRA_DOCKER_LOCAL.md` | 7/10 | Boa topologia; precisa alinhar portas e compose já existente do QDI. |
| `08_PLANO_EXECUCAO_FASEADO.md` | 5/10 | Muito grande para o momento; deveria começar com sprint de validação curta. |
| `09_BENCHMARK_AVALIACAO.md` | 9/10 | Melhor parte operacional; deve ser antecipada. |
| `10_REFERENCIAS_ESTUDO.md` | 8/10 | Bom roteiro; alguns links/versionamentos devem ser checados antes de execução. |
| `11_RISCOS_E_DECISOES.md` | 8/10 | Boa matriz; faltou risco de duplicar infraestrutura existente. |
| `12_FONTES_LOCAIS_OLLAMA.md` | 9/10 | Documento muito útil; alinha bem com ensino supervisionado e catálogo de fontes. |

---

## 6. Prioridade Recomendada

### Fazer agora

1. Corrigir paths para `src/` minúsculo.
2. Criar benchmark curto com 10 perguntas.
3. Validar modelo local que não trave.
4. Criar catálogo de fontes.
5. Rodar RAG piloto com 3 a 5 documentos.

### Fazer depois

1. Indexar código por AST.
2. Criar retrieval híbrido completo.
3. Integrar ao router existente.
4. Persistir memória conversacional com LangGraph.
5. Automatizar reindexação por commit.

### Não fazer ainda

1. Ingerir toda Lexiq de uma vez.
2. Criar novo `LLMProvider` sem reconciliar com o código existente.
3. Adotar `nomic-embed-text` sem comparação com `mxbai-embed-large`.
4. Transformar o Modelfile em depósito de regras longas.
5. Colocar hook Git automático antes do pipeline estar estável.

---

## 7. Plano Enxuto Proposto

### Sprint IA-0 — Validação de base, 2 a 3 blocos de 45 min

Entregas:

- `ollama list` saneado.
- modelo local escolhido provisoriamente.
- smoke test com 5 perguntas.
- decisão registrada.

### Sprint IA-1 — Memória supervisionada, 1 semana leve

Entregas:

- `Modelfile` enxuto.
- `.ollama/context/*.md`.
- caderno supervisionado com 10 casos.
- avaliação manual.

### Sprint IA-2 — RAG piloto, 1 semana

Entregas:

- catálogo de fontes.
- 3 a 5 documentos indexados.
- busca com citação.
- 10 golden questions.

### Sprint IA-3 — Integração com QDI existente

Entregas:

- adaptação ao router/adapters já existentes.
- testes unitários e integração.
- decisão sobre expandir Lexiq.

---

## 8. Decisões Que Allan Deve Tomar

| Decisão | Recomendação |
|---|---|
| A proposta vira execução imediata? | Não. Virar roadmap. |
| Modelo base final agora? | Não. Validar localmente primeiro. |
| Embedding final agora? | Não. Comparar `mxbai`, `nomic`, `bge-m3` se disponível. |
| Checkpointer já? | Não. Depois do RAG piloto. |
| RAG completo já? | Não. Começar por corpus pequeno. |
| Modelfile do Claude deve substituir o atual? | Não diretamente. Mesclar e enxugar. |

---

## 9. Veredito Final

A sugestão do Claude é uma boa **arquitetura de chegada**, mas não é um bom **primeiro passo operacional**. Ela tem visão de engenheiro sênior, porém precisa passar pelo filtro do estado real do QDI: código já existente, paths em minúsculo, decisões anteriores, adapters atuais e capacidade de Allan em blocos de estudo de 45 minutos.

O caminho mais seguro é tratar a proposta como backlog técnico supervisionado. Primeiro, provar que o modelo local responde bem; depois, provar que o RAG recupera fonte certa; só então persistir memória conversacional e indexar o código inteiro.

---

## 10. Referências Consultadas

### Documentos locais avaliados

- `README.md`
- `00_VISAO_GERAL.md`
- `01_ESCOLHA_MODELO_BASE.md`
- `02_MODELFILE_QDI_MENTOR.modelfile`
- `03_RAG_LEXIQ_ESTRATEGIA.md`
- `04_ADAPTER_OLLAMA_PROVIDER.md`
- `05_INDEXACAO_DOMINIO.md`
- `06_CHECKPOINTER_LANGGRAPH.md`
- `07_INFRA_DOCKER_LOCAL.md`
- `08_PLANO_EXECUCAO_FASEADO.md`
- `09_BENCHMARK_AVALIACAO.md`
- `10_REFERENCIAS_ESTUDO.md`
- `11_RISCOS_E_DECISOES.md`
- `12_FONTES_LOCAIS_OLLAMA.md`

### Fontes oficiais verificadas

- Planalto — Lei Complementar 214/2025: https://planalto.gov.br/ccivil_03/Leis/LCP/Lcp214.htm
- Planalto — Lei Complementar 227/2026: https://www.planalto.gov.br/ccivil_03/leis/lcp/Lcp227.htm
- Planalto — Constituição Federal com referências à EC 132/2023: https://planalto.gov.br/ccivil_03/constituicao/constituicao.htm

