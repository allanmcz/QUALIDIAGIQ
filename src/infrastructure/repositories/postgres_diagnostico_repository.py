"""
Persistência de diagnósticos em PostgreSQL (SQL direto, sem PostgREST).

Camada: Infrastructure
Implementa: ``DiagnosticoRepository``

Usado quando ``DATABASE_URL`` / ``sync_database_url`` está definido — alinha com login em
``admins`` e com ``PostgresLeadDiagnosticoVinculoAdapter`` (importar leads OTP).

Analogia: mesmo ``DiagnosticoRepository`` que o adapter Supabase honra, mas a «ferida»
é ``psycopg2`` síncrono em thread pool (como outras peças já sync no projeto).
"""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime
from typing import Any, cast
from uuid import UUID

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from src.application.constants.refazer_questionario import MOTIVO_REFAZER_QUESTIONARIO_PAINEL
from src.application.services.plano_painel_derivacao import derivar_plano_painel_materializado
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    FaixaFaturamentoDeclarada,
    PainelEstadoCicloDiagnostico,
    PlanoDiagnostico,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
    StatusDiagnostico,
)
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.domain.value_objects.checklist_m12_likert import normalizar_checklist_m12_estado_bruto
from src.domain.value_objects.linha_resposta_questionario import LinhaRespostaQuestionario
from src.domain.value_objects.plano_painel_serializado import PlanoPainelSerializado
from src.domain.value_objects.resultado_eliminacao_empresa import ResultadoEliminacaoEmpresa
from src.domain.value_objects.score import ScoreCompleto
from src.infrastructure.repositories.postgres_diagnostico_resposta_sync import (
    inserir_respostas_questionario_em_cursor,
    inserir_respostas_questionario_refazer_sync,
    listar_respostas_questionario_sync,
    proximo_refazer_lote_respostas_sync,
)
from src.infrastructure.repositories.postgres_plano_painel_sync import (
    atualizar_subtarefa_sync,
    buscar_plano_painel_serializado_sync,
    inserir_subtarefa_sync,
    materializar_plano_em_conexao,
    plano_materializado_existe_sync,
)


def _quadro_anotacoes_de_row(row: dict[str, Any]) -> dict[str, dict[str, str | list[str]]] | None:
    """Lê JSONB ``quadro_implantacao_anotacoes`` (mapa f{i}_a{j} -> prazo_meta, comentarios[]; legado comentario)."""
    raw = row.get("quadro_implantacao_anotacoes")
    if raw is None or not isinstance(raw, dict):
        return None
    out: dict[str, dict[str, str | list[str]]] = {}
    for k, v in raw.items():
        if not isinstance(v, dict):
            continue
        prazo = str(v.get("prazo_meta", "") or "").strip()
        comentarios: list[str] = []
        cr = v.get("comentarios")
        if isinstance(cr, list):
            comentarios = [str(x).strip() for x in cr if str(x).strip()]
        if not comentarios:
            leg = str(v.get("comentario", "") or "").strip()
            if leg:
                comentarios = [leg]
        item: dict[str, str | list[str]] = {"prazo_meta": prazo, "comentarios": comentarios}
        dp = str(v.get("descricao_personalizada", "") or "").strip()
        if dp:
            item["descricao_personalizada"] = dp
        out[str(k)] = item
    return out or None


def _explicacao_score_llm_de_row(row: dict[str, Any]) -> dict[str, Any] | None:
    """Lê JSONB ``explicacao_score_llm`` (última narrativa LLM do painel)."""
    raw = row.get("explicacao_score_llm")
    return cast("dict[str, Any]", raw) if isinstance(raw, dict) else None


def _painel_estado_ciclo_de_row(row: dict[str, Any]) -> str:
    """Fallback alinhado à migração 0048 para linhas antigas sem coluna hidratada no driver."""
    raw = row.get("painel_estado_ciclo")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return (
        PainelEstadoCicloDiagnostico.REALIZADO.value
        if str(row.get("status") or "") == StatusDiagnostico.FINALIZADO.value
        else PainelEstadoCicloDiagnostico.EM_ANDAMENTO.value
    )


