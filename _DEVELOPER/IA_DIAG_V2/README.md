# IA_DIAG_V2 — Memoria, Contexto e RAG Local para o QDI

> **Status:** proposta consolidada  
> **Data:** 2026-05-17  
> **Origem:** sintese das propostas Codex + Claude e das 6 rodadas de avaliacao tecnica  
> **Projeto:** QualiDiagIQ (QDI)

## Resposta direta

Esta pasta e a versao executiva da estrategia de IA local do QDI. Ela substitui a leitura dispersa das pastas anteriores por um conjunto menor de documentos decisorios, operacionais e prontos para desenvolvimento incremental.

O objetivo nao e "treinar o Ollama" no sentido de alterar pesos do modelo. O objetivo e construir memoria de projeto em camadas: persona fixa, contexto supervisionado, RAG com fontes confiaveis, benchmark local e integracao gradual com o gateway LLM ja existente no QDI.

## Por onde comecar

Leia nesta ordem:

1. `00_RESUMO_EXECUTIVO.md`
2. `ADR-IA-001-estrategia-hibrida-memoria-rag-local.md`
3. `DECISOES_PENDENTES_ALLAN.md`
4. `ROADMAP_IA_LOCAL_QDI_V1.md`
5. `FASE_A_CHECKLIST_OLLAMA.md`
6. `FASE_B_BENCHMARK_MODELOS.md`
7. `PROMPT_CURSOR_DESENVOLVIMENTO.md`

**Handoff 2026-05-17:** Fases A–D executadas — leia [`reports/HANDOFF_COMPLETO_IA_DIAG_V2.md`](reports/HANDOFF_COMPLETO_IA_DIAG_V2.md).

Depois disso (se reiniciar do zero), execute a Fase A e registre o resultado em `reports/FASE_A_RELATORIO.md`.

## Estrutura da pasta

```text
IA_DIAG_V2/
├── README.md
├── 00_RESUMO_EXECUTIVO.md
├── ADR-IA-001-estrategia-hibrida-memoria-rag-local.md
├── DECISOES_PENDENTES_ALLAN.md
├── ROADMAP_IA_LOCAL_QDI_V1.md
├── FASE_A_CHECKLIST_OLLAMA.md
├── FASE_B_BENCHMARK_MODELOS.md
├── FONTES_E_RAG_POLITICA.md
├── ENSINO_SUPERVISIONADO_QDI.md
├── PROMPT_CURSOR_DESENVOLVIMENTO.md
├── RELATORIO_CONSOLIDACAO_FONTES.md
├── templates/
│   ├── FASE_A_RELATORIO_TEMPLATE.md
│   ├── BENCHMARK_RESPOSTA_TEMPLATE.md
│   └── CASO_SUPERVISIONADO_TEMPLATE.md
├── reports/
└── _FONTES_ORIGINAIS/
    ├── CODEX_BASE/
    ├── CLAUDE_BASE/
    └── AVALIACOES/
```

## Decisao central da V2

A V2 adota uma estrategia hibrida:

| Camada | Decisao |
|---|---|
| Persona local | Manter Modelfile enxuto e versionado |
| Contexto de projeto | Manter arquivos `.md` supervisionados |
| Fontes tributarias | Preparar RAG piloto antes de Lexiq completa |
| Modelo base | Escolher por benchmark local, nao por preferencia previa |
| Integracao com produto | Evoluir o gateway LLM existente, nao criar adapter paralelo sem auditoria |
| Observabilidade | JSONL e logs existentes primeiro; OTel avancado depois |
| Checkpointer | Onda IA 1.1, apos auditoria real do wizard |

## Regra de carga de trabalho

Limite operacional recomendado: **8 a 10 horas por semana** para IA local.

Se a execucao ultrapassar esse limite, reduzir escopo antes de aumentar carga. A meta e evoluir com consistencia, nao transformar IA local em um segundo projeto concorrente ao MVP.

