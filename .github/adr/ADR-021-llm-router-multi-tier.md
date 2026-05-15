# ADR-021 — Roteamento LLM centralizado (`llm_router`) e tier `QDI_LLM_DEFAULT_TIER`

Data: 2026-05-14  
Estado: aceito (MVP incremental)

## Contexto

A selecção do adapter de recomendação (Anthropic vs Ollama REST vs LangGraph/Ollama vs OpenAI Chat) estava embutida em `get_llm_service(Request)` na camada Presentation. O sprint hardening (prompt `09`) pede **router explícito**, **observabilidade** (`provider`, `model`, `tier`, `trace_id` via logger existente) e preparação para **tiers** alinhados a planos (Plus/Pro) sem acoplar JWT/BFF.

Base normativa: **LC 214/2025** — previsibilidade de ambiente e rastreabilidade operacional das saídas que alimentam relatório ao cliente.

## Decisão

1. **Fábrica única** `build_llm_adapter_from_settings()` em `src/infrastructure/adapters/llm_adapter_factory.py` — precedência:
   - `QDI_LLM_BACKEND=openai` + `OPENAI_API_KEY` não vazia → `OpenAiChatLlmAdapter` (`OPENAI_CHAT_MODEL` / `QDI_OPENAI_CHAT_MODEL`);
   - `openai` sem chave → se ``QDI_LLM_OPENAI_FALLBACK_ANTHROPIC=true`` e ``ANTHROPIC_API_KEY`` válida → ``AnthropicLlmAdapter`` (log ``llm_openai_indisponivel_fallback_anthropic``); caso contrário ``logger.warning`` (`llm_backend_openai_sem_api_key`) + fallback ``LangGraphOllamaLlmAdapter``;
   - `QDI_LLM_BACKEND=anthropic` + `ANTHROPIC_API_KEY` não vazia → `AnthropicLlmAdapter`;
   - `anthropic` sem chave → `logger.warning` (`llm_backend_anthropic_sem_api_key`) + fallback `LangGraphOllamaLlmAdapter`;
   - `QDI_LLM_BACKEND=http_ollama` → `OllamaLlmAdapter`;
   - default → `LangGraphOllamaLlmAdapter`.
2. **Tier observável (plano 2.3.1)** — `resolver_tier_efetivo_observabilidade` em `src/application/services/llm_tier_observabilidade.py`; **não** altera `QDI_LLM_BACKEND`. Precedência: parâmetro opcional `tier_use_case` em `build_llm_adapter_from_settings` > claim JWT assinada `qdi_llm_tier` > `perfil_conta` do JWT (`gratuito`→local, `avancado`→standard, `admin`→premium) > `QDI_LLM_DEFAULT_TIER` > fallback por `APP_ENV` (`production`→`standard`, caso contrário `local`). `get_llm_service(Request)` lê `Authorization` via `jwt_llm_tier_context.py`. O use case `RealizarDiagnostico` emite `diagnostico_llm_tier_plano_observabilidade` com tier derivado do plano do comando (complemento ao router). **Proibido** tier a partir de header HTTP público (decisão 4).
3. **Port** `LlmServicePort` é **ABC** + `@abstractmethod` (alinhamento à política QDI de ports; substitui `Protocol`).
4. **Segurança (tier “premium”)**: em **produção**, **proibido** usar header HTTP público (ex.: `X-QDI-LLM-Tier`) como fonte directa de roteamento para modelo pago — qualquer evolução passa por **config** (`Settings`) / **claims** de confiança no JWT ou política interna documentada.

## Consequências

- `get_llm_service(Request)` delega no router e resolve tier a partir do **Bearer JWT** assinado + Settings.
- CI e testes locais **sem** keys reais: mocks de `get_settings` / `AsyncOpenAI` nos testes unitários.
- Docker: manter **`OLLAMA_BASE_URL=http://host.docker.internal:11434`** no `docker-compose.yml` quando Ollama corre no host; em `uvicorn` no host usar `http://127.0.0.1:11434` (ver README / compose).
- **Use case** `RealizarDiagnostico`: `try/except` à volta de `gerar_recomendacao` — se qualquer adapter lançar excepção não prevista, o diagnóstico **não falha**; devolve mensagem estável de indisponibilidade de IA (PDF e persistência seguem).
- **2.3.5 (produção):** opt-in ``QDI_LLM_OPENAI_FALLBACK_ANTHROPIC`` — com ``QDI_LLM_BACKEND=openai`` sem chave OpenAI, usar Claude se Anthropic estiver configurado; validação em ``Settings._producao_segredos_obrigatorios`` exige Anthropic válido nesse modo.

## Cruzamento

- **ADR-003** — dev vs prod LLM.  
- **ADR-007** — stack LangGraph + Ollama.  
- **ADR-006** — dependências de IA fora de `src/domain`.