def _row_dict_para_entity_listagem(row: dict[str, Any]) -> Diagnostico:
    """
    Hidrata entidade mínima para GET /diagnosticos/ (resumo do painel).

    Evita ler/parsear JSONB pesado (``score_completo``, quadro, LLM) na listagem.
    """
    raw_created = row.get("criado_em")
    criado_em = (
        datetime.fromisoformat(str(raw_created).replace("Z", "+00:00")) if raw_created else None
    )
    raw_fin = row.get("finalizado_em")
    finalizado_em = datetime.fromisoformat(str(raw_fin).replace("Z", "+00:00")) if raw_fin else None

    return Diagnostico(
        id=UUID(str(row["id"])),
        tenant_id=UUID(str(row["tenant_id"])),
        empresa=EmpresaInfo(
            cnpj=str(row.get("empresa_cnpj") or ""),
            razao_social=str(row.get("empresa_razao_social") or ""),
            porte=PorteEmpresa.MEDIO,
            regime=RegimeTributario.LUCRO_PRESUMIDO,
            cnae_principal="6201500",
            uf="SP",
            setor_macro=SetorMacro.SERVICOS,
        ),
        respondente=Respondente(email="listagem@placeholder.qdi"),
        status=StatusDiagnostico(str(row["status"])),
        plano=PlanoDiagnostico(str(row.get("plano", "gratuito"))),
        criado_em=criado_em if criado_em is not None else datetime.now(UTC),
        finalizado_em=finalizado_em,
        score_geral=row.get("score_geral"),
        relatorio_pdf_url=row.get("relatorio_pdf_url"),
        score_completo_snapshot=None,
        versao_otimista=int(row.get("versao_otimista") or 1),
        numero_interno_grupo=(
            int(raw_nim) if (raw_nim := row.get("numero_interno_grupo")) is not None else None
        ),
        painel_estado_ciclo=_painel_estado_ciclo_de_row(row),
    )


def _row_dict_para_entity(row: dict[str, Any]) -> Diagnostico:
    """Converte uma linha ``RealDict`` em entidade de domínio (paridade com Supabase)."""
    raw_created = row.get("criado_em")
    criado_em = (
        datetime.fromisoformat(str(raw_created).replace("Z", "+00:00")) if raw_created else None
    )
    raw_fin = row.get("finalizado_em")
    finalizado_em = datetime.fromisoformat(str(raw_fin).replace("Z", "+00:00")) if raw_fin else None

    snap: ScoreCompleto | None = None
    sc_raw = row.get("score_completo")
    if isinstance(sc_raw, dict):
        try:
            snap = ScoreCompleto.desde_dict(sc_raw)
        except (KeyError, TypeError, ValueError):
            snap = None

    email_resp = row.get("respondente_email") or "nao-informado@placeholder.qdi"

    m12_raw = row.get("checklist_m12_estado")
    checklist_m12 = normalizar_checklist_m12_estado_bruto(m12_raw)

    aceite_raw = row.get("aceite_termos_privacidade_em")
    aceite_em: datetime | None = None
    if aceite_raw is not None:
        aceite_em = datetime.fromisoformat(str(aceite_raw).replace("Z", "+00:00"))

    loc_raw = row.get("locale_relatorio") or "pt-BR"
    locale_relatorio = str(loc_raw).strip() if loc_raw is not None else "pt-BR"

    ff_raw = row.get("empresa_faixa_faturamento")
    faixa: FaixaFaturamentoDeclarada | None = None
    if ff_raw is not None and str(ff_raw).strip() != "":
        try:
            faixa = FaixaFaturamentoDeclarada(str(ff_raw).strip())
        except ValueError:
            faixa = None

    cnae_raw = row.get("empresa_cnae")
    cnae_principal = (
        str(cnae_raw).strip() if cnae_raw is not None and str(cnae_raw).strip() != "" else "6201500"
    )

    return Diagnostico(
        id=UUID(str(row["id"])),
        tenant_id=UUID(str(row["tenant_id"])),
        empresa=EmpresaInfo(
            cnpj=str(row["empresa_cnpj"]),
            razao_social=str(row["empresa_razao_social"]),
            porte=PorteEmpresa(str(row["empresa_porte"])),
            regime=RegimeTributario(str(row["empresa_regime"])),
            cnae_principal=cnae_principal,
            uf=str(row["empresa_uf"]),
            setor_macro=SetorMacro(str(row["empresa_setor_macro"])),
            faixa_faturamento=faixa,
        ),
        respondente=Respondente(
            email=str(email_resp),
            nome=row.get("respondente_nome"),
            cargo=row.get("respondente_cargo"),
            telefone=row.get("respondente_telefone"),
            ip_origem=row.get("respondente_ip_origem"),
        ),
        status=StatusDiagnostico(str(row["status"])),
        plano=PlanoDiagnostico(str(row.get("plano", "gratuito"))),
        criado_em=criado_em if criado_em is not None else datetime.now(UTC),
        finalizado_em=finalizado_em,
        score_geral=row.get("score_geral"),
        relatorio_pdf_url=row.get("relatorio_pdf_url"),
        score_completo_snapshot=snap,
        hash_evidencia=row.get("hash_sha256"),
        versao_otimista=int(row.get("versao_otimista") or 1),
        checklist_m12_estado=checklist_m12,
        quadro_implantacao_anotacoes=_quadro_anotacoes_de_row(row),
        aceite_termos_privacidade_em=aceite_em,
        locale_relatorio=locale_relatorio,
        versao_plano=int(row.get("versao_plano") or 1),
        explicacao_score_llm=_explicacao_score_llm_de_row(row),
        numero_interno_grupo=(
            int(raw_nim) if (raw_nim := row.get("numero_interno_grupo")) is not None else None
        ),
        painel_estado_ciclo=_painel_estado_ciclo_de_row(row),
    )


