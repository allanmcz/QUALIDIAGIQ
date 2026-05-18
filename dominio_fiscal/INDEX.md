# Índice — domínio fiscal (corpus RAG local)

> **Atualizado:** 2026-05-17  
> **Catálogo machine-readable:** [`catalogo_fontes.yml`](catalogo_fontes.yml)  
> **Política:** [`_DEVELOPER/IA_DIAG_V2/FONTES_E_RAG_POLITICA.md`](../_DEVELOPER/IA_DIAG_V2/FONTES_E_RAG_POLITICA.md)

## Resposta direta

Esta pasta concentra **fontes brutas** da Reforma Tributária (PDF, DOCX, XLSX, PPTX). O RAG piloto usa primeiro as entradas com `piloto: true` no catálogo YAML; o restante fica para formação humana ou ondas posteriores.

---

## Estrutura física

| Pasta | Ficheiros | Papel |
|-------|----------:|-------|
| `01_LEGISLACAO_BASE/` | 6 | EC 132, LC 214, LC 225, LC 227 |
| `02_MANUAIS_E_RTC/` | 7 | Manuais RFB, glossário, apuração assistida |
| `03_DOCUMENTOS_FISCAIS_E_TABELAS/` | 9 | NT 2025.002, IT, cClassTrib, cCredPres, NCM |
| `04_CONCEITOS_E_TEMAS/` | 6 | Neutralidade, IS, transição (classe C) |
| `05_NOTAS_TECNICAS_E_CARTILHAS/` | 7 | Cartilhas, resumos PLP-68 |
| `06_APRESENTACOES/` | 4 | Slides — **fora do piloto RAG** |
| `07_COMPLIANCE_E_FERRAMENTAS/` | 13 | POPs, checklists cliente — **fora do piloto RAG** |
| `08_REFERENCIAS_ORIGINAIS/` | 6 | Metodologia CIRT (Markdown) |

**Total:** ~58 ficheiros · ~43 MB

Documentos QDI (classe B) permanecem em `docs/refs/` — listados no catálogo como FONTE-020…024.

---

## Corpus piloto (prioridade 1 — indexar na Fase D)

| ID | Título | Caminho |
|----|--------|---------|
| FONTE-001 | EC 132/2023 | `01_LEGISLACAO_BASE/EMENDA CONSTITUCIONAL 132 2023.pdf` |
| FONTE-002 | LC 214/2025 | `01_LEGISLACAO_BASE/LC-214-2025_texto_Planalto.pdf` |
| FONTE-005 | NT 2025.002 v1.35 | `03_DOCUMENTOS_FISCAIS_E_TABELAS/NT_2025.002_v1.35_RTC_NFe_NFCe.pdf` |
| FONTE-008 | cClassTrib | `03_DOCUMENTOS_FISCAIS_E_TABELAS/cClassTrib 2025-12-12.xlsx` |
| FONTE-009 | cCredPres | `03_DOCUMENTOS_FISCAIS_E_TABELAS/cCredPres_2025-12-12Public.xlsx` |
| FONTE-020 | PRD-base QDI | `docs/refs/01_PRD_BASE.md` |
| FONTE-021 | MoSCoW | `docs/refs/02_MOSCOW_FEATURES.md` |
| FONTE-022 | Metodologia score | `docs/refs/04_METODOLOGIA.md` |
| FONTE-023 | Questionário v1 | `docs/refs/05_QUESTIONARIO_v1.md` |

---

## Próximo passo no pipeline

1. Extrair texto → `dominio_fiscal/extraido/` (a criar na Fase D).  
2. Chunk + embedding (`mxbai-embed-large` ou candidato do benchmark).  
3. Retriever com gate: **citar fonte ou «base insuficiente»** (DP-006).

---

## Decisões Allan (IA_DIAG_V2)

| ID | Escolha |
|----|---------|
| DP-002 | Legislação + documentos QDI |
| DP-003 | `dominio_fiscal/` + `docs/refs` |
| DP-006 | Gate de citação aprovado |

Ver [`_DEVELOPER/IA_DIAG_V2/DECISOES_PENDENTES_ALLAN.md`](../_DEVELOPER/IA_DIAG_V2/DECISOES_PENDENTES_ALLAN.md).
