# 06 - Checklist Operacional

## Criacao inicial

- [x] Criar pasta `.ollama/`.
- [x] Criar `Modelfile`.
- [x] Criar variante `Modelfile.qwen`.
- [x] Criar contexto resumido do QDI.
- [x] Criar contexto arquitetural.
- [x] Criar regras de codigo.
- [x] Criar script `ask_qdi.sh`.
- [x] Criar documentacao de estudo em `_IA_AVANCADO_DIAG`.

## Validacao Ollama

- [x] Confirmar que Ollama esta instalado.
- [x] Confirmar modelos disponiveis.
- [x] Criar `qdi-assistant`.
- [x] Confirmar que `qdi-assistant` aparece em `/api/tags`.
- [ ] Validar geracao no runtime padrao sem travamento.
- [ ] Recriar `qdi-assistant` com `Modelfile.qwen`.
- [ ] Validar pergunta curta via `ask_qdi.sh`.

## Comandos principais

```bash
ollama list
ollama create qdi-assistant -f .ollama/Modelfile.qwen
.ollama/scripts/ask_qdi.sh "Onde fica uma entidade de dominio no QDI?"
```

## Criterio de sucesso

Uma resposta boa deve mencionar:

- Clean Architecture.
- `src/domain`.
- Entidade sem dependencia de FastAPI, Supabase ou Pydantic externo.
- Casos de uso em `src/application`.
- Persistencia em `src/infrastructure`.
- Schemas HTTP em `src/presentation`.

Exemplo esperado:

```text
No QDI, use Clean Architecture. A entidade DiagnosticoTributario deve ficar em src/domain, pois representa regra central do negocio e nao deve depender de FastAPI, Supabase ou Pydantic de API. Casos de uso que criam ou avaliam o diagnostico ficam em src/application; repositorios concretos em src/infrastructure; schemas HTTP em src/presentation.
```
