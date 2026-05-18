# ADR-IA-001 — Estrategia Hibrida de Memoria, Contexto e RAG Local

> **Status:** Proposto  
> **Data:** 2026-05-17  
> **Decisores:** Allan + Codex  
> **Contexto:** QualiDiagIQ (QDI), IA local com Ollama, RAG tributario e integracao futura ao gateway LLM

## 1. Contexto

O QDI precisa de uma estrategia de IA local para estudo, desenvolvimento, validacao de respostas e eventual apoio ao produto. As discussoes anteriores produziram duas linhas complementares:

- uma linha didatica e incremental, focada em memoria/contexto com Ollama;
- uma linha arquitetural, focada em RAG, pgvector, adapter, benchmark e checkpointer.

As avaliacoes cruzadas convergiram para uma proposta hibrida, com execucao faseada e decisao por dados reais.

## 2. Decisao

Adotar memoria e contexto local em quatro camadas, mas implementar de forma incremental:

| Camada | Decisao V2 |
|---|---|
| 1. Persona | Modelfile enxuto para persona QDI e regras permanentes |
| 2. Contexto supervisionado | Arquivos Markdown versionados e revisados por Allan |
| 3. RAG factual | Piloto com fontes A/B antes de indexacao ampla |
| 4. Historico/episodica | Postergar Checkpointer para Onda IA 1.1 |

## 3. Decisoes aprovadas

1. O Ollama sera usado como ambiente local de desenvolvimento, estudo e benchmark.
2. A IA local nao substitui de imediato o provider de producao.
3. O modelo base sera escolhido apos benchmark local.
4. Qwen 2.5 14B Instruct e candidato preferencial, nao decisao previa.
5. `nomic-embed-text`, `mxbai-embed-large` e/ou `bge-m3` serao comparados conforme disponibilidade local.
6. RAG tributario deve citar fonte valida ou declarar base insuficiente.
7. RAG piloto vira gate antes de Lexiq completa.
8. O gateway LLM existente deve ser auditado antes de criar novo adapter.
9. Paths oficiais do projeto usam `src/` minusculo.
10. Observabilidade completa com OTel/Jaeger fica fora da primeira onda se logs JSONL bastarem.
11. Checkpointer LangGraph fica para Onda IA 1.1, apos auditoria do wizard.
12. A carga operacional recomendada e 8 a 10h/semana.

## 4. Decisoes pendentes de Allan

As decisoes abaixo precisam ser marcadas em `DECISOES_PENDENTES_ALLAN.md`:

| ID | Decisao | Opcoes |
|---|---|---|
| DP-001 | Modelo inicial para benchmark | Qwen 14B, Llama 8B, Phi/Mistral, modelos ja instalados |
| DP-002 | Corpus piloto | Legislacao oficial apenas, ou legislacao + docs QDI |
| DP-003 | Local fisico das fontes | `dominio_fiscal/`, `docs/legal/`, ou estrutura nova |
| DP-004 | Integração no codigo | Apenas scripts primeiro, ou branch de adapter apos Fase B |
| DP-005 | Janela semanal | 8h, 10h, ou outro limite definido por Allan |

## 5. Consequencias positivas

- Reduz risco de arquitetura paralela.
- Forca benchmark antes de preferencia de modelo.
- Protege o MVP de escopo excessivo.
- Mantem auditabilidade tributaria.
- Cria aprendizado supervisionado conduzivel por Allan.
- Permite evoluir de script local para produto sem salto grande.

## 6. Consequencias negativas

- O ganho imediato e menor do que implementar tudo de uma vez.
- Algumas decisoes ficam pendentes ate haver dados reais.
- A Lexiq completa demora mais para entrar.
- Checkpointer e memoria episodica ficam para uma segunda onda.

## 7. Gates de qualidade

| Fase | Gate minimo |
|---|---|
| A | Ollama responde localmente e versoes estao documentadas |
| B | Benchmark com 3 modelos x 5 perguntas concluido |
| C | Contexto supervisionado revisado por Allan |
| D | RAG piloto retorna fonte ou base insuficiente |
| E | Integracao ao gateway respeita testes existentes |

## 8. Criterio de revisao deste ADR

Este ADR deve ser revisado quando houver:

- resultado do benchmark Fase B;
- primeira prova de RAG piloto;
- decisao de integrar IA local ao fluxo FastAPI;
- mudanca relevante no gateway LLM existente;
- decisao de usar Checkpointer em producao.

