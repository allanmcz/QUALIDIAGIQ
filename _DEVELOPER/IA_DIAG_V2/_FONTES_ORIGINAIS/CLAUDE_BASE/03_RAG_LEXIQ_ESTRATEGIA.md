# 03 — RAG sobre a Lexiq Tributária (Camada 2)

> **Objetivo:** detalhar a estratégia de ingestão, chunking, embeddings e retrieval da base normativa do QDI para a memória factual do Ollama.

---

## 1. Fonte de Dados

| Documento | Tipo | Volume | Localização atual |
|-----------|------|--------|-------------------|
| LC 214/2025 (integral) | PDF/TXT | ~400 pág | `dominio_fiscal/legislacao/` |
| EC 132/2023 | PDF | ~30 pág | `dominio_fiscal/legislacao/` |
| LC 227/2026 | PDF | ~80 pág | `dominio_fiscal/legislacao/` |
| NT 2025.002 v1.33+ | PDF | ~250 pág | `dominio_fiscal/notas_tecnicas/` |
| Pareceres PT-001 a PT-011 | MD | 11 × 15 pág | `dominio_fiscal/pareceres/` |
| Tabela cClassTrib | CSV | ~200 linhas | `dominio_fiscal/tabelas/` |
| Tabela cCredPres | CSV | ~50 linhas | `dominio_fiscal/tabelas/` |
| Tabela NCM (resumida) | CSV | ~500 grupos | `dominio_fiscal/tabelas/` |
| Tabela CST CBS/IBS | CSV | ~80 linhas | `dominio_fiscal/tabelas/` |

---

## 2. Estratégia de Chunking

A escolha do chunking é o **fator mais determinante da qualidade do RAG**. Cada tipo de documento exige uma estratégia distinta:

### 2.1 Legislação (LC 214/2025, EC 132/2023, LC 227/2026)

**Estratégia:** chunking semântico por unidade normativa (artigo → parágrafo → inciso).

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter_legislacao = RecursiveCharacterTextSplitter(
    chunk_size=800,           # ≈ 200 tokens
    chunk_overlap=120,        # preserva continuidade entre artigos
    separators=[
        "\n\nTÍTULO ",        # nível 0
        "\n\nCAPÍTULO ",      # nível 1
        "\n\nSEÇÃO ",         # nível 2
        "\n\nArt. ",          # nível 3 (principal)
        "\n\n§ ",             # nível 4
        "\n\nI - ", "\n\nII - ",  # incisos
        "\n\n", "\n", ". ",
    ],
)
```

**Metadados obrigatórios:**

```python
{
    "documento": "LC_214_2025",
    "titulo": "Da Contribuição sobre Bens e Serviços",
    "capitulo": "I",
    "secao": "I",
    "artigo": "Art. 23",
    "vigencia_inicio": "2027-01-01",
    "vigencia_fim": None,
    "hierarquia": "lei_complementar",
    "hash_sha256": "abc123...",
    "tenant_id": "shared",  # base global
    "indexed_at": "2026-05-17T18:30:00-03:00",
}
```

---

### 2.2 Nota Técnica 2025.002 (NF-e/NFC-e Reforma)

**Estratégia:** chunking por seção técnica + preservação de tabelas.

```python
splitter_nt = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=[
        "\n\n## ",            # seção principal
        "\n\n### ",           # subseção
        "\n\nGrupo ",         # grupo de tags XML (M, Q, S...)
        "\n\nTag ",           # tag individual
        "\n\n", "\n", ". ",
    ],
)
```

**Cuidado especial:** tabelas de mapeamento (ex: vincula `cClassTrib` ↔ `CST`) devem virar **um chunk por linha** para retrieval preciso.

---

### 2.3 Pareceres Internos (PT-001 a PT-011)

**Estratégia:** chunking por capítulo + preservação de exemplos.

```python
splitter_parecer = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=120,
    separators=[
        "\n\n## ",            # capítulo
        "\n\n### ",           # subseção
        "\n\n**Exemplo",      # exemplos isolados
        "\n\n**Conclusão",
        "\n\n", "\n", ". ",
    ],
)
```

---

### 2.4 Tabelas (cClassTrib, cCredPres, CST, NCM)

**Estratégia:** **1 chunk por código** (granularidade máxima para retrieval cirúrgico).

```python
# Exemplo para cClassTrib
def chunk_cclasstrib(codigo: str, descricao: str, regime: str, vigencia: dict):
    texto = f"""
Código cClassTrib: {codigo}
Descrição: {descricao}
Regime tributário: {regime}
Vigência: {vigencia['inicio']} a {vigencia.get('fim') or 'indeterminado'}
Base normativa: LC 214/2025
""".strip()

    metadata = {
        "tipo": "tabela_cclasstrib",
        "codigo": codigo,
        "regime": regime,
        **vigencia,
    }
    return texto, metadata
