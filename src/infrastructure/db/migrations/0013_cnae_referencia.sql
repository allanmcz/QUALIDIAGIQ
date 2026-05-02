-- =====================================================================
-- MIGRATION 0013 — CNAE 2.3 (referência) no schema qdi
-- Origem: _DEVELOPER/CNAE/sql/001_create_cnae_tables.sql (sincronizado Ciclo Q)
-- =====================================================================
-- Produto:    QualiDiagIQ (QDI)
-- Base legal: Resolução CONCLA nº 02/2023 (CNAE 2.3, vigente 01/01/2024)
--             LC 214/2025 + EC 132/2023 (Reforma Tributária do Consumo)
-- Fonte:      https://concla.ibge.gov.br/classificacoes/por-tema/atividades-economicas
-- Total:      21 seções, 87 divisões, 285 grupos, 673 classes, 1.332 subclasses
-- Padrões:    Tributiq — multi-tenant + RLS + WORM + versionamento normativo
-- Autor:      Allan Marcio + Claude (Arquiteto QDI)
-- Data:       2026-05-01
-- =====================================================================

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ BLOCO 1: EXTENSÕES + SCHEMA                                         │
-- └────────────────────────────────────────────────────────────────────┘

-- Alinhado a 0001_extensions.sql: sem uuid-ossp no bootstrap frágil; IDs com gen_random_uuid().
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE SCHEMA IF NOT EXISTS qdi;
COMMENT ON SCHEMA qdi IS 'Schema do produto QualiDiagIQ (QDI) — Diagnóstico Tributário';

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ BLOCO 2: ENUMS                                                      │
-- └────────────────────────────────────────────────────────────────────┘

