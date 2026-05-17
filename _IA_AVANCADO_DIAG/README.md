# IA Avancado DIAG - Memoria, Contexto e RAG Local

Esta pasta documenta o estudo e a implementacao inicial de memoria/contexto local para o projeto QualiDiagIQ usando Ollama.

## Objetivo

Criar uma base de estudo para entender como um modelo local pode responder considerando:

- Persona tecnica do projeto QDI.
- Arquitetura obrigatoria.
- Stack definida no `AGENTS.md`.
- Regras de codigo e qualidade.
- Documentos de referencia em `docs/refs`.

## Resultado implementado no projeto

Foi criada a pasta `.ollama/` com:

```text
.ollama/
├── Modelfile
├── Modelfile.qwen
├── README.md
├── context/
│   ├── architecture.md
│   ├── coding_rules.md
│   └── qdi_context.md
└── scripts/
    └── ask_qdi.sh
```

## Ordem sugerida de estudo

1. Leia `01_conceitos.md`.
2. Leia `02_arquitetura_da_memoria.md`.
3. Leia `03_comandos_ollama.md`.
4. Leia `04_diagnostico_do_teste.md`.
5. Leia `05_proximo_passo_rag_local.md`.
6. Leia `07_como_ensinar_memoria.md`.
7. Use `08_templates_de_memoria.md` para registrar novas decisoes.
8. Conduza a evolucao com `09_plano_evolucao_memoria_contexto.md`.
9. Audite a qualidade usando `10_checklist_qualidade_memoria.md`.

## Ideia central

O Ollama nao possui memoria persistente de projeto por padrao. O que criamos aqui e uma memoria projetada em camadas:

| Camada | Arquivo | Funcao |
|---|---|---|
| Identidade fixa | `.ollama/Modelfile` | Persona, stack e regras permanentes |
| Contexto textual | `.ollama/context/*.md` | Memoria resumida do QDI |
| Injetor de prompt | `.ollama/scripts/ask_qdi.sh` | Junta contexto + pergunta |
| Futuro RAG | A implementar | Busca trechos relevantes automaticamente |

Analogia com Oracle/Winthor: o `Modelfile` funciona como parametro global do sistema; os arquivos `.md` sao tabelas de configuracao; e o RAG sera como uma consulta indexada que busca apenas os registros relevantes para a pergunta.

## Documentos de conducao criados

| Arquivo | Finalidade |
|---|---|
| `07_como_ensinar_memoria.md` | Manual pratico para ensinar novas informacoes ao contexto |
| `08_templates_de_memoria.md` | Modelos prontos para registrar decisoes, regras e excecoes |
| `09_plano_evolucao_memoria_contexto.md` | Plano de evolucao em fases para Allan conduzir |
| `10_checklist_qualidade_memoria.md` | Checklist para revisar se a memoria esta boa |
| `11_roteiro_de_estudo_45min.md` | Roteiro em blocos de estudo de 45 minutos |
| `12_como_transformar_fontes_em_contexto.md` | Como usar aulas, legislacao, PDFs e anotacoes como fontes |
| `13_catalogo_de_fontes_qdi.md` | Modelo de catalogo para controlar origem, confiabilidade e vigencia |
| `14_pipeline_fontes_para_rag.md` | Pipeline pratico para preparar fontes para RAG local |
| `15_ensino_supervisionado.md` | Como ensinar o agente com correcao humana, rubricas e promocao de memoria |
| `16_caderno_treino_supervisionado.md` | Modelo de caderno para perguntas, respostas esperadas e correcoes |
