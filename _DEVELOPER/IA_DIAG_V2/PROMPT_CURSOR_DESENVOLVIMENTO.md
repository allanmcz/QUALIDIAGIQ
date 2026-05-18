# Prompt de Desenvolvimento para o Cursor

> Copie este prompt para o Cursor quando for iniciar a implementacao da IA local V2.

```text
Voce esta trabalhando no projeto QualiDiagIQ (QDI), em:

/Users/allan/000-PROJETOS/018-QUALIDIAGIQ

Leia obrigatoriamente antes de alterar codigo:

1. AGENTS.md
2. _DEVELOPER/IA_DIAG_V2/README.md
3. _DEVELOPER/IA_DIAG_V2/ADR-IA-001-estrategia-hibrida-memoria-rag-local.md
4. _DEVELOPER/IA_DIAG_V2/ROADMAP_IA_LOCAL_QDI_V1.md
5. _DEVELOPER/IA_DIAG_V2/FASE_A_CHECKLIST_OLLAMA.md
6. _DEVELOPER/IA_DIAG_V2/FASE_B_BENCHMARK_MODELOS.md

Objetivo desta tarefa:

Executar apenas a Fase A da estrategia IA_DIAG_V2: estabilizar e diagnosticar o Ollama local, sem alterar codigo de produto em `src/`.

Regras obrigatorias:

- Responder em PT-BR.
- Nao criar adapter novo nesta fase.
- Nao alterar `src/`, `frontend/` ou migrations.
- Nao usar paths `SRC/`; o projeto usa `src/` minusculo.
- Nao fazer commit.
- Nao fazer git push.
- Nao instalar dependencias sem registrar no relatorio.
- Registrar evidencias em `_DEVELOPER/IA_DIAG_V2/reports/FASE_A_RELATORIO.md`.

Passos:

1. Execute os comandos de `_DEVELOPER/IA_DIAG_V2/FASE_A_CHECKLIST_OLLAMA.md`.
2. Registre:
   - versao do Ollama;
   - modelos instalados;
   - resposta de `curl -s http://localhost:11434/api/tags`;
   - resultado do smoke test;
   - portas 11434/11435;
   - qualquer divergencia client/server.
3. Use o template `_DEVELOPER/IA_DIAG_V2/templates/FASE_A_RELATORIO_TEMPLATE.md`.
4. Ao final, diga se a Fase A esta Go, Go com ressalva ou No-Go.

Se a Fase A passar, prepare mas nao execute a Fase B:

- crie ou atualize `_DEVELOPER/IA_DIAG_V2/reports/FASE_B_BENCHMARK_MODELOS.md` apenas com a estrutura inicial;
- liste os modelos candidatos encontrados no `ollama list`;
- nao rode benchmark sem confirmacao de Allan.

Contexto tecnico importante:

O QDI ja possui gateway/adapters LLM existentes:

- `src/domain/ports/llm_gateway.py`
- `src/infrastructure/llm/gateway_router.py`
- `src/infrastructure/adapters/llm_ollama.py`
- `src/infrastructure/adapters/llm_langgraph_ollama.py`
- testes em `tests/unit/infrastructure/llm/` e `tests/unit/infrastructure/test_llm_ollama_adapter*.py`

Portanto, qualquer integracao futura deve auditar e evoluir a base existente, nao criar arquitetura paralela.

Entrega esperada desta tarefa:

- `_DEVELOPER/IA_DIAG_V2/reports/FASE_A_RELATORIO.md` preenchido.
- Resumo final com status Go/No-Go.
- Nenhuma alteracao em codigo de produto.
```

## Prompt para a Fase B, apos Allan aprovar

```text
Agora execute a Fase B da IA_DIAG_V2.

Leia:

- _DEVELOPER/IA_DIAG_V2/FASE_B_BENCHMARK_MODELOS.md
- _DEVELOPER/IA_DIAG_V2/templates/BENCHMARK_RESPOSTA_TEMPLATE.md

Use os modelos aprovados por Allan a partir do `ollama list`.

Para cada modelo, rode as 5 perguntas da Fase B, registre resposta, latencia aproximada e notas da rubrica.

Crie:

_DEVELOPER/IA_DIAG_V2/reports/FASE_B_BENCHMARK_MODELOS.md

Nao altere codigo de produto. Nao faca commit. Ao final, recomende o modelo base com justificativa objetiva.
```

