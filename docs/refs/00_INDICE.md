# Documentos de Referência — Snapshot da Discovery do QDI

> Esses 7 documentos foram **copiados em 2026-04-26** da pasta de pesquisa original `DIAGNOSTICO_REFORMA_MANUS/`.
> Tornam este scaffold **autossuficiente** — qualquer Claude Code, Cursor ou ChatGPT pode trabalhar sem acesso a paths externos.
> **Atenção:** se a pesquisa-fonte for atualizada, esses arquivos podem ficar desatualizados — verifique.

## Índice

| # | Arquivo | Conteúdo | Quando consultar |
|---|---------|----------|------------------|
| 01 | [01_PRD_BASE.md](./01_PRD_BASE.md) | Estrutura completa do PRD do QDI | Ao redigir PRD oficial |
| 02 | [02_MOSCOW_FEATURES.md](./02_MOSCOW_FEATURES.md) | MoSCoW priorizado (12 MUST + 11 SHOULD + 10 COULD) | Para validar escopo de feature |
| 03 | [03_GAP_ANALYSIS.md](./03_GAP_ANALYSIS.md) | 5 vetores de diferenciação competitiva | Para reforçar diferenciais no código |
| 04 | [04_METODOLOGIA.md](./04_METODOLOGIA.md) | Fluxograma 8 etapas + algoritmo de score | Para implementar use case principal |
| 05 | [05_QUESTIONARIO_v1.md](./05_QUESTIONARIO_v1.md) | Banco de 35 perguntas + pesos + base legal | **Essencial** para implementar wizard |
| 06 | [06_MATRIZ_COMPETITIVA.md](./06_MATRIZ_COMPETITIVA.md) | 7 concorrentes × 15 dimensões | Para entender posicionamento |
| 07 | [07_ESTRATEGIA_GERAL.md](./07_ESTRATEGIA_GERAL.md) | Visão de produto + tiers Free/Plus/Pro/Enterprise | Para decisões de UX e gating |

## Fonte original

Pasta-mãe: `DIAGNOSTICO_REFORMA_MANUS/` — preserva o histórico completo da Discovery (62 arquivos, ~35.500 palavras).

## Como atualizar estes documentos

Caso a pesquisa-fonte seja atualizada:

```bash
# A partir do diretório-raiz do scaffold (018-QUALIDIAGIQ/)
cp ../path/to/DIAGNOSTICO_REFORMA_MANUS/03_GAP_ANALYSIS_QDI/recomendacoes_prd_qdi.md docs/refs/01_PRD_BASE.md
# ... etc
```

Ou, se você fez `git clone` do scaffold em outro local sem acesso à pesquisa-fonte, esses arquivos permanecem como **snapshot histórico** da discovery em 2026-04-26.
