# 00 — Resumo Executivo da Proposta V2

## Resposta direta

A proposta V2 recomenda sair da meta-analise e iniciar execucao controlada. O caminho correto e estabilizar o Ollama, auditar o que ja existe no QDI, fazer benchmark com modelos locais e so depois integrar RAG piloto ao gateway LLM existente.

A decisao mais importante: **nao criar uma arquitetura paralela**. O projeto ja possui `src/domain/ports/llm_gateway.py`, `src/infrastructure/llm/gateway_router.py`, adapters LLM, testes e guardrails; portanto a IA local deve entrar como evolucao incremental dessa base.

## O que foi consolidado

| Origem | Contribuicao aproveitada |
|---|---|
| Codex base | didatica de memoria, ensino supervisionado, pipeline de fontes, templates |
| Claude base | arquitetura em camadas, RAG Lexiq, adapter, benchmark, riscos |
| Avaliacoes cruzadas | correcao de escopo, cronograma, paths reais, gates e decisao por benchmark |
| Codigo atual QDI | gateway LLM ja existente, guardrails, testes, Clean Architecture em `src/` minusculo |

## Principios da V2

1. **Executar pequeno, medir cedo.**
2. **Modelo base sera escolhido por benchmark local.**
3. **RAG piloto antes de Lexiq completa.**
4. **Citar fonte ou recusar resposta tributaria.**
5. **Preservar Clean Architecture.**
6. **Usar `src/`, nao `SRC/`.**
7. **Nao duplicar adapters sem auditoria.**
8. **Registrar aprendizado supervisionado em arquivos versionados.**
9. **Manter saude e foco: 8 a 10h/semana.**
10. **So reabrir debate tecnico com dados reais.**

## O que muda em relacao as propostas anteriores

| Tema | Antes | V2 |
|---|---|---|
| Modelo | Qwen 14B quase decidido | Qwen 14B e candidato; benchmark decide |
| RAG | Lexiq completa logo no inicio | Piloto com corpus pequeno e confiavel |
| Adapter | Criar novo adapter | Auditar gateway/adapters existentes primeiro |
| Checkpointer | Entrava cedo | Onda IA 1.1 |
| Observabilidade | OTel/Jaeger cedo | JSONL/logs primeiro, OTel depois |
| Cronograma | 5 sprints densas | Fases A-D ate 30/jun/2026, E-H depois |

## Resultado esperado ate 30/jun/2026

Ao final da Onda 1.0, o QDI deve ter:

- Ollama local estavel.
- Relatorio da Fase A.
- Benchmark com 3 modelos e 5 perguntas.
- Decisao registrada sobre modelo base.
- Politica de fontes e catalogo inicial.
- RAG piloto validado por script.
- Prompt e contexto supervisionado versionados.
- Plano claro para integrar ao gateway LLM sem quebrar o MVP.

## Analogias praticas

Pense na V2 como a criacao de um novo modulo fiscal no Winthor:

- primeiro estabiliza ambiente;
- depois homologa cadastros;
- depois roda massa pequena de teste;
- depois amplia para regras oficiais;
- so entao integra no fluxo operacional.

No Oracle, seria equivalente a criar staging, validar carga, criar indices, medir plano de execucao e so depois plugar no processo de fechamento.

