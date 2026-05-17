# Memoria Local Ollama do QDI

Esta pasta cria um assistente local do projeto QualiDiagIQ usando Ollama.

## Criar ou atualizar o modelo

```bash
ollama create qdi-assistant -f .ollama/Modelfile
```

Se o servidor Ollama local tiver `qwen2.5-coder:7b`, esta variante costuma ser melhor para codigo:

```bash
ollama create qdi-assistant -f .ollama/Modelfile.qwen
```

## Perguntar com contexto do projeto

```bash
.ollama/scripts/ask_qdi.sh "Explique como modelar DiagnosticoTributario no domain"
```

Para incluir tambem `AGENTS.md` e `docs/refs`, use:

```bash
.ollama/scripts/ask_qdi.sh --full "Compare esta decisao com o PRD-base"
```

## Como funciona

- `.ollama/Modelfile` define a memoria fixa do modelo.
- `.ollama/context/*.md` guarda contexto textual do QDI.
- `.ollama/scripts/ask_qdi.sh` injeta o contexto no prompt antes da pergunta.

Isto e uma memoria textual injetada no prompt, nao uma memoria viva. O proximo passo natural e adicionar RAG local sobre `docs/refs/`, `AGENTS.md` e decisoes arquiteturais.