def _entity_para_params(d: Diagnostico) -> dict[str, Any]:
    """Monta dict de parâmetros para INSERT/UPSERT (tipos nativos + ``Json`` para JSONB)."""
    score_blob = (
        d.score_completo_snapshot.para_dict_serializavel()
        if d.score_completo_snapshot is not None
        else None
    )
    return {
        "id": d.id,
        "tenant_id": d.tenant_id,
        "respondente_email": d.respondente.email if d.respondente else None,
        "respondente_nome": d.respondente.nome if d.respondente else None,
        "respondente_cargo": d.respondente.cargo if d.respondente else None,
        "respondente_telefone": d.respondente.telefone if d.respondente else None,
        "respondente_ip_origem": d.respondente.ip_origem if d.respondente else None,
        "empresa_cnpj": d.empresa.cnpj,
        "empresa_razao_social": d.empresa.razao_social,
        "empresa_porte": d.empresa.porte.value,
        "empresa_regime": d.empresa.regime.value,
        "empresa_cnae": d.empresa.cnae_principal,
        "empresa_uf": d.empresa.uf,
        "empresa_setor_macro": d.empresa.setor_macro.value,
        "empresa_faixa_faturamento": (
            d.empresa.faixa_faturamento.value if d.empresa.faixa_faturamento is not None else None
        ),
        "status": d.status.value,
        "plano": d.plano.value,
        "score_geral": d.score_geral,
        "relatorio_pdf_url": d.relatorio_pdf_url,
        "criado_em": d.criado_em,
        "finalizado_em": d.finalizado_em,
        "hash_sha256": d.hash_evidencia,
        "score_completo": Json(score_blob) if score_blob is not None else None,
        "versao_otimista": d.versao_otimista,
        "checklist_m12_estado": (
            Json(d.checklist_m12_estado) if d.checklist_m12_estado is not None else None
        ),
        "quadro_implantacao_anotacoes": (
            Json(d.quadro_implantacao_anotacoes)
            if getattr(d, "quadro_implantacao_anotacoes", None) is not None
            else None
        ),
        "aceite_termos_privacidade_em": d.aceite_termos_privacidade_em,
        "locale_relatorio": getattr(d, "locale_relatorio", "pt-BR"),
        "versao_plano": int(getattr(d, "versao_plano", 1) or 1),
        "painel_estado_ciclo": getattr(
            d, "painel_estado_ciclo", PainelEstadoCicloDiagnostico.EM_ANDAMENTO.value
        ),
    }


