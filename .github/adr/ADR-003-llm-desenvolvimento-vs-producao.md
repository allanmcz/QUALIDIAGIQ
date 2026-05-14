# ADR-003 — LLM desenvolvimento (Ollama) vs modelo produção (Claude/API)

Data: 2026-05-05  
Estado: aceito MVP

## Contexto

Stack declarada pelo produto menciona modelo primário Claude (Anthropic). O código expõe `OllamaLlmAdapter` para execução self-hosted/offline (**LC 214/2025** — previsibilidade de ambiente deve ser comunicada quando saídas impactam relatório tributário ao cliente).

## Decisão

1. Desenvolvimento / laboratório usa stack **LangGraph + LangChain ChatOllama** por padrão (`get_llm_service`), configurável por **`OLLAMA_BASE_URL`** (ou `OLLAMA_URL`) e **`OLLAMA_MODEL`** — ver **ADR-007**. Fallback **`QDI_LLM_BACKEND=http_ollama`** mantém **`OllamaLlmAdapter`** (REST direta).
2. Produção cliente pago deve documentar modelo **contratado** (Claude/API ou equivalente) em variável de ambiente **`LLM_PROVIDER`** + versão modelo em changelog interno antes de comunicar SLA de precisão.
3. Outputs exibidas ao cliente final da assessoria sempre passam disclaimers já presentes nos textos UX (consultoria tributária, não parecer jurídico).

## Consequências

- Divergências de comportamento Dev vs Produção ficam tratadas como **infra**, não regressão matemática do score (motor de score permanece determinístico).
- Time avalia atualização deste ADR quando tiers **Plus/Pro** tiverem anexo contratual modelo.

## Atualização QDI-H-032 (2026-05-11)

- **`QDI_LLM_BACKEND`** + **`ANTHROPIC_API_KEY`** em `Settings` materializam a fábrica em `build_llm_adapter_from_settings()` (**ADR-021**, `llm_router.py`), invocada por `get_llm_service()` (`deps_infra_services.py`): `anthropic` com chave ⇒ `AnthropicLlmAdapter`; sem chave ⇒ fallback **LangGraph/Ollama** com log estruturado (`llm_backend_anthropic_sem_api_key`).
- Produção com `anthropic` **exige** chave não vazia (validador `_producao_segredos_obrigatorios`).

## Atualização QDI-H-032b (2026-05-13)

- **`QDI_LLM_BACKEND=openai`** + **`OPENAI_API_KEY`** + **`OPENAI_CHAT_MODEL`** (ou `QDI_OPENAI_CHAT_MODEL`) ⇒ `OpenAiChatLlmAdapter`; sem chave OpenAI ⇒ se **`QDI_LLM_OPENAI_FALLBACK_ANTHROPIC=true`** e **`ANTHROPIC_API_KEY`** válida ⇒ **Anthropic** (`llm_openai_indisponivel_fallback_anthropic`); senão fallback **LangGraph/Ollama** (`llm_backend_openai_sem_api_key`, evento `llm_plano_fallback_backend`).
- Produção com `openai` **exige** `OPENAI_API_KEY` não vazia **ou** `QDI_LLM_OPENAI_FALLBACK_ANTHROPIC=true` com `ANTHROPIC_API_KEY` válida (mesmo validador `_producao_segredos_obrigatorios`).
- A chave **OpenAI** continua a servir também **embeddings** (RAG-light / pgvector) quando `DATABASE_URL` e adapter pgvector estão activos — ver `Settings.openai_embedding_model`.
