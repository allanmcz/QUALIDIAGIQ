# HANDOFF COMPLETO — IA_DIAG_V2 (Onda 1.0)

> **Para:** Allan Marcio  
> **Executor:** Agente Cursor (sessao autonoma — descanso)  
> **Data:** 2026-05-17 / 2026-05-18 UTC  
> **Escopo executado:** Fases **A, B, C, D** + decisoes + catalogo fontes  
> **Nao executado:** Fases **E–H** (Onda IA 1.1 — integracao `src/` / frontend)

---

## Resumo executivo (30 segundos)

| Fase | Status | Documento |
|------|--------|-------------|
| **A** Ollama | Go com ressalva | [`FASE_A_RELATORIO.md`](FASE_A_RELATORIO.md) |
| **B** Benchmark | Concluido — **revisar alucinacoes** | [`FASE_B_BENCHMARK_MODELOS.md`](FASE_B_BENCHMARK_MODELOS.md) |
| **C** Ensino | Pre-preenchido — **validar 10 casos** | [`FASE_C_ENSINO_SUPERVISIONADO.md`](FASE_C_ENSINO_SUPERVISIONADO.md) |
| **D** RAG piloto | Go (Markdown) | [`FASE_D_RAG_PILOTO.md`](FASE_D_RAG_PILOTO.md) |
| **E–H** | Nao iniciado | Ver secao 8 |

**Decisoes:** [`DECISOES_PENDENTES_ALLAN.md`](../DECISOES_PENDENTES_ALLAN.md) — DP-001..006 fechadas.

**Fontes:** [`dominio_fiscal/catalogo_fontes.yml`](../../dominio_fiscal/catalogo_fontes.yml) + [`INDEX.md`](../../dominio_fiscal/INDEX.md).

---

## 1. O que foi criado/alterado

### Documentacao e relatorios (`_DEVELOPER/IA_DIAG_V2/reports/`)

- `FASE_A_RELATORIO.md`
- `FASE_B_BENCHMARK_MODELOS.md` + `fase_b_raw.json`
- `FASE_C_ENSINO_SUPERVISIONADO.md`
- `FASE_D_RAG_PILOTO.md` + `fase_d_rag_piloto.json`
- `HANDOFF_COMPLETO_IA_DIAG_V2.md` (este arquivo)

### Scripts (`scripts/` — sem alterar `src/`)

| Script | Funcao |
|--------|--------|
| `ia_diag_v2_fase_b_benchmark.py` | Benchmark 3 modelos x 5 perguntas |
| `ia_diag_v2_gerar_relatorio_fase_b.py` | Gera MD a partir do JSON |
| `ia_diag_v2_fase_d_rag_piloto.py` | RAG piloto embeddings + docs/refs |
| `remover_empresa_dev.py` | (sessao anterior) limpeza dev |
| `backfill_materializacao_empresa.py` | (sessao anterior) backfill CNPJ |

### Dominio fiscal

- `dominio_fiscal/catalogo_fontes.yml` (20 entradas, 15 piloto)
- `dominio_fiscal/INDEX.md`

### Nao alterado (conforme DP-004)

- `src/`, `frontend/`, migrations, `make test`

---

## 2. Fase A — pontos criticos

1. **Dois Ollama na porta 11434** (Docker `qdi-ollama` + processo nativo) — unificar antes de produto.
2. **Client 0.20.4 / Server 0.21.0** — alinhar com `brew upgrade ollama`.
3. API HTTP `/api/generate` funciona; CLI `ollama run` travou >5 min no handoff.

**Acao Allan (5 min):**

```bash
# Escolha UMA instancia:
brew services stop ollama          # OU
docker compose stop ollama
```

---

## 3. Fase B — pontos criticos

Benchmark rodou: `llama3.2:latest`, `qdi-assistant:latest` (404 no Docker), `qwen2.5-coder:14b`.

**Nenhum modelo acertou o dominio QualiDiagIQ sem RAG** (alucinaram OMS, Alibaba, saude).

**Conclusao:** Modelfile + RAG sao obrigatorios antes da Fase E. Ver decisao corrigida no final de `FASE_B_BENCHMARK_MODELOS.md`.

**Reproducao:**

```bash
PYTHONPATH=. python scripts/ia_diag_v2_fase_b_benchmark.py
PYTHONPATH=. python scripts/ia_diag_v2_gerar_relatorio_fase_b.py
```

---

## 4. Fase C — sua fila ao acordar

Abrir `FASE_C_ENSINO_SUPERVISIONADO.md` e marcar [ ] aprovar / corrigir cada SUP-001..010.

Regras aprovadas devem ir para `.ollama/context/` (criar se nao existir) ou atualizar Modelfile `qdi-assistant`.

---

## 5. Fase D — pontos positivos

- **mxbai-embed-large** operacional via `/api/embed`.
- 4/4 perguntas-teste sobre produto retornaram **com_fonte** em `docs/refs/`.
- Threshold 0.45 adequado para Markdown; ajustar apos incluir PDFs.

**Pendente:** extrair `01_LEGISLACAO_BASE/*.pdf` e `03_DOCUMENTOS_FISCAIS_E_TABELAS/NT_*.pdf` para chunks classe A.

---

## 6. Go / No-Go integracao (Fase E)

| Criterio | OK? |
|----------|-----|
| Ollama unico e estavel | Nao — duplicidade 11434 |
| Modelo com persona QDI | Nao — qdi-assistant 404 no compose |
| Benchmark dominio aceitavel | Nao — alucinacao sem RAG |
| RAG piloto docs QDI | Sim |
| RAG piloto legislacao PDF | Nao — extracao pendente |
| DP-004 scripts primeiro | Sim — cumprido |

**Veredito Fase E:** **No-Go** ate Allan unificar Ollama + disponibilizar `qdi-assistant` no compose + extrair PDFs piloto.

---

## 7. Onda IA 1.1 (E–H) — roteiro futuro

| Fase | Entrega | Pre-requisito |
|------|---------|---------------|
| **E** | Evoluir `gateway_router` + citacoes na UI ExplicacaoScoreLlm | Go acima |
| **F** | Lexiq / pgvector ampliado | PDFs extraidos |
| **G** | Indice `src/` + ADRs | Fase F estavel |
| **H** | LangGraph Checkpointer wizard | Auditoria wizard |

---

## 8. Checklist primeira hora apos descanso

1. [ ] Unificar Ollama (secao 2)
2. [ ] Validar SUP-001..010 (Fase C)
3. [ ] Ler decisao corrigida Fase B
4. [ ] Opcional: `ollama create qdi-assistant` no container Docker
5. [ ] Retomar teste OLIVEIRA & SILVA no painel (empresa removida na sessao anterior)
6. [ ] Nao fazer commit ate revisar diff (`git status`)

---

## 9. Mensagem sugerida de commit (quando revisar)

```text
docs(qdi-docs): handoff IA_DIAG_V2 fases A-D, catalogo dominio_fiscal e scripts piloto

Refs: _DEVELOPER/IA_DIAG_V2/reports/HANDOFF_COMPLETO_IA_DIAG_V2.md
```

---

*Bom descanso, Allan. O ambiente esta documentado; a integracao em produto espera Ollama unificado + persona + PDFs no RAG.*