DO $$ BEGIN
    CREATE TYPE qdi.cnae_status_importacao AS ENUM (
        'INICIADA',
        'PROCESSANDO',
        'CONCLUIDA',
        'CONCLUIDA_COM_ERROS',
        'FALHOU',
        'CANCELADA'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ BLOCO 3: FUNÇÕES UTILITÁRIAS (hash + updated_at + WORM)            │
-- └────────────────────────────────────────────────────────────────────┘

-- Atualiza updated_at em UPDATE
CREATE OR REPLACE FUNCTION qdi.fn_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Calcula hash SHA-256 do conteúdo material (descricao + observacoes)
CREATE OR REPLACE FUNCTION qdi.fn_set_hash_conteudo()
RETURNS TRIGGER AS $$
BEGIN
    NEW.hash_conteudo := encode(
        digest(
            COALESCE(NEW.descricao, '') || '|' || COALESCE(NEW.observacoes, ''),
            'sha256'
        ),
        'hex'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Bloqueio WORM: após 30 dias, somente service_role pode alterar
CREATE OR REPLACE FUNCTION qdi.fn_worm_30_dias()
RETURNS TRIGGER AS $$
BEGIN
    IF (NOW() - OLD.created_at) > INTERVAL '30 days'
       AND current_setting('request.jwt.claims', TRUE)::jsonb ->> 'role' <> 'service_role'
    THEN
        RAISE EXCEPTION 'WORM: registro CNAE imutável após 30 dias (created_at=%)',
            OLD.created_at;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ BLOCO 4: TABELA cnae_secao (21 registros: A-U)                     │
-- └────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS qdi.cnae_secao (
    secao_id          CHAR(1)     PRIMARY KEY,
    descricao         TEXT        NOT NULL,
    observacoes       TEXT,
    vigencia_inicio   DATE        NOT NULL DEFAULT '2024-01-01',
    vigencia_fim      DATE,
    hash_conteudo     TEXT        NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ,
    CONSTRAINT chk_cnae_secao_id CHECK (secao_id ~ '^[A-U]$'),
    CONSTRAINT chk_cnae_secao_vigencia CHECK (
        vigencia_fim IS NULL OR vigencia_fim >= vigencia_inicio
    )
);

COMMENT ON TABLE qdi.cnae_secao IS
'Seções CNAE 2.3 — primeiro nível hierárquico (A-U). Base: Resolução CONCLA 02/2023.';

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ BLOCO 5: TABELA cnae_divisao (87 registros: 01-99)                 │
-- └────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS qdi.cnae_divisao (
    divisao_id        CHAR(2)     PRIMARY KEY,
    secao_id          CHAR(1)     NOT NULL REFERENCES qdi.cnae_secao(secao_id) ON UPDATE CASCADE,
    descricao         TEXT        NOT NULL,
    observacoes       TEXT,
    vigencia_inicio   DATE        NOT NULL DEFAULT '2024-01-01',
    vigencia_fim      DATE,
    hash_conteudo     TEXT        NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ,
    CONSTRAINT chk_cnae_divisao_id CHECK (divisao_id ~ '^[0-9]{2}$')
);

COMMENT ON TABLE qdi.cnae_divisao IS
'Divisões CNAE 2.3 — segundo nível hierárquico (01-99). 87 registros.';

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ BLOCO 6: TABELA cnae_grupo (285 registros: 011-999)                │
-- └────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS qdi.cnae_grupo (
    grupo_id          CHAR(3)     PRIMARY KEY,
    divisao_id        CHAR(2)     NOT NULL REFERENCES qdi.cnae_divisao(divisao_id) ON UPDATE CASCADE,
    descricao         TEXT        NOT NULL,
    observacoes       TEXT,
    vigencia_inicio   DATE        NOT NULL DEFAULT '2024-01-01',
    vigencia_fim      DATE,
    hash_conteudo     TEXT        NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at        TIMESTAMPTZ,
    CONSTRAINT chk_cnae_grupo_id CHECK (grupo_id ~ '^[0-9]{3}$')
);

COMMENT ON TABLE qdi.cnae_grupo IS
'Grupos CNAE 2.3 — terceiro nível hierárquico (3 dígitos). 285 registros.';

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ BLOCO 7: TABELA cnae_classe (673 registros: 5 dígitos)             │
-- └────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS qdi.cnae_classe (
    classe_id              CHAR(5)     PRIMARY KEY,
    classe_id_formatado    CHAR(6)     GENERATED ALWAYS AS (
        substr(classe_id, 1, 4) || '-' || substr(classe_id, 5, 1)
    ) STORED,
    grupo_id               CHAR(3)     NOT NULL REFERENCES qdi.cnae_grupo(grupo_id) ON UPDATE CASCADE,
    descricao              TEXT        NOT NULL,
    observacoes            TEXT,
    vigencia_inicio        DATE        NOT NULL DEFAULT '2024-01-01',
    vigencia_fim           DATE,
    hash_conteudo          TEXT        NOT NULL,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at             TIMESTAMPTZ,
    CONSTRAINT chk_cnae_classe_id CHECK (classe_id ~ '^[0-9]{5}$')
);

COMMENT ON TABLE qdi.cnae_classe IS
'Classes CNAE 2.3 — quarto nível (5 dígitos, ex: 0111-3). 673 registros.';

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ BLOCO 8: TABELA cnae_subclasse (1.332 registros: 7 dígitos)        │
-- │           Inclui campos para Reforma Tributária (LC 214/2025)      │
-- └────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS qdi.cnae_subclasse (
    subclasse_id              CHAR(7)     PRIMARY KEY,
    subclasse_id_formatado    CHAR(9)     GENERATED ALWAYS AS (
        substr(subclasse_id, 1, 4) || '-' ||
        substr(subclasse_id, 5, 1) || '/' ||
        substr(subclasse_id, 6, 2)
    ) STORED,
    classe_id                 CHAR(5)     NOT NULL REFERENCES qdi.cnae_classe(classe_id) ON UPDATE CASCADE,
    descricao                 TEXT        NOT NULL,
    atividades                TEXT[]      DEFAULT ARRAY[]::TEXT[],
    observacoes               TEXT,
    vigencia_inicio           DATE        NOT NULL DEFAULT '2024-01-01',
    vigencia_fim              DATE,
    hash_conteudo             TEXT        NOT NULL,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at                TIMESTAMPTZ,

    -- Campos específicos Reforma Tributária (LC 214/2025) — preenchidos por job futuro
    cbs_aliquota_padrao       NUMERIC(7,4),                       -- alíquota CBS prevista
    ibs_aliquota_padrao       NUMERIC(7,4),                       -- alíquota IBS prevista
    regime_aplicavel          TEXT[]      DEFAULT ARRAY[]::TEXT[],-- ['monofasico', 'reduzida_60', 'isencao']
    simples_nacional_anexo    CHAR(1),                            -- 'I'..'V' ou NULL
    simples_impedido          BOOLEAN     DEFAULT FALSE,
    tags_diagnostico          JSONB       DEFAULT '[]'::jsonb,    -- tags p/ engine de score
    cclasstrib_sugerido       TEXT,                               -- código cClassTrib NT 2025.002
    ncm_predominante          TEXT[]      DEFAULT ARRAY[]::TEXT[],-- NCMs típicos p/ esta subclasse

    CONSTRAINT chk_cnae_subclasse_id CHECK (subclasse_id ~ '^[0-9]{7}$'),
    CONSTRAINT chk_cnae_subclasse_simples CHECK (
        simples_nacional_anexo IS NULL OR simples_nacional_anexo IN ('I','II','III','IV','V')
    )
);

COMMENT ON TABLE qdi.cnae_subclasse IS
'Subclasses CNAE 2.3 — quinto nível (7 dígitos, ex: 0111-3/01). 1.332 registros.
 Inclui campos auxiliares para diagnóstico tributário Reforma do Consumo (LC 214/2025).';

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ BLOCO 9: TABELA cnae_importacao_log (auditoria multi-tenant)       │
-- └────────────────────────────────────────────────────────────────────┘

CREATE TABLE IF NOT EXISTS qdi.cnae_importacao_log (
    id                    UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id             UUID,                                    -- NULL = importação global (admin)
    arquivo_nome          TEXT        NOT NULL,
    arquivo_tamanho_bytes BIGINT,
    hash_arquivo          TEXT        NOT NULL,                    -- SHA-256 do arquivo bruto
    versao_cnae           TEXT        NOT NULL DEFAULT '2.3',
    fonte                 TEXT        NOT NULL DEFAULT 'CONCLA/IBGE',
    total_registros       INTEGER     NOT NULL DEFAULT 0,
    registros_inseridos   INTEGER     NOT NULL DEFAULT 0,
    registros_atualizados INTEGER     NOT NULL DEFAULT 0,
    registros_rejeitados  INTEGER     NOT NULL DEFAULT 0,
    iniciado_em           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    concluido_em          TIMESTAMPTZ,
    duracao_ms            INTEGER,
    status                qdi.cnae_status_importacao NOT NULL DEFAULT 'INICIADA',
    executado_por         UUID,                                    -- referência a auth.users.id
    erros                 JSONB       DEFAULT '[]'::jsonb,
    detalhes              JSONB       DEFAULT '{}'::jsonb,
    idempotency_key       TEXT        UNIQUE                       -- previne dupla importação
);

COMMENT ON TABLE qdi.cnae_importacao_log IS
'Log de auditoria de importações CNAE — multi-tenant + idempotência.';

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ BLOCO 10: ÍNDICES (BTREE + BRIN + GIN)                              │
-- └────────────────────────────────────────────────────────────────────┘

-- BTREE em FKs (otimiza JOINs)
CREATE INDEX IF NOT EXISTS idx_cnae_divisao_secao    ON qdi.cnae_divisao(secao_id);
CREATE INDEX IF NOT EXISTS idx_cnae_grupo_divisao    ON qdi.cnae_grupo(divisao_id);
CREATE INDEX IF NOT EXISTS idx_cnae_classe_grupo     ON qdi.cnae_classe(grupo_id);
CREATE INDEX IF NOT EXISTS idx_cnae_subclasse_classe ON qdi.cnae_subclasse(classe_id);

-- BRIN em vigencia_inicio (alta cardinalidade ordenada — espaço mínimo)
CREATE INDEX IF NOT EXISTS idx_cnae_secao_vigencia     ON qdi.cnae_secao     USING BRIN (vigencia_inicio);
CREATE INDEX IF NOT EXISTS idx_cnae_divisao_vigencia   ON qdi.cnae_divisao   USING BRIN (vigencia_inicio);
CREATE INDEX IF NOT EXISTS idx_cnae_grupo_vigencia     ON qdi.cnae_grupo     USING BRIN (vigencia_inicio);
CREATE INDEX IF NOT EXISTS idx_cnae_classe_vigencia    ON qdi.cnae_classe    USING BRIN (vigencia_inicio);
CREATE INDEX IF NOT EXISTS idx_cnae_subclasse_vigencia ON qdi.cnae_subclasse USING BRIN (vigencia_inicio);

-- GIN com pg_trgm (busca fuzzy em descrições)
CREATE INDEX IF NOT EXISTS idx_cnae_secao_descricao_trgm     ON qdi.cnae_secao     USING GIN (descricao gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_cnae_divisao_descricao_trgm   ON qdi.cnae_divisao   USING GIN (descricao gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_cnae_grupo_descricao_trgm     ON qdi.cnae_grupo     USING GIN (descricao gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_cnae_classe_descricao_trgm    ON qdi.cnae_classe    USING GIN (descricao gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_cnae_subclasse_descricao_trgm ON qdi.cnae_subclasse USING GIN (descricao gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_cnae_subclasse_atividades_gin ON qdi.cnae_subclasse USING GIN (atividades);
CREATE INDEX IF NOT EXISTS idx_cnae_subclasse_tags_gin       ON qdi.cnae_subclasse USING GIN (tags_diagnostico);

-- Índices do log
CREATE INDEX IF NOT EXISTS idx_cnae_log_tenant       ON qdi.cnae_importacao_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cnae_log_status       ON qdi.cnae_importacao_log(status);
CREATE INDEX IF NOT EXISTS idx_cnae_log_iniciado_em  ON qdi.cnae_importacao_log USING BRIN (iniciado_em);

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ BLOCO 11: TRIGGERS                                                  │
-- └────────────────────────────────────────────────────────────────────┘

-- updated_at + hash_conteudo nas 5 tabelas hierárquicas
DO $$
DECLARE tabela TEXT;
BEGIN
    FOREACH tabela IN ARRAY ARRAY['cnae_secao','cnae_divisao','cnae_grupo','cnae_classe','cnae_subclasse']
    LOOP
        EXECUTE format(
            'DROP TRIGGER IF EXISTS trg_%1$s_set_updated_at ON qdi.%1$s;
             CREATE TRIGGER trg_%1$s_set_updated_at
             BEFORE UPDATE ON qdi.%1$s
             FOR EACH ROW EXECUTE FUNCTION qdi.fn_set_updated_at();',
            tabela
        );
        EXECUTE format(
            'DROP TRIGGER IF EXISTS trg_%1$s_set_hash ON qdi.%1$s;
             CREATE TRIGGER trg_%1$s_set_hash
             BEFORE INSERT OR UPDATE OF descricao, observacoes ON qdi.%1$s
             FOR EACH ROW EXECUTE FUNCTION qdi.fn_set_hash_conteudo();',
            tabela
        );
        EXECUTE format(
            'DROP TRIGGER IF EXISTS trg_%1$s_worm ON qdi.%1$s;
             CREATE TRIGGER trg_%1$s_worm
             BEFORE UPDATE OR DELETE ON qdi.%1$s
             FOR EACH ROW EXECUTE FUNCTION qdi.fn_worm_30_dias();',
            tabela
        );
    END LOOP;
END $$;

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ BLOCO 12: ROW-LEVEL SECURITY (RLS)                                  │
-- └────────────────────────────────────────────────────────────────────┘

-- Habilitar RLS nas 5 tabelas + log
ALTER TABLE qdi.cnae_secao            ENABLE ROW LEVEL SECURITY;
ALTER TABLE qdi.cnae_divisao          ENABLE ROW LEVEL SECURITY;
ALTER TABLE qdi.cnae_grupo            ENABLE ROW LEVEL SECURITY;
ALTER TABLE qdi.cnae_classe           ENABLE ROW LEVEL SECURITY;
ALTER TABLE qdi.cnae_subclasse        ENABLE ROW LEVEL SECURITY;
ALTER TABLE qdi.cnae_importacao_log   ENABLE ROW LEVEL SECURITY;

-- Política SELECT: qualquer authenticated (lookup global de referência)
DO $$
DECLARE tabela TEXT;
BEGIN
    FOREACH tabela IN ARRAY ARRAY['cnae_secao','cnae_divisao','cnae_grupo','cnae_classe','cnae_subclasse']
    LOOP
        EXECUTE format(
            'DROP POLICY IF EXISTS pol_%1$s_select ON qdi.%1$s;
             CREATE POLICY pol_%1$s_select ON qdi.%1$s
                FOR SELECT TO authenticated USING (deleted_at IS NULL);',
            tabela
        );
        EXECUTE format(
            'DROP POLICY IF EXISTS pol_%1$s_admin ON qdi.%1$s;
             CREATE POLICY pol_%1$s_admin ON qdi.%1$s
                FOR ALL TO service_role
                USING (true) WITH CHECK (true);',
            tabela
        );
    END LOOP;
END $$;

-- Política do log: tenant vê apenas seus logs (ou logs globais com tenant_id NULL)
DROP POLICY IF EXISTS pol_cnae_log_select ON qdi.cnae_importacao_log;
CREATE POLICY pol_cnae_log_select ON qdi.cnae_importacao_log
    FOR SELECT TO authenticated
    USING (
        tenant_id IS NULL
        OR tenant_id = (current_setting('request.jwt.claims', TRUE)::jsonb ->> 'tenant_id')::uuid
    );

DROP POLICY IF EXISTS pol_cnae_log_admin ON qdi.cnae_importacao_log;
CREATE POLICY pol_cnae_log_admin ON qdi.cnae_importacao_log
    FOR ALL TO service_role
    USING (true) WITH CHECK (true);

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ BLOCO 13: VIEW DE CONVENIÊNCIA (consulta hierárquica completa)     │
-- └────────────────────────────────────────────────────────────────────┘

CREATE OR REPLACE VIEW qdi.v_cnae_completo AS
SELECT
    sec.secao_id,
    sec.descricao             AS secao_descricao,
    div.divisao_id,
    div.descricao             AS divisao_descricao,
    gru.grupo_id,
    gru.descricao             AS grupo_descricao,
    cla.classe_id,
    cla.classe_id_formatado,
    cla.descricao             AS classe_descricao,
    sub.subclasse_id,
    sub.subclasse_id_formatado,
    sub.descricao             AS subclasse_descricao,
    sub.atividades,
    sub.observacoes           AS subclasse_observacoes,
    sub.cbs_aliquota_padrao,
    sub.ibs_aliquota_padrao,
    sub.regime_aplicavel,
    sub.simples_nacional_anexo,
    sub.simples_impedido,
    sub.tags_diagnostico,
    sub.cclasstrib_sugerido,
    sub.ncm_predominante,
    sub.vigencia_inicio,
    sub.vigencia_fim
FROM qdi.cnae_subclasse sub
JOIN qdi.cnae_classe   cla ON cla.classe_id  = sub.classe_id  AND cla.deleted_at IS NULL
JOIN qdi.cnae_grupo    gru ON gru.grupo_id   = cla.grupo_id   AND gru.deleted_at IS NULL
JOIN qdi.cnae_divisao  div ON div.divisao_id = gru.divisao_id AND div.deleted_at IS NULL
JOIN qdi.cnae_secao    sec ON sec.secao_id   = div.secao_id   AND sec.deleted_at IS NULL
WHERE sub.deleted_at IS NULL
  AND (sub.vigencia_fim IS NULL OR sub.vigencia_fim >= CURRENT_DATE);

COMMENT ON VIEW qdi.v_cnae_completo IS
'View denormalizada — 1 linha por subclasse vigente, com toda a hierarquia.';

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ BLOCO 14: FUNÇÃO RPC PARA IMPORTAÇÃO IDEMPOTENTE                    │
-- └────────────────────────────────────────────────────────────────────┘

CREATE OR REPLACE FUNCTION qdi.fn_importar_cnae_subclasses(
    p_payload          JSONB,           -- array de subclasses
    p_idempotency_key  TEXT,
    p_arquivo_nome     TEXT,
    p_hash_arquivo     TEXT,
    p_executado_por    UUID DEFAULT NULL,
    p_tenant_id        UUID DEFAULT NULL
) RETURNS UUID
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_log_id      UUID;
    v_total       INTEGER := 0;
    v_inseridos   INTEGER := 0;
    v_atualizados INTEGER := 0;
    v_rejeitados  INTEGER := 0;
    v_inicio      TIMESTAMPTZ := NOW();
    v_existente   UUID;
BEGIN
    -- Idempotência: se a chave já foi usada, retorna o log antigo
    SELECT id INTO v_existente FROM qdi.cnae_importacao_log
        WHERE idempotency_key = p_idempotency_key;
    IF v_existente IS NOT NULL THEN
        RETURN v_existente;
    END IF;

    -- Cria log INICIADA
    INSERT INTO qdi.cnae_importacao_log (
        tenant_id, arquivo_nome, hash_arquivo, total_registros,
        executado_por, status, idempotency_key, iniciado_em
    ) VALUES (
        p_tenant_id, p_arquivo_nome, p_hash_arquivo, jsonb_array_length(p_payload),
        p_executado_por, 'PROCESSANDO', p_idempotency_key, v_inicio
    ) RETURNING id INTO v_log_id;

    v_total := jsonb_array_length(p_payload);

    -- UPSERT em massa
    WITH dados AS (
        SELECT
            (item->>'subclasse_id')::CHAR(7)  AS subclasse_id,
            (item->>'classe_id')::CHAR(5)     AS classe_id,
            item->>'descricao'                AS descricao,
            COALESCE(
                ARRAY(SELECT jsonb_array_elements_text(item->'atividades')),
                ARRAY[]::TEXT[]
            )                                  AS atividades,
            item->>'observacoes'              AS observacoes
        FROM jsonb_array_elements(p_payload) AS item
    ),
    upsert AS (
        INSERT INTO qdi.cnae_subclasse (
            subclasse_id, classe_id, descricao, atividades, observacoes, hash_conteudo
        )
        SELECT
            d.subclasse_id, d.classe_id, d.descricao, d.atividades, d.observacoes,
            encode(digest(COALESCE(d.descricao,'') || '|' || COALESCE(d.observacoes,''), 'sha256'), 'hex')
        FROM dados d
        ON CONFLICT (subclasse_id) DO UPDATE
            SET descricao   = EXCLUDED.descricao,
                atividades  = EXCLUDED.atividades,
                observacoes = EXCLUDED.observacoes,
                updated_at  = NOW()
            WHERE qdi.cnae_subclasse.hash_conteudo <> EXCLUDED.hash_conteudo
        RETURNING (xmax = 0) AS foi_inserido
    )
    SELECT
        COUNT(*) FILTER (WHERE foi_inserido),
        COUNT(*) FILTER (WHERE NOT foi_inserido)
    INTO v_inseridos, v_atualizados
    FROM upsert;

    v_rejeitados := v_total - v_inseridos - v_atualizados;

    -- Atualiza log para CONCLUIDA
    UPDATE qdi.cnae_importacao_log SET
        registros_inseridos   = v_inseridos,
        registros_atualizados = v_atualizados,
        registros_rejeitados  = v_rejeitados,
        concluido_em          = NOW(),
        duracao_ms            = EXTRACT(MILLISECOND FROM (NOW() - v_inicio))::INTEGER
                              + EXTRACT(SECOND FROM (NOW() - v_inicio))::INTEGER * 1000,
        status                = CASE WHEN v_rejeitados = 0 THEN 'CONCLUIDA'::qdi.cnae_status_importacao
                                     ELSE 'CONCLUIDA_COM_ERROS'::qdi.cnae_status_importacao END
    WHERE id = v_log_id;

    RETURN v_log_id;
EXCEPTION WHEN OTHERS THEN
    UPDATE qdi.cnae_importacao_log SET
        status       = 'FALHOU',
        concluido_em = NOW(),
        erros        = jsonb_build_array(jsonb_build_object('message', SQLERRM, 'state', SQLSTATE))
    WHERE id = v_log_id;
    RAISE;
END;
$$;

COMMENT ON FUNCTION qdi.fn_importar_cnae_subclasses IS
'Importação idempotente de subclasses CNAE em massa. Recebe JSONB array.
 Idempotency-Key obrigatória — segunda chamada com mesma key retorna log existente.';

-- ┌────────────────────────────────────────────────────────────────────┐
-- │ BLOCO 15: GRANTS                                                    │
-- └────────────────────────────────────────────────────────────────────┘

GRANT USAGE ON SCHEMA qdi TO authenticated, service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA qdi TO authenticated;
GRANT SELECT ON qdi.v_cnae_completo TO authenticated;
GRANT EXECUTE ON FUNCTION qdi.fn_importar_cnae_subclasses TO service_role;

-- ============================================================================
-- FIM DA MIGRATION 0013 — CNAE 2.3 (DDL + RLS + view + RPC)
-- Próximo passo no repo: migração 0014_cnae_seed_dados.sql
-- ============================================================================
