# FASE D — RAG Piloto com Citacao

> **Data:** 2026-05-17  
> **Script:** `scripts/ia_diag_v2_fase_d_rag_piloto.py`  
> **Dados brutos:** `reports/fase_d_rag_piloto.json`  
> **Status:** **Go** (docs QDI) · **Go com ressalva** (PDFs dominio_fiscal ainda nao extraidos)

## Escopo do piloto

| Item | Valor |
|------|--------|
| Embedding | `mxbai-embed-large:latest` via `POST /api/embed` |
| Chunks | 93 (4 arquivos Markdown `docs/refs/`) |
| Threshold similaridade | 0.45 |
| Catalogo | `dominio_fiscal/catalogo_fontes.yml` (15 fontes piloto) |

## Resultados das 4 perguntas-teste

| Pergunta | Status | Melhor score | Fonte top |
|----------|--------|-------------|-----------|
| Escopo MVP QDI | com_fonte | 0.746 | FONTE-020 PRD |
| Calculo score 0-100 | com_fonte | 0.709 | FONTE-023 / FONTE-022 |
| cClassTrib reforma | com_fonte | 0.724 | FONTE-020 / FONTE-023 |
| Apurar CBS no QDI | com_fonte | 0.692 | FONTE-023 |

**Gate DP-006:** todas as perguntas sobre produto/escopo recuperaram chunk citavel — **passou** para corpus Markdown.

**Ressalva:** pergunta "cClassTrib" recuperou PRD/questionario, nao NT 2025.002 PDF (ainda nao indexado). Proximo passo: pipeline de extracao PDF → `dominio_fiscal/extraido/`.

## Problemas tecnicos

- 3 chunks falharam embed (HTTP 400) — caracteres ou tamanho; 90/93 OK.
- Corpus normativo classe A (LC 214 PDF) **fora** deste piloto ate extracao.

## Decisao

```text
Go para ampliar corpus com extracao PDF das fontes FONTE-001..009.
Go/No-Go integracao produto (Fase E): condicionado a unificar Ollama + revisar benchmark generativo.
```

## Comando de reproducao

```bash
cd /Users/allan/000-PROJETOS/018-QUALIDIAGIQ
PYTHONPATH=. python scripts/ia_diag_v2_fase_d_rag_piloto.py
```
