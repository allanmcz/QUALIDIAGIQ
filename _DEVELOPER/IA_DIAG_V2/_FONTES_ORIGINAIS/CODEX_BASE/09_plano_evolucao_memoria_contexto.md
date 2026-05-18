# 09 - Plano de Evolucao da Memoria e Contexto

## Objetivo

Evoluir a memoria local do QDI de um contexto manual simples para um sistema de conhecimento local com RAG, citacoes e manutencao continua.

## Visao em fases

| Fase | Nome | Resultado |
|---|---|---|
| 0 | Base manual | `.ollama/context` funcionando |
| 1 | Disciplina de registro | Decisoes e regras registradas com templates |
| 2 | Contexto por sprint | Memoria separada por momento do projeto |
| 3 | RAG local | Busca semantica em docs e ADRs |
| 4 | Avaliacao de qualidade | Testes de memoria e respostas esperadas |
| 5 | Governanca | Processo recorrente de revisao e consolidacao |

## Fase 0 - Base manual

Status atual: iniciado.

Entregas:

- `.ollama/Modelfile`
- `.ollama/Modelfile.qwen`
- `.ollama/context/qdi_context.md`
- `.ollama/context/architecture.md`
- `.ollama/context/coding_rules.md`
- `.ollama/scripts/ask_qdi.sh`

Acao de Allan:

```bash
ollama create qdi-assistant -f .ollama/Modelfile.qwen
.ollama/scripts/ask_qdi.sh "Onde fica uma entidade de dominio no QDI?"
```

Criterio de conclusao:

- O modelo responde em PT-BR.
- O modelo menciona Clean Architecture.
- O modelo sabe separar domain, application, infrastructure e presentation.

## Fase 1 - Disciplina de registro

Objetivo:

Padronizar como novas decisoes entram na memoria.

Criar ou manter:

```text
.ollama/context/decisions.md
.ollama/context/scope.md
.ollama/context/glossary.md
```

Sugestao de conteudo:

- `decisions.md`: decisoes tecnicas e produto.
- `scope.md`: o que entra e o que nao entra no MVP.
- `glossary.md`: termos QDI, Tributiq, Winthor, Reforma Tributaria.

Rotina semanal:

1. Revisar decisoes tomadas.
2. Registrar as aceitas.
3. Remover duplicidades.
4. Fazer 3 perguntas de teste.

Criterio de conclusao:

- Toda decisao importante tem data, status e consequencia.

## Fase 2 - Contexto por sprint

Objetivo:

Evitar que a memoria permanente fique poluida por prioridades temporarias.

Criar:

```text
.ollama/context/sprint_current.md
```

Conteudo:

```md
# Sprint Atual

Sprint: 1 de 12
Objetivo:
- <objetivo>

Prioridades:
- <prioridade 1>
- <prioridade 2>

Nao fazer agora:
- <item>
```

Alteracao necessaria:

Adicionar `sprint_current.md` ao array `CONTEXT_FILES` do `ask_qdi.sh`.

Criterio de conclusao:

- O modelo diferencia prioridade da sprint de regra permanente.

## Fase 3 - RAG local

Objetivo:

Parar de enviar documentos grandes inteiros no prompt e recuperar apenas trechos relevantes.

Fontes:

- `AGENTS.md`
- `docs/refs/*.md`
- ADRs
- documentos de dominio
- documentos normativos permitidos

Stack sugerida:

- Python 3.12
- `mxbai-embed-large:latest` para embeddings
- ChromaDB ou FAISS
- Script `build_index.py`
- Script `ask_rag.py`

Criterio de conclusao:

- Perguntas sobre PRD retornam trechos citados.
- Perguntas sem fonte retornam "base insuficiente".

## Fase 4 - Avaliacao de qualidade

Objetivo:

Criar testes de memoria.

Criar:

```text
_IA_AVANCADO_DIAG/testes_memoria.md
```

Exemplo:

```md
## Teste 001 - Entidade de dominio

Pergunta:
Onde fica DiagnosticoTributario?

Deve conter:
- src/domain
- sem dependencia externa
- application orquestra caso de uso

Nao pode conter:
- schema FastAPI dentro do domain
- SQL dentro da entidade
```

Criterio de conclusao:

- Pelo menos 10 testes cobrindo arquitetura, stack, escopo e RAG.

## Fase 5 - Governanca

Objetivo:

Manter a memoria util e limpa.

Rotina quinzenal:

1. Consolidar decisoes duplicadas.
2. Marcar decisoes substituidas.
3. Mover conhecimento grande para RAG.
4. Manter `Modelfile` pequeno.
5. Rodar testes de memoria.

Regra de ouro:

Memoria boa e como cadastro fiscal bem cuidado: se duplicar, contradizer ou ficar desatualizada, o diagnostico perde confiabilidade.

## Roadmap pratico de 30 dias

| Semana | Foco | Entrega |
|---|---|---|
| 1 | Validar Ollama e memoria enxuta | `qdi-assistant` respondendo corretamente |
| 2 | Criar `decisions.md`, `scope.md`, `glossary.md` | Contexto organizado |
| 3 | Criar primeiros testes de memoria | 10 perguntas com resposta esperada |
| 4 | Prototipar RAG local | Busca em `docs/refs` com citacoes |

## Ritual recomendado para Allan

Em cada bloco de 45 minutos:

1. Escolha uma decisao ou conceito.
2. Registre usando template.
3. Faça uma pergunta de teste.
4. Ajuste a memoria.
5. Anote o resultado.
