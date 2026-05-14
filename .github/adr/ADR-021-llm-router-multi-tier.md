# ADR-021 — Roteamento LLM centralizado (`llm_router`) e tier `QDI_LLM_DEFAULT_TIER`

Data: 2026-05-14  
Estado: aceito (MVP incremental)

## Contexto

A selecção do adapter de recomendação (Anthropic vs Ollama REST vs LangGraph/Ollama) estava embutida em `get_llm_service()` na camada Presentation. O sprint hardening (prompt `09`) pede **router explícito**, **observabilidade** (`provider`, `model`, `tier`, `trace_id` via logger existente) e preparação para **tiers** alinhados a planos (Plus/Pro) sem acoplar JWT/BFF.

Base normativa: **LC 214/2025** — previsibilidade de ambiente e rastreabilidade operacional das saídas que alimentam relatório ao cliente.

## Decisão

1. **Fábrica única** `build_llm_adapter_from_settings()` em `src/infrastructure/adapters/llm_router.py` — mesma precedência actual que **ADR-003** / **ADR-007**:
   - `QDI_LLM_BACKEND=anthropic` + `ANTHROPIC_API_KEY` não vazia → `AnthropicLlmAdapter`;
   - `anthropic` sem chave → `logger.warning` (`llm_backend_anthropic_sem_api_key`) + fallback `LangGraphOllamaLlmAdapter`;
   - `QDI_LLM_BACKEND=http_ollama` → `OllamaLlmAdapter`;
   - default → `LangGraphOllamaLlmAdapter`.
2. **`QDI_LLM_DEFAULT_TIER`** (`local` | `standard` | `premium`, default `local`) — **só observabilidade** na presente versão (evento `llm_router_resolvido`); **não** sobrescreve `QDI_LLM_BACKEND` automaticamente (evita surpresa em dev com chave Anthropic carregada por engano).
3. **Port** `LlmServicePort` passa a **ABC** + `@abstractmethod` (alinhamento à política QDI de ports; substitui `Protocol`).
4. **OpenAI Chat** como backend de recomendação: **fora deste ADR** (embeddings RAG-light continuam em `OPENAI_API_KEY` conforme migração pgvector).

## Consequências

- `get_llm_service()` delega no router — um único sítio para evoluir matriz tier × ambiente (roadmap tenant/plano).
- CI e testes locais **sem** keys OpenAI/Anthropic reais: inalterados (mocks de `get_settings` nos testes existentes).
- Docker: manter **`OLLAMA_BASE_URL=http://host.docker.internal:11434`** no `docker-compose.yml` quando Ollama corre no host; em `uvicorn` no host usar `http://127.0.0.1:11434` (ver README / compose).

## Cruzamento

- **ADR-003** — dev vs prod LLM.  
- **ADR-007** — stack LangGraph + Ollama.  
- **ADR-006** — dependências de IA fora de `src/domain`.
