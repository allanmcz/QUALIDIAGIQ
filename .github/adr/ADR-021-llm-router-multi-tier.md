# ADR-021 — Roteamento LLM centralizado (`llm_router`) e tier `QDI_LLM_DEFAULT_TIER`

Data: 2026-05-14  
Estado: aceito (MVP incremental)

## Contexto

A selecção do adapter de recomendação (Anthropic vs Ollama REST vs LangGraph/Ollama vs OpenAI Chat) estava embutida em `get_llm_service()` na camada Presentation. O sprint hardening (prompt `09`) pede **router explícito**, **observabilidade** (`provider`, `model`, `tier`, `trace_id` via logger existente) e preparação para **tiers** alinhados a planos (Plus/Pro) sem acoplar JWT/BFF.

Base normativa: **LC 214/2025** — previsibilidade de ambiente e rastreabilidade operacional das saídas que alimentam relatório ao cliente.

## Decisão

1. **Fábrica única** `build_llm_adapter_from_settings()` em `src/infrastructure/adapters/llm_router.py` — precedência:
   - `QDI_LLM_BACKEND=openai` + `OPENAI_API_KEY` não vazia → `OpenAiChatLlmAdapter` (`OPENAI_CHAT_MODEL` / `QDI_OPENAI_CHAT_MODEL`);
   - `openai` sem chave → `logger.warning` (`llm_backend_openai_sem_api_key`) + fallback `LangGraphOllamaLlmAdapter`;
   - `QDI_LLM_BACKEND=anthropic` + `ANTHROPIC_API_KEY` não vazia → `AnthropicLlmAdapter`;
   - `anthropic` sem chave → `logger.warning` (`llm_backend_anthropic_sem_api_key`) + fallback `LangGraphOllamaLlmAdapter`;
   - `QDI_LLM_BACKEND=http_ollama` → `OllamaLlmAdapter`;
   - default → `LangGraphOllamaLlmAdapter`.
2. **`QDI_LLM_DEFAULT_TIER`** (`local` | `standard` | `premium`, default `local`) — **só observabilidade** na presente versão (evento `llm_router_resolvido`); **não** sobrescreve `QDI_LLM_BACKEND` automaticamente (evita surpresa em dev com chave Anthropic/OpenAI carregada por engano). **Matriz tier × plano × use case** fica para roadmap (tenant/plano no JWT ou serviço de billing — nunca header HTTP público).
3. **Port** `LlmServicePort` é **ABC** + `@abstractmethod` (alinhamento à política QDI de ports; substitui `Protocol`).
4. **Segurança (tier “premium”)**: em **produção**, **proibido** usar header HTTP público (ex.: `X-QDI-LLM-Tier`) como fonte directa de roteamento para modelo pago — qualquer evolução passa por **config** (`Settings`) / **claims** de confiança no JWT ou política interna documentada.

## Consequências

- `get_llm_service()` delega no router — um único sítio para evoluir matriz tier × ambiente (roadmap tenant/plano).
- CI e testes locais **sem** keys reais: mocks de `get_settings` / `AsyncOpenAI` nos testes unitários.
- Docker: manter **`OLLAMA_BASE_URL=http://host.docker.internal:11434`** no `docker-compose.yml` quando Ollama corre no host; em `uvicorn` no host usar `http://127.0.0.1:11434` (ver README / compose).
- **Use case** `RealizarDiagnostico`: `try/except` à volta de `gerar_recomendacao` — se qualquer adapter lançar excepção não prevista, o diagnóstico **não falha**; devolve mensagem estável de indisponibilidade de IA (PDF e persistência seguem).

## Cruzamento

- **ADR-003** — dev vs prod LLM.  
- **ADR-007** — stack LangGraph + Ollama.  
- **ADR-006** — dependências de IA fora de `src/domain`.
