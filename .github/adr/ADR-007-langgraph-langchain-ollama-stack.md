# ADR-007 — Stack IA diferenciada: LangGraph + LangChain + Ollama (conjunto)

**Data:** 2026-05-02  
**Estado:** Aceite  
**Decisor:** Produto (Allan) — execução técnica no repo.

## Contexto

O QDI precisa de uma stack IA **extensível** (grafos multi-passo, RAG futuro, ferramentas) mantendo **Ollama** como runtime local/dev e custo previsível. LangChain e LangGraph não substituem o Ollama: orquestram o fluxo; o servidor **Ollama** continua a expor o modelo.

## Decisão

1. **Runtime default da API:** ``LangGraphOllamaLlmAdapter`` — grafo LangGraph com nó que invoca **LangChain ``ChatOllama``** contra o endpoint configurado (**``OLLAMA_BASE_URL``**, **``OLLAMA_MODEL``**, **``OLLAMA_TIMEOUT_SECONDS``**).
2. **Fallback operacional:** ``QDI_LLM_BACKEND=http_ollama`` usa ``OllamaLlmAdapter`` (REST **httpx**, legado).
3. **Port unchanged:** ``LlmServicePort`` (ABC) — domínio/casos de uso não dependem de LangChain.

## Consequências

- Dependência explícita **``langchain-ollama``** (``ChatOllama`` oficialmente suportado; evita depreciação do wrapper em ``langchain-community``).
- Evolução natural: novos nós no grafo (ex.: retrieval Lexiq) sem reescrever o caso de uso **RealizarDiagnostico**.
- ADR-003 mantém-se para **modelo declarado ao cliente** em produção paga (Claude/API etc.); troca de provedor continua por adapter + env.

## Referências

- ``src/infrastructure/adapters/llm_langgraph_ollama.py``
- ADR-003, ADR-006
