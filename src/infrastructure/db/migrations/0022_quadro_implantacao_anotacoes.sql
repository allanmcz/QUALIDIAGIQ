-- Quadro de implantação — anotações do consultor (comentário + meta de prazo) por ação sugerida.
-- Chaves canónicas no JSON: f{índice_frente}_a{índice_ação} (ordem do checklist derivado do motor M07/M08).
-- Compatível com WORM granular (0012): coluna fora da lista de campos de evidência bloqueados.
-- Base: LC 214/2025 (governança de projeto); ABNT NBR 17301:2026 (planejamento e evidências).

ALTER TABLE diagnosticos ADD COLUMN IF NOT EXISTS quadro_implantacao_anotacoes JSONB NULL;

COMMENT ON COLUMN diagnosticos.quadro_implantacao_anotacoes IS
    'QDI — mapa JSON chave f{i}_a{j} -> {comentario, prazo_meta} (YYYY-MM-DD ou vazio); PATCH com If-Match (versao_otimista).';
