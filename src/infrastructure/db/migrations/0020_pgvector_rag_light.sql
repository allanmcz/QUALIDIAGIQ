-- Sprint 11/12 — RAG-light: embeddings normativos (OpenAI text-embedding-3-small = 1536 dims).
-- Requer imagem Postgres com extensão vector (ex.: pgvector/pgvector:pg16).

CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS qdi_rag;

CREATE TABLE IF NOT EXISTS qdi_rag.documento_normativo (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fonte TEXT NOT NULL,
    artigo TEXT,
    paragrafo TEXT,
    texto TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    vigencia_inicio DATE NOT NULL,
    vigencia_fim DATE,
    criado_em TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_doc_norm_emb ON qdi_rag.documento_normativo
    USING hnsw (embedding vector_cosine_ops);

ALTER TABLE qdi_rag.documento_normativo ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS doc_norm_public_read ON qdi_rag.documento_normativo;
CREATE POLICY doc_norm_public_read ON qdi_rag.documento_normativo
    FOR SELECT TO authenticated USING (true);

GRANT USAGE ON SCHEMA qdi_rag TO postgres;
GRANT SELECT ON qdi_rag.documento_normativo TO postgres;
GRANT USAGE ON SCHEMA qdi_rag TO authenticated;
GRANT SELECT ON qdi_rag.documento_normativo TO authenticated;

COMMENT ON TABLE qdi_rag.documento_normativo IS
    'Chunks normativos para RAG-light — ingestão via scripts/ingestao_rag_baseline.py (fonte default scripts/normativos_baseline/*.txt)';