_UPSERT_SQL = """
INSERT INTO diagnosticos (
    id, tenant_id,
    respondente_email, respondente_nome, respondente_cargo, respondente_telefone,
    respondente_ip_origem,
    empresa_cnpj, empresa_razao_social, empresa_porte, empresa_regime,
    empresa_cnae, empresa_uf, empresa_setor_macro, empresa_faixa_faturamento,
    status, plano, score_geral, relatorio_pdf_url,
    criado_em, finalizado_em,
    hash_sha256, score_completo, versao_otimista, checklist_m12_estado,
    quadro_implantacao_anotacoes,
    aceite_termos_privacidade_em, locale_relatorio, versao_plano, painel_estado_ciclo
) VALUES (
    %(id)s, %(tenant_id)s,
    %(respondente_email)s, %(respondente_nome)s, %(respondente_cargo)s, %(respondente_telefone)s,
    %(respondente_ip_origem)s,
    %(empresa_cnpj)s, %(empresa_razao_social)s, %(empresa_porte)s, %(empresa_regime)s,
    %(empresa_cnae)s, %(empresa_uf)s, %(empresa_setor_macro)s, %(empresa_faixa_faturamento)s,
    %(status)s, %(plano)s, %(score_geral)s, %(relatorio_pdf_url)s,
    %(criado_em)s, %(finalizado_em)s,
    %(hash_sha256)s, %(score_completo)s, %(versao_otimista)s, %(checklist_m12_estado)s,
    %(quadro_implantacao_anotacoes)s,
    %(aceite_termos_privacidade_em)s, %(locale_relatorio)s, %(versao_plano)s,
    %(painel_estado_ciclo)s
)
ON CONFLICT (id) DO UPDATE SET
    tenant_id = EXCLUDED.tenant_id,
    respondente_email = EXCLUDED.respondente_email,
    respondente_nome = EXCLUDED.respondente_nome,
    respondente_cargo = EXCLUDED.respondente_cargo,
    respondente_telefone = EXCLUDED.respondente_telefone,
    respondente_ip_origem = EXCLUDED.respondente_ip_origem,
    empresa_cnpj = EXCLUDED.empresa_cnpj,
    empresa_razao_social = EXCLUDED.empresa_razao_social,
    empresa_porte = EXCLUDED.empresa_porte,
    empresa_regime = EXCLUDED.empresa_regime,
    empresa_cnae = EXCLUDED.empresa_cnae,
    empresa_uf = EXCLUDED.empresa_uf,
    empresa_setor_macro = EXCLUDED.empresa_setor_macro,
    empresa_faixa_faturamento = EXCLUDED.empresa_faixa_faturamento,
    status = EXCLUDED.status,
    plano = EXCLUDED.plano,
    score_geral = EXCLUDED.score_geral,
    relatorio_pdf_url = EXCLUDED.relatorio_pdf_url,
    criado_em = EXCLUDED.criado_em,
    finalizado_em = EXCLUDED.finalizado_em,
    hash_sha256 = EXCLUDED.hash_sha256,
    score_completo = EXCLUDED.score_completo,
    versao_otimista = EXCLUDED.versao_otimista,
    checklist_m12_estado = EXCLUDED.checklist_m12_estado,
    quadro_implantacao_anotacoes = EXCLUDED.quadro_implantacao_anotacoes,
    aceite_termos_privacidade_em = EXCLUDED.aceite_termos_privacidade_em,
    locale_relatorio = EXCLUDED.locale_relatorio,
    versao_plano = EXCLUDED.versao_plano,
    painel_estado_ciclo = EXCLUDED.painel_estado_ciclo
"""


def _salvar_sync(dsn: str, diagnostico: Diagnostico) -> None:
    params = _entity_para_params(diagnostico)
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(_UPSERT_SQL, params)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _inserir_historico_cnpj_cur(
    cur: Any,
    tenant_id: UUID,
    diagnostico_id: UUID,
    itens: list[tuple[str, str | None, str]],
    cnpj_consulta_id: UUID | None,
) -> None:
    """Grava trilha append-only ligada à consulta CNPJ (mesma transação do UPSERT)."""
    if not itens:
        return
    cid = str(cnpj_consulta_id) if cnpj_consulta_id else None
    tid, did = str(tenant_id), str(diagnostico_id)
    for campo, anterior, novo in itens:
        cur.execute(
            """
            INSERT INTO diagnostico_empresa_campo_historico (
                tenant_id, diagnostico_id, cnpj_consulta_id,
                campo, valor_anterior, valor_novo
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (tid, did, cid, campo, anterior, novo),
        )


def _salvar_e_materializar_plano_sync(
    dsn: str,
    diagnostico: Diagnostico,
    score_completo: ScoreCompleto,
    *,
    historico_campos_empresa_cnpj: list[tuple[str, str | None, str]] | None = None,
    cnpj_consulta_id: UUID | None = None,
    linhas_resposta_questionario: tuple[LinhaRespostaQuestionario, ...] = (),
) -> PlanoPainelSerializado:
    """Transação única: UPSERT diagnóstico + substituição idempotente do plano ``versao_plano``."""
    vp = int(getattr(diagnostico, "versao_plano", 1) or 1)
    deriv = derivar_plano_painel_materializado(diagnostico, score_completo, versao_plano=vp)
    params = _entity_para_params(diagnostico)
    params["versao_plano"] = vp
    conn = psycopg2.connect(dsn)
    try:
        conn.autocommit = False
        with conn.cursor() as cur:
            cur.execute(_UPSERT_SQL, params)
            _inserir_historico_cnpj_cur(
                cur,
                diagnostico.tenant_id,
                diagnostico.id,
                historico_campos_empresa_cnpj or [],
                cnpj_consulta_id,
            )
        materializar_plano_em_conexao(conn, diagnostico, deriv)
        if linhas_resposta_questionario:
            with conn.cursor() as cur:
                inserir_respostas_questionario_em_cursor(
                    cur,
                    diagnostico.id,
                    diagnostico.tenant_id,
                    linhas_resposta_questionario,
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    out = buscar_plano_painel_serializado_sync(dsn, diagnostico.id, diagnostico.tenant_id)
    return out if out is not None else deriv.serializado_http


def _materializar_plano_backfill_sync(
    dsn: str, diagnostico_id: UUID, tenant_id: UUID
) -> PlanoPainelSerializado | None:
    if plano_materializado_existe_sync(dsn, diagnostico_id, tenant_id, 1):
        return None
    d = _buscar_sync(dsn, diagnostico_id, tenant_id)
    if d is None or d.status != StatusDiagnostico.FINALIZADO:
        return None
    sc = d.score_completo_snapshot
    if sc is None:
        return None
    deriv = derivar_plano_painel_materializado(d, sc, versao_plano=1)
    conn = psycopg2.connect(dsn)
    try:
        conn.autocommit = False
        materializar_plano_em_conexao(conn, d, deriv)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return buscar_plano_painel_serializado_sync(dsn, diagnostico_id, tenant_id)


def _buscar_sync(dsn: str, diagnostico_id: UUID, tenant_id: UUID) -> Diagnostico | None:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM diagnosticos
                WHERE id = %s AND tenant_id = %s
                LIMIT 1
                """,
                (str(diagnostico_id), str(tenant_id)),
            )
            row = cur.fetchone()
        if not row:
            return None
        return _row_dict_para_entity(cast("dict[str, Any]", dict(row)))
    finally:
        conn.close()


