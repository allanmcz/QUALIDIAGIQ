# ADR-006 — Dependências Python de IA não referenciadas em `src/`

**Data:** 2026-05-02  
**Estado:** Aceite  
**Contexto:** Pacotes `anthropic`, `openai`, `langchain*`, `langgraph` constam em `pyproject.toml`. Até **2026-05-02** o runtime MVP usava só **REST httpx** ao Ollama (`llm_ollama.py`). **ADR-007** passou a usar **LangGraph + LangChain + Ollama** em `src/` com fallback HTTP opcional.

## Decisão

**Manter as dependências instaladas no pacote principal** até haver corte explícito de roadmap ou migração para extras opcionais (`pip install .[ia-producao]`).

## Alternativas consideradas

| Alternativa | Prós | Contras |
|-------------|------|---------|
| Remover do core e mover para extras | Imagem menor, superfície menor | Quebra ambientes que já fixaram prod com LangChain; retrabalho CI ao ligar SHOULD |
| Remover de vez | Menor attack surface | Perde tração para sprint Anthropic/LangGraph sem reintroduzir deps |

## Consequências

- CI continua resolvendo o mesmo conjunto de pacotes; não há ganho imediato de tempo de install.
- Qualquer novo código em `src/` que use Anthropic/LangChain deve passar por adapter dedicado (Port + Adapter), mantendo **Ollama** como backend default dev.
- Revisitar esta ADR quando SHOULD “motor IA produção” entrar em desenvolvimento ativo ou quando métricas de build indicarem custo relevante.

## Referências

- ADR-003 (stack LLM produção planejada)
- **ADR-007** (LangGraph + LangChain + Ollama em runtime)
- `pyproject.toml` — grupo `dependencies` IA / LLM
