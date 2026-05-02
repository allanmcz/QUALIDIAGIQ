# ADR-006 — Dependências Python de IA não referenciadas em `src/`

**Data:** 2026-05-02  
**Estado:** Aceite  
**Contexto:** Pacotes `anthropic`, `openai`, `langchain*`, `langgraph` constam em `pyproject.toml` mas o fluxo runtime do MVP usa o adapter **Ollama** (`src/infrastructure/adapters/llm_ollama.py`). Há risco de “dependências mortas” vs preparação para SHOULD (ADR-003).

## Decisão

**Manter as dependências instaladas no pacote principal** até haver corte explícito de roadmap ou migração para extras opcionais (`pip install .[ia-producao]`).

## Alternativas consideradas

| Alternativa | Prós | Contras |
|-------------|------|---------|
| Remover do core e mover para extras | Imagem menor, superfície menor | Quebra ambientes que já fixaram prod com LangChain; retrabalho CI ao ligar SHOULD |
| Remover de vez | Menor attack surface | Perde tração para sprint Anthropic/LangGraph sem reintroduzir deps |

## Consequências

- CI continua resolvendo o mesmo conjunto de pacotes; não há ganho imediato de tempo de install.
- Qualquer novo código em `src/` que use Anthropic/LangChain deve passar por adapter dedicado (Port + Adapter), mantendo Ollama como default dev.
- Revisitar esta ADR quando SHOULD “motor IA produção” entrar em desenvolvimento ativo ou quando métricas de build indicarem custo relevante.

## Referências

- ADR-003 (stack LLM produção planejada)
- `pyproject.toml` — grupo `dependencies` IA / LLM