_STATUSES_ELIMINAVEIS_EMPRESA = frozenset({"em_andamento", "cancelado", "expirado"})


def _eliminar_empresa_sync(
    dsn: str,
    tenant_id: UUID,
    empresa_cnpj: str,
    *,
    actor_user_id: UUID | None,
) -> ResultadoEliminacaoEmpresa:
    _ = actor_user_id
    conn = psycopg2.connect(dsn)
    try:
        conn.autocommit = False
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, status
                FROM diagnosticos
                WHERE tenant_id = %s
                  AND empresa_cnpj = %s
                """,
                (str(tenant_id), empresa_cnpj),
            )
            rows = cur.fetchall()
            eliminados: list[UUID] = []
            mantidos_finalizados = 0
            mantidos_outros = 0
            for row in rows:
                st = str(row["status"])
                rid = UUID(str(row["id"]))
                if st == "finalizado":
                    mantidos_finalizados += 1
                elif st in _STATUSES_ELIMINAVEIS_EMPRESA:
                    cur.execute(
                        """
                        DELETE FROM diagnosticos
                        WHERE id = %s
                          AND tenant_id = %s
                        """,
                        (str(rid), str(tenant_id)),
                    )
                    if cur.rowcount == 1:
                        eliminados.append(rid)
                else:
                    mantidos_outros += 1
        conn.commit()
        return ResultadoEliminacaoEmpresa(
            empresa_cnpj=empresa_cnpj,
            eliminados_ids=tuple(eliminados),
            mantidos_finalizados=mantidos_finalizados,
            mantidos_outros_status=mantidos_outros,
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _listar_resumo_sync(
    dsn: str,
    tenant_id: UUID,
    limit: int,
    offset: int,
    empresa_cnpj: str | None = None,
    *,
    excluir_empresas_arquivadas: bool = False,
) -> list[Diagnostico]:
    """Listagem do painel — colunas mínimas (sem JSONB de score completo / quadro)."""
    return _listar_sync(
        dsn,
        tenant_id,
        limit,
        offset,
        empresa_cnpj,
        excluir_empresas_arquivadas=excluir_empresas_arquivadas,
        apenas_colunas_resumo=True,
    )


def _listar_sync(
    dsn: str,
    tenant_id: UUID,
    limit: int,
    offset: int,
    empresa_cnpj: str | None = None,
    *,
    excluir_empresas_arquivadas: bool = False,
    apenas_colunas_resumo: bool = False,
) -> list[Diagnostico]:
    motivo_refazer_sql = MOTIVO_REFAZER_QUESTIONARIO_PAINEL.replace("'", "''")
    filtro_arquivo = ""
    if excluir_empresas_arquivadas and not empresa_cnpj:
        filtro_arquivo = """
              AND (
                COALESCE(d.empresa_cnpj, '') = ''
                OR NOT EXISTS (
                    SELECT 1 FROM empresa_painel_arquivo epa
                    WHERE epa.tenant_id = d.tenant_id
                      AND epa.empresa_cnpj = d.empresa_cnpj
                )
              )
        """
    if apenas_colunas_resumo:
        colunas = f"""
    d.id, d.tenant_id,
    d.empresa_cnpj, d.empresa_razao_social,
    d.status, d.plano,
    COALESCE(
        (
            SELECT (r.payload_retificacao->>'score_geral')::double precision
            FROM diagnostico_retificacao r
            WHERE r.diagnostico_original_id = d.id
              AND r.tenant_id = d.tenant_id
              AND r.motivo_retificacao = '{motivo_refazer_sql}'
            ORDER BY r.criado_em DESC
            LIMIT 1
        ),
        d.score_geral
    ) AS score_geral,
    d.criado_em, d.finalizado_em, d.relatorio_pdf_url,
    d.numero_interno_grupo, d.versao_otimista, d.painel_estado_ciclo