```

---

## 3. Pipeline de Ingestão

```python
# _DEVELOPER/IA_DIAG_AVANCADO/SCRIPTS/INGESTAO_LEXIQ.PY
"""
Ingere a base normativa do QDI no pgvector local.

Execução:
    python -m _developer.ia_diag_avancado.scripts.ingestao_lexiq

Idempotente: usa hash SHA-256 do chunk como chave de upsert.
"""
import asyncio
import hashlib
from pathlib import Path
from typing import Iterator

import asyncpg
import structlog
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader, TextLoader
import httpx

logger = structlog.get_logger(__name__)

# -----------------------------------------------------------------------------
# Configuração
# -----------------------------------------------------------------------------
PG_DSN = "postgresql://qdi:devdev@localhost:5433/qdi_rag"
OLLAMA_URL = "http://localhost:11434"
EMBEDDING_MODEL = "nomic-embed-text"
EMBEDDING_DIM = 768


# -----------------------------------------------------------------------------
# DDL — executar 1 vez
# -----------------------------------------------------------------------------
DDL = f"""
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- p/ busca híbrida BM25-like

CREATE SCHEMA IF NOT EXISTS qdi_rag;

CREATE TABLE IF NOT EXISTS qdi_rag.lexiq_chunks (
    id BIGSERIAL PRIMARY KEY,
    hash_sha256 CHAR(64) UNIQUE NOT NULL,
    documento TEXT NOT NULL,
    artigo TEXT,
    capitulo TEXT,
    secao TEXT,
    vigencia_inicio DATE,
    vigencia_fim DATE,
    hierarquia TEXT NOT NULL,
    tenant_id UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000000',
    conteudo TEXT NOT NULL,
    embedding vector({EMBEDDING_DIM}) NOT NULL,
    indexed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índice HNSW para similaridade
CREATE INDEX IF NOT EXISTS idx_lexiq_embedding_hnsw
ON qdi_rag.lexiq_chunks
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Índice trigram para busca lexical (busca híbrida)
CREATE INDEX IF NOT EXISTS idx_lexiq_conteudo_trgm
ON qdi_rag.lexiq_chunks
USING gin (conteudo gin_trgm_ops);

-- Índice de filtros frequentes
CREATE INDEX IF NOT EXISTS idx_lexiq_documento ON qdi_rag.lexiq_chunks(documento);
CREATE INDEX IF NOT EXISTS idx_lexiq_vigencia ON qdi_rag.lexiq_chunks(vigencia_inicio, vigencia_fim);
"""


async def embedir_texto(texto: str) -> list[float]:
    """Gera embedding via Ollama nomic-embed-text."""
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": texto},
        )
        resp.raise_for_status()
        return resp.json()["embedding"]


async def ingerir_chunk(
    conn: asyncpg.Connection,
    conteudo: str,
    metadata: dict,
) -> None:
    """Insere chunk com upsert idempotente via hash SHA-256."""
    hash_chunk = hashlib.sha256(conteudo.encode("utf-8")).hexdigest()
    embedding = await embedir_texto(conteudo)

    await conn.execute(
        """
        INSERT INTO qdi_rag.lexiq_chunks
            (hash_sha256, documento, artigo, capitulo, secao,
             vigencia_inicio, vigencia_fim, hierarquia, conteudo, embedding)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10::vector)
        ON CONFLICT (hash_sha256) DO NOTHING
        """,
        hash_chunk,
        metadata["documento"],
        metadata.get("artigo"),
        metadata.get("capitulo"),
        metadata.get("secao"),
        metadata.get("vigencia_inicio"),
        metadata.get("vigencia_fim"),
        metadata["hierarquia"],
        conteudo,
        str(embedding),
    )
    logger.info("chunk.ingerido", documento=metadata["documento"], hash=hash_chunk[:8])


async def main():
    conn = await asyncpg.connect(PG_DSN)
    try:
        await conn.execute(DDL)
        # ... pipeline completo de ingestão por tipo de documento
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. Estratégia de Retrieval Híbrido

**Princípio:** combinar busca semântica (embeddings) + busca lexical (trigram/BM25) para maximizar recall em consultas tributárias, onde termos técnicos exatos importam.

