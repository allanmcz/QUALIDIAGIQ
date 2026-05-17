# 11 - Roteiro de Estudo em Blocos de 45 Minutos

Este roteiro respeita blocos curtos de estudo e evita tentar absorver tudo de uma vez.

## Bloco 1 - Entender as camadas

Tempo: 45 minutos

Objetivo:

Entender a diferenca entre memoria fixa, contexto injetado e RAG.

Leia:

- `01_conceitos.md`
- `02_arquitetura_da_memoria.md`

Pratica:

```bash
sed -n '1,200p' .ollama/Modelfile
sed -n '1,200p' .ollama/context/qdi_context.md
```

Pergunta de fechamento:

```bash
.ollama/scripts/ask_qdi.sh "Explique a diferenca entre Modelfile, contexto e RAG usando analogia com Oracle"
```

## Bloco 2 - Ensinar uma decisao

Tempo: 45 minutos

Objetivo:

Registrar uma decisao tecnica usando template.

Leia:

- `07_como_ensinar_memoria.md`
- `08_templates_de_memoria.md`

Pratica:

1. Escolha uma decisao pequena.
2. Registre em `.ollama/context/qdi_context.md`.
3. Teste com uma pergunta direta.

Exemplo:

```bash
.ollama/scripts/ask_qdi.sh "Qual ERP o QDI deve priorizar primeiro e por quê?"
```

## Bloco 3 - Separar regra permanente de regra viva

Tempo: 45 minutos

Objetivo:

Aprender quando alterar `Modelfile` e quando alterar contexto.

Leia:

- `03_comandos_ollama.md`
- `10_checklist_qualidade_memoria.md`

Pratica:

Classifique 5 informacoes:

| Informacao | Modelfile ou Contexto? |
|---|---|
| Sempre responder em PT-BR | Modelfile |
| Winthor como primeiro ERP | Contexto |
| Sprint atual prioriza wizard | Contexto de sprint |
| Usar Clean Architecture | Modelfile e architecture.md |
| Nova decisao de ADR | Contexto e futuro RAG |

## Bloco 4 - Plano de evolucao

Tempo: 45 minutos

Objetivo:

Planejar a evolucao para RAG local.

Leia:

- `05_proximo_passo_rag_local.md`
- `09_plano_evolucao_memoria_contexto.md`

Pratica:

Crie uma lista de 10 perguntas que o RAG do QDI deve responder com citacao.

Exemplos:

- Quais sao as features MUST do MVP?
- Quais itens estao fora de escopo?
- Qual diferencial competitivo do QDI frente ao Cosmos?
- Como o QDI deve tratar ABNT NBR 17301?

## Bloco 5 - Auditoria da memoria

Tempo: 45 minutos

Objetivo:

Testar se a memoria responde de forma consistente.

Leia:

- `10_checklist_qualidade_memoria.md`

Pratica:

Rode:

```bash
.ollama/scripts/ask_qdi.sh "O que esta fora do MVP do QDI?"
.ollama/scripts/ask_qdi.sh "Onde fica uma entidade de dominio?"
.ollama/scripts/ask_qdi.sh "Como devo tratar regra tributaria com vigencia?"
```

Anote:

- O que respondeu bem.
- O que respondeu generico.
- O que precisa ser ensinado melhor.

## Regra de pausa

Ao final de cada bloco:

- Levante.
- Hidrate.
- Anote uma unica melhoria para o proximo bloco.

O objetivo nao e decorar. E construir uma memoria que trabalhe junto com voce.