"""
        from_clause = "diagnosticos d"
    else:
        colunas = "*"
        from_clause = "diagnosticos"
        if filtro_arquivo:
            filtro_arquivo = filtro_arquivo.replace("d.", "diagnosticos.")
    para_entity = _row_dict_para_entity_listagem if apenas_colunas_resumo else _row_dict_para_entity

    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if empresa_cnpj:
                cur.execute(
                    f"""
                    SELECT {colunas} FROM {from_clause}
                    WHERE {"d." if apenas_colunas_resumo else ""}tenant_id = %s
                      AND {"d." if apenas_colunas_resumo else ""}empresa_cnpj = %s
                    ORDER BY {"d." if apenas_colunas_resumo else ""}criado_em DESC
                    LIMIT %s OFFSET %s
                    """,
                    (str(tenant_id), empresa_cnpj, limit, offset),
                )
            else:
                sql_com_arquivo = f"""
                    SELECT {colunas} FROM {from_clause}
                    WHERE {"d." if apenas_colunas_resumo else ""}tenant_id = %s
                    {filtro_arquivo}
                    ORDER BY {"d." if apenas_colunas_resumo else ""}criado_em DESC
                    LIMIT %s OFFSET %s
                """
                params = (str(tenant_id), limit, offset)
                try:
                    cur.execute(sql_com_arquivo, params)
                except Exception as exc:
                    from src.infrastructure.repositories.postgres_empresa_painel_arquivo_compat import (
                        erro_tabela_empresa_painel_arquivo_ausente,
                    )

                    if filtro_arquivo and erro_tabela_empresa_painel_arquivo_ausente(exc):
                        cur.execute(
                            f"""
                            SELECT {colunas} FROM {from_clause}
                            WHERE {"d." if apenas_colunas_resumo else ""}tenant_id = %s
                            ORDER BY {"d." if apenas_colunas_resumo else ""}criado_em DESC
                            LIMIT %s OFFSET %s
                            """,
                            params,
                        )
                    else:
                        raise
            rows = cur.fetchall()
        return [para_entity(cast("dict[str, Any]", dict(r))) for r in rows]
    finally:
        conn.close()


def _patch_relatorio_sync(
    dsn: str,
    diagnostico_id: UUID,
    tenant_id: UUID,
    relatorio_pdf_url: str,
    versao_esperada: int,
) -> Diagnostico | None:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE diagnosticos
                SET relatorio_pdf_url = %s,
                    versao_otimista = versao_otimista + 1
                WHERE id = %s AND tenant_id = %s AND versao_otimista = %s
                RETURNING *
                """,
                (relatorio_pdf_url, str(diagnostico_id), str(tenant_id), versao_esperada),
            )
            row = cur.fetchone()
        conn.commit()
        if not row:
            return None
        return _row_dict_para_entity(cast("dict[str, Any]", dict(row)))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _patch_quadro_sync(
    dsn: str,
    diagnostico_id: UUID,
    tenant_id: UUID,
    quadro_implantacao_anotacoes: dict[str, dict[str, Any]],
    versao_esperada: int,
) -> Diagnostico | None:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE diagnosticos
                SET quadro_implantacao_anotacoes = %s,
                    versao_otimista = versao_otimista + 1
                WHERE id = %s AND tenant_id = %s AND versao_otimista = %s
                RETURNING *
                """,
                (
                    Json(quadro_implantacao_anotacoes),
                    str(diagnostico_id),
                    str(tenant_id),
                    versao_esperada,
                ),
            )
            row = cur.fetchone()
        conn.commit()
        if not row:
            return None
        return _row_dict_para_entity(cast("dict[str, Any]", dict(row)))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _patch_painel_estado_ciclo_sync(
    dsn: str,
    diagnostico_id: UUID,
    tenant_id: UUID,
    painel_estado_ciclo: str,
    versao_esperada: int,
) -> Diagnostico | None:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE diagnosticos
                SET painel_estado_ciclo = %s,
                    versao_otimista = versao_otimista + 1
                WHERE id = %s AND tenant_id = %s AND versao_otimista = %s
                RETURNING *
                """,
                (
                    painel_estado_ciclo,
                    str(diagnostico_id),
                    str(tenant_id),
                    versao_esperada,
                ),
            )
            row = cur.fetchone()
        conn.commit()
        if not row:
            return None
        return _row_dict_para_entity(cast("dict[str, Any]", dict(row)))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _patch_m12_sync(
    dsn: str,
    diagnostico_id: UUID,
    tenant_id: UUID,
    checklist_m12_estado: list[int],
    versao_esperada: int,
) -> Diagnostico | None:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE diagnosticos
                SET checklist_m12_estado = %s,
                    versao_otimista = versao_otimista + 1
                WHERE id = %s AND tenant_id = %s AND versao_otimista = %s
                RETURNING *
                """,
                (Json(checklist_m12_estado), str(diagnostico_id), str(tenant_id), versao_esperada),
            )
            row = cur.fetchone()
        conn.commit()
        if not row:
            return None
        return _row_dict_para_entity(cast("dict[str, Any]", dict(row)))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _limpar_explicacao_score_llm_sync(
    dsn: str,
    diagnostico_id: UUID,
    tenant_id: UUID,
) -> None:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE diagnosticos
                SET explicacao_score_llm = NULL
                WHERE id = %s AND tenant_id = %s
                """,
                (str(diagnostico_id), str(tenant_id)),
            )
            if cur.rowcount == 0:
                raise ValueError("Diagnóstico não encontrado para limpar explicação LLM")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _patch_explicacao_score_llm_sync(
    dsn: str,
    diagnostico_id: UUID,
    tenant_id: UUID,
    snapshot: dict[str, Any],
) -> None:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE diagnosticos
                SET explicacao_score_llm = %s
                WHERE id = %s AND tenant_id = %s
                """,
                (Json(snapshot), str(diagnostico_id), str(tenant_id)),
            )
            if cur.rowcount == 0:
                raise ValueError("Diagnóstico não encontrado para persistir explicação LLM")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class PostgresDiagnosticoRepository(DiagnosticoRepository):
    """Adapter Postgres síncrono por baixo de ``asyncio.to_thread``."""

    def __init__(self, dsn_sync: str) -> None:
        self._dsn = dsn_sync

    async def salvar(self, diagnostico: Diagnostico) -> None:
        await asyncio.to_thread(_salvar_sync, self._dsn, diagnostico)

    async def salvar_e_materializar_plano_painel(
        self,
        diagnostico: Diagnostico,
        score_completo: ScoreCompleto,
        *,
        historico_campos_empresa_cnpj: list[tuple[str, str | None, str]] | None = None,
        cnpj_consulta_id: UUID | None = None,
        linhas_resposta_questionario: tuple[LinhaRespostaQuestionario, ...] = (),
    ) -> PlanoPainelSerializado:
        return await asyncio.to_thread(
            _salvar_e_materializar_plano_sync,
            self._dsn,
            diagnostico,
            score_completo,
            historico_campos_empresa_cnpj=historico_campos_empresa_cnpj,
            cnpj_consulta_id=cnpj_consulta_id,
            linhas_resposta_questionario=linhas_resposta_questionario,
        )

    async def listar_respostas_questionario(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
    ) -> list[dict[str, Any]]:
        return await asyncio.to_thread(
            listar_respostas_questionario_sync,
            self._dsn,
            diagnostico_id,
            tenant_id,
        )

    async def proximo_refazer_lote_respostas(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
    ) -> int:
        return await asyncio.to_thread(
            proximo_refazer_lote_respostas_sync,
            self._dsn,
            diagnostico_id,
            tenant_id,
        )

    async def inserir_respostas_questionario_refazer(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        linhas: tuple[LinhaRespostaQuestionario, ...],
        *,
        refazer_lote: int,
    ) -> None:
        await asyncio.to_thread(
            inserir_respostas_questionario_refazer_sync,
            self._dsn,
            diagnostico_id,
            tenant_id,
            linhas,
            refazer_lote=refazer_lote,
        )

    async def limpar_explicacao_score_llm(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
    ) -> None:
        await asyncio.to_thread(
            _limpar_explicacao_score_llm_sync,
            self._dsn,
            diagnostico_id,
            tenant_id,
        )

    async def buscar_plano_painel_serializado(
        self, diagnostico_id: UUID, tenant_id: UUID
    ) -> PlanoPainelSerializado | None:
        return await asyncio.to_thread(
            buscar_plano_painel_serializado_sync, self._dsn, diagnostico_id, tenant_id
        )

    async def materializar_plano_painel_idempotente_backfill(
        self, diagnostico_id: UUID, tenant_id: UUID
    ) -> PlanoPainelSerializado | None:
        return await asyncio.to_thread(
            _materializar_plano_backfill_sync, self._dsn, diagnostico_id, tenant_id
        )

    async def inserir_subtarefa_plano(
        self,
        tenant_id: UUID,
        diagnostico_id: UUID,
        plano_acao_id: UUID,
        titulo: str,
        ordem: int = 0,
    ) -> dict[str, Any]:
        return await asyncio.to_thread(
            inserir_subtarefa_sync,
            self._dsn,
            tenant_id,
            diagnostico_id,
            plano_acao_id,
            titulo,
            ordem,
        )

    async def atualizar_subtarefa_plano(
        self,
        tenant_id: UUID,
        diagnostico_id: UUID,
        subtarefa_id: UUID,
        *,
        titulo: str | None = None,
        status: str | None = None,
        prazo: date | None = None,
        comentarios: str | None = None,
        ordem: int | None = None,
    ) -> dict[str, Any] | None:
        return await asyncio.to_thread(
            atualizar_subtarefa_sync,
            self._dsn,
            tenant_id,
            diagnostico_id,
            subtarefa_id,
            titulo=titulo,
            status=status,
            prazo=prazo,
            comentarios=comentarios,
            ordem=ordem,
        )

    async def buscar_por_id(self, diagnostico_id: UUID, tenant_id: UUID) -> Diagnostico | None:
        return await asyncio.to_thread(_buscar_sync, self._dsn, diagnostico_id, tenant_id)

    async def listar_por_tenant(
        self,
        tenant_id: UUID,
        limit: int = 100,
        offset: int = 0,
        *,
        empresa_cnpj: str | None = None,
        excluir_empresas_arquivadas: bool = False,
    ) -> list[Diagnostico]:
        return await asyncio.to_thread(
            _listar_resumo_sync,
            self._dsn,
            tenant_id,
            limit,
            offset,
            empresa_cnpj,
            excluir_empresas_arquivadas=excluir_empresas_arquivadas,
        )

    async def eliminar_diagnosticos_empresa_eliminaveis(
        self,
        tenant_id: UUID,
        empresa_cnpj: str,
        *,
        actor_user_id: UUID | None = None,
    ) -> ResultadoEliminacaoEmpresa:
        return await asyncio.to_thread(
            _eliminar_empresa_sync,
            self._dsn,
            tenant_id,
            empresa_cnpj,
            actor_user_id=actor_user_id,
        )

    async def atualizar_relatorio_pdf_com_versao(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        relatorio_pdf_url: str,
        versao_esperada: int,
    ) -> Diagnostico | None:
        return await asyncio.to_thread(
            _patch_relatorio_sync,
            self._dsn,
            diagnostico_id,
            tenant_id,
            relatorio_pdf_url,
            versao_esperada,
        )

    async def atualizar_checklist_m12_com_versao(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        checklist_m12_estado: list[int],
        versao_esperada: int,
    ) -> Diagnostico | None:
        return await asyncio.to_thread(
            _patch_m12_sync,
            self._dsn,
            diagnostico_id,
            tenant_id,
            checklist_m12_estado,
            versao_esperada,
        )

    async def atualizar_quadro_implantacao_com_versao(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        quadro_implantacao_anotacoes: dict[str, dict[str, Any]],
        versao_esperada: int,
    ) -> Diagnostico | None:
        return await asyncio.to_thread(
            _patch_quadro_sync,
            self._dsn,
            diagnostico_id,
            tenant_id,
            quadro_implantacao_anotacoes,
            versao_esperada,
        )

    async def atualizar_painel_estado_ciclo_com_versao(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        painel_estado_ciclo: str,
        versao_esperada: int,
    ) -> Diagnostico | None:
        return await asyncio.to_thread(
            _patch_painel_estado_ciclo_sync,
            self._dsn,
            diagnostico_id,
            tenant_id,
            painel_estado_ciclo,
            versao_esperada,
        )

    async def atualizar_explicacao_score_llm(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        snapshot: dict[str, Any],
    ) -> None:
        await asyncio.to_thread(
            _patch_explicacao_score_llm_sync,
            self._dsn,
            diagnostico_id,
            tenant_id,
            snapshot,
        )

    async def registrar_explicacao_score_llm_historico(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        snapshot: dict[str, Any],
        *,
        actor_user_id: UUID | None,
        trace_id: str | None,
    ) -> None:
        from src.infrastructure.repositories.postgres_explicacao_score_llm_historico_sync import (
            inserir_explicacao_score_llm_historico_sync,
        )

        await asyncio.to_thread(
            inserir_explicacao_score_llm_historico_sync,
            self._dsn,
            tenant_id=tenant_id,
            diagnostico_id=diagnostico_id,
            snapshot=snapshot,
            actor_user_id=actor_user_id,
            trace_id=trace_id,
        )

    async def listar_explicacao_score_llm_historico(
        self,
        diagnostico_id: UUID,
        tenant_id: UUID,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        from src.infrastructure.repositories.postgres_explicacao_score_llm_historico_sync import (
            listar_explicacao_score_llm_historico_sync,
        )

        return await asyncio.to_thread(
            listar_explicacao_score_llm_historico_sync,
            self._dsn,
            tenant_id=tenant_id,
            diagnostico_id=diagnostico_id,
            limit=limit,
        )