```python
async def buscar_lexiq(
    pergunta: str,
    *,
    k: int = 8,
    threshold_score: float = 0.65,
    filtro_vigencia: date | None = None,
) -> list[ChunkLexiq]:
    """
    Busca híbrida na Lexiq com fusão de scores.

    Algoritmo:
        1. Embedding da pergunta (Ollama nomic-embed-text)
        2. Top-K semântico via HNSW (cosine similarity)
        3. Top-K lexical via similarity ts_query (pg_trgm)
        4. Reciprocal Rank Fusion (RRF) dos dois rankings
        5. Filtro de vigência (data atual ou data informada)
        6. Threshold de score (princípio QDI #6: < 0.65 → INDEFINIDO)
    """
    embedding_pergunta = await embedir_texto(pergunta)

    sql = """
    WITH busca_semantica AS (
        SELECT id, 1 - (embedding <=> $1::vector) AS score_semantico,
               ROW_NUMBER() OVER (ORDER BY embedding <=> $1::vector) AS rank_sem
        FROM qdi_rag.lexiq_chunks
        WHERE ($2::date IS NULL OR vigencia_inicio <= $2)
          AND ($2::date IS NULL OR vigencia_fim IS NULL OR vigencia_fim >= $2)
        ORDER BY embedding <=> $1::vector
        LIMIT 30
    ),
    busca_lexical AS (
        SELECT id, similarity(conteudo, $3) AS score_lexical,
               ROW_NUMBER() OVER (ORDER BY similarity(conteudo, $3) DESC) AS rank_lex
        FROM qdi_rag.lexiq_chunks
        WHERE conteudo % $3
          AND ($2::date IS NULL OR vigencia_inicio <= $2)
          AND ($2::date IS NULL OR vigencia_fim IS NULL OR vigencia_fim >= $2)
        ORDER BY similarity(conteudo, $3) DESC
        LIMIT 30
    ),
    fusao AS (
        SELECT
            COALESCE(s.id, l.id) AS id,
            COALESCE(1.0 / (60 + s.rank_sem), 0) +
            COALESCE(1.0 / (60 + l.rank_lex), 0) AS score_rrf,
            s.score_semantico
        FROM busca_semantica s
        FULL OUTER JOIN busca_lexical l USING (id)
    )
    SELECT c.*, f.score_rrf, f.score_semantico
    FROM fusao f
    JOIN qdi_rag.lexiq_chunks c ON c.id = f.id
    WHERE f.score_semantico >= $4
    ORDER BY f.score_rrf DESC
    LIMIT $5
    """

    # ... execução
```

---

## 5. Versionamento Normativo (Princípio QDI #2)

**Problema:** LC 214/2025 prevê regimes que mudam ao longo do tempo:
- 2026: período de testes (alíquota zero)
- 2027: cobrança plena de CBS
- 2029-2032: transição ICMS → IBS
- 2033+: regime definitivo

**Solução:** todo chunk carrega `vigencia_inicio` e `vigencia_fim`. O retrieval **filtra obrigatoriamente** pela data do diagnóstico.

```python
# Diagnóstico em 2026-05-17 → só retorna chunks vigentes em 2026-05-17
# Diagnóstico em 2027-06-01 → retorna chunks vigentes em 2027-06-01 (regimes diferentes)
```

---

## 6. Métricas de Qualidade do RAG

A pasta `09_BENCHMARK_AVALIACAO.md` detalha a suite. Resumo:

| Métrica | Alvo |
|---------|------|
| Recall@8 (golden questions) | ≥ 85% |
| MRR (Mean Reciprocal Rank) | ≥ 0.70 |
| Taxa de citação válida | 100% |
| Taxa de alucinação NCM/cClassTrib | 0% |
| Latência p50 retrieval | < 200 ms |
| Latência p95 retrieval | < 500 ms |

---

## 7. Cronograma de Ingestão

| Etapa | Esforço | Sprint |
|-------|---------|--------|
| Setup pgvector + DDL | 1h | 1 |
| Ingestão LC 214/2025 | 4h | 2 |
| Ingestão EC 132 + LC 227 | 2h | 2 |
| Ingestão NT 2025.002 | 4h | 2 |
| Ingestão pareceres PT-001 a PT-011 | 3h | 2 |
| Ingestão tabelas (cClassTrib, NCM...) | 3h | 3 |
| Golden questions + benchmark | 6h | 3 |
| Tuning de chunking + threshold | 4h | 3 |
| **Total** | **27h** | Sprints 1-3 |
