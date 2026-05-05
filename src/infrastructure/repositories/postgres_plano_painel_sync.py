"""
Operações síncronas de materialização do plano de ação (psycopg2).

Camada: Infrastructure — usada por ``PostgresDiagnosticoRepository`` via ``asyncio.to_thread``.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any, cast
from uuid import UUID

import psycopg2
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor

from src.application.services.plano_painel_derivacao import DerivacaoPlanoMaterializado
from src.domain.entities.diagnostico import Diagnostico
from src.domain.value_objects.plano_painel_serializado import PlanoPainelSerializado


def _limpar_plano_versao(
    cur: Any, diagnostico_id: UUID, tenant_id: UUID, versao_plano: int
) -> None:
    cur.execute(
        """
        DELETE FROM diagnostico_plano_matriz
        WHERE diagnostico_id = %s AND tenant_id = %s AND versao_plano = %s
        """,
        (str(diagnostico_id), str(tenant_id), versao_plano),
    )
    cur.execute(
        """
        DELETE FROM diagnostico_plano_cronograma
        WHERE diagnostico_id = %s AND tenant_id = %s AND versao_plano = %s
        """,
        (str(diagnostico_id), str(tenant_id), versao_plano),
    )
    cur.execute(
        """
        DELETE FROM diagnostico_plano_acao
        WHERE diagnostico_id = %s AND tenant_id = %s AND versao_plano = %s
        """,
        (str(diagnostico_id), str(tenant_id), versao_plano),
    )


def _inserir_plano_derivacao(
    cur: Any,
    diagnostico_id: UUID,
    tenant_id: UUID,
    deriv: DerivacaoPlanoMaterializado,
) -> None:
    v = deriv.versao_plano
    for ln in deriv.linhas_acao:
        cur.execute(
            """
            INSERT INTO diagnostico_plano_acao (
                id, diagnostico_id, tenant_id, versao_plano, ordem_exibicao,
                frente_indice, acao_indice, frente_nome, texto_acao,
                responsavel_sugerido, prazo_sugerido_texto, criticidade, base_legal,
                origem_motor, prioridade_motor
            ) VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s
            )
            """,
            (
                str(ln.id),
                str(diagnostico_id),
                str(tenant_id),
                v,
                ln.ordem_exibicao,
                ln.frente_indice,
                ln.acao_indice,
                ln.frente_nome,
                ln.texto_acao,
                ln.responsavel_sugerido,
                ln.prazo_sugerido_texto,
                ln.criticidade,
                ln.base_legal,
                ln.origem_motor,
                ln.prioridade_motor,
            ),
        )
    for m in deriv.linhas_matriz:
        cur.execute(
            """
            INSERT INTO diagnostico_plano_matriz (
                id, diagnostico_id, tenant_id, versao_plano, ordem_exibicao,
                departamento, impacto_resumo, criticidade, base_legal
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(m.id),
                str(diagnostico_id),
                str(tenant_id),
                v,
                m.ordem_exibicao,
                m.departamento,
                m.impacto_resumo,
                m.criticidade,
                m.base_legal,
            ),
        )
    for c in deriv.linhas_cronograma:
        cur.execute(
            """
            INSERT INTO diagnostico_plano_cronograma (
                id, diagnostico_id, tenant_id, versao_plano, ordem_exibicao,
                fase, foco, referencia_normativa
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                str(c.id),
                str(diagnostico_id),
                str(tenant_id),
                v,
                c.ordem_exibicao,
                c.fase,
                c.foco,
                c.referencia_normativa,
            ),
        )


def materializar_plano_em_conexao(
    conn: PgConnection,
    diagnostico: Diagnostico,
    deriv: DerivacaoPlanoMaterializado,
) -> None:
    """Escreve linhas do plano (transação deve ser gerida pelo chamador)."""
    with conn.cursor() as cur:
        _limpar_plano_versao(cur, diagnostico.id, diagnostico.tenant_id, deriv.versao_plano)
        _inserir_plano_derivacao(cur, diagnostico.id, diagnostico.tenant_id, deriv)


def plano_materializado_existe_sync(
    dsn: str, diagnostico_id: UUID, tenant_id: UUID, versao_plano: int = 1
) -> bool:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1 FROM diagnostico_plano_acao
                WHERE diagnostico_id = %s AND tenant_id = %s AND versao_plano = %s
                LIMIT 1
                """,
                (str(diagnostico_id), str(tenant_id), versao_plano),
            )
            return cur.fetchone() is not None
    finally:
        conn.close()


def buscar_plano_painel_serializado_sync(
    dsn: str, diagnostico_id: UUID, tenant_id: UUID
) -> PlanoPainelSerializado | None:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM diagnostico_plano_acao
                WHERE diagnostico_id = %s AND tenant_id = %s
                ORDER BY ordem_exibicao ASC
                """,
                (str(diagnostico_id), str(tenant_id)),
            )
            acoes = cur.fetchall()
            if not acoes:
                return None
            versao_plano = int(acoes[0]["versao_plano"])

            cur.execute(
                """
                SELECT * FROM diagnostico_plano_matriz
                WHERE diagnostico_id = %s AND tenant_id = %s AND versao_plano = %s
                ORDER BY ordem_exibicao ASC
                """,
                (str(diagnostico_id), str(tenant_id), versao_plano),
            )
            mat_rows = cur.fetchall()

            cur.execute(
                """
                SELECT * FROM diagnostico_plano_cronograma
                WHERE diagnostico_id = %s AND tenant_id = %s AND versao_plano = %s
                ORDER BY ordem_exibicao ASC
                """,
                (str(diagnostico_id), str(tenant_id), versao_plano),
            )
            cro_rows = cur.fetchall()

            cur.execute(
                """
                SELECT * FROM diagnostico_plano_subtarefa
                WHERE diagnostico_id = %s AND tenant_id = %s
                ORDER BY plano_acao_id, ordem ASC, criado_em ASC
                """,
                (str(diagnostico_id), str(tenant_id)),
            )
            sub_rows = cur.fetchall()

        por_fi: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for r in acoes:
            por_fi[int(r["frente_indice"])].append(dict(r))

        checklist: list[dict[str, Any]] = []
        for fi in sorted(por_fi.keys()):
            rows_f = sorted(por_fi[fi], key=lambda x: int(x["ordem_exibicao"]))
            nome_f = str(rows_f[0]["frente_nome"])
            acoes_http: list[dict[str, Any]] = []
            for r in rows_f:
                pid = str(r["id"])
                st_list = [
                    _subtarefa_row_para_http(dict(sr))
                    for sr in sub_rows
                    if str(sr["plano_acao_id"]) == pid
                ]
                acoes_http.append(
                    {
                        "descricao": r["texto_acao"],
                        "responsavel": r["responsavel_sugerido"],
                        "prazo": r["prazo_sugerido_texto"],
                        "criticidade": r["criticidade"],
                        "base_legal": r["base_legal"],
                        "prioridade": int(r["prioridade_motor"]),
                        "plano_acao_id": pid,
                        "chave_quadro_legado": f"f{int(r['frente_indice'])}_a{int(r['acao_indice'])}",
                        "subtarefas": st_list,
                    }
                )
            checklist.append({"nome": nome_f, "acoes": acoes_http})

        matriz_http = [
            {
                "departamento": mr["departamento"],
                "impacto_resumo": mr["impacto_resumo"],
                "criticidade": mr["criticidade"],
                "base_legal": mr["base_legal"],
            }
            for mr in mat_rows
        ]
        cron_http = [
            {
                "fase": cr["fase"],
                "foco": cr["foco"],
                "referencia_normativa": cr["referencia_normativa"],
            }
            for cr in cro_rows
        ]

        sub_map: dict[str, tuple[dict[str, Any], ...]] = {}
        for sr in sub_rows:
            pid = str(sr["plano_acao_id"])
            sub_map.setdefault(pid, ())
            sub_map[pid] = (*sub_map[pid], _subtarefa_row_para_http(dict(sr)))

        return PlanoPainelSerializado(
            versao_plano=versao_plano,
            checklist=tuple(checklist),
            matriz_impacto=tuple(matriz_http),
            cronograma=tuple(cron_http),
            subtarefas_por_acao=sub_map,
        )
    finally:
        conn.close()


def _subtarefa_row_para_http(r: dict[str, Any]) -> dict[str, Any]:
    prazo = r.get("prazo")
    prazo_out: str | None
    if prazo is None:
        prazo_out = None
    elif isinstance(prazo, datetime):
        prazo_out = prazo.date().isoformat()
    else:
        prazo_out = str(prazo)[:10]
    return {
        "id": str(r["id"]),
        "titulo": r["titulo"],
        "status": r["status"],
        "prazo": prazo_out,
        "comentarios": r.get("comentarios"),
        "ordem": int(r["ordem"]),
    }


def inserir_subtarefa_sync(
    dsn: str,
    tenant_id: UUID,
    diagnostico_id: UUID,
    plano_acao_id: UUID,
    titulo: str,
    ordem: int,
) -> dict[str, Any]:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT 1 FROM diagnostico_plano_acao
                WHERE id = %s AND diagnostico_id = %s AND tenant_id = %s
                LIMIT 1
                """,
                (str(plano_acao_id), str(diagnostico_id), str(tenant_id)),
            )
            if cur.fetchone() is None:
                raise ValueError("Ação do plano inexistente ou fora do tenant/diagnóstico.")
            cur.execute(
                """
                INSERT INTO diagnostico_plano_subtarefa (
                    plano_acao_id, diagnostico_id, tenant_id, titulo, ordem
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING *
                """,
                (str(plano_acao_id), str(diagnostico_id), str(tenant_id), titulo.strip(), ordem),
            )
            row = cur.fetchone()
        conn.commit()
        assert row is not None
        return _subtarefa_row_para_http(cast("dict[str, Any]", dict(row)))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def atualizar_subtarefa_sync(
    dsn: str,
    tenant_id: UUID,
    diagnostico_id: UUID,
    subtarefa_id: UUID,
    *,
    titulo: str | None,
    status: str | None,
    prazo: date | None,
    comentarios: str | None,
    ordem: int | None,
) -> dict[str, Any] | None:
    sets: list[str] = []
    vals: list[Any] = []
    if titulo is not None:
        sets.append("titulo = %s")
        vals.append(titulo.strip())
    if status is not None:
        sets.append("status = %s")
        vals.append(status.strip())
    if prazo is not None:
        sets.append("prazo = %s")
        vals.append(prazo)
    if comentarios is not None:
        sets.append("comentarios = %s")
        vals.append(comentarios)
    if ordem is not None:
        sets.append("ordem = %s")
        vals.append(ordem)
    if not sets:
        conn = psycopg2.connect(dsn)
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT * FROM diagnostico_plano_subtarefa
                    WHERE id = %s AND tenant_id = %s AND diagnostico_id = %s
                    """,
                    (str(subtarefa_id), str(tenant_id), str(diagnostico_id)),
                )
                row = cur.fetchone()
            return _subtarefa_row_para_http(dict(row)) if row else None
        finally:
            conn.close()
    sets.append("atualizado_em = CURRENT_TIMESTAMP")
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            vals.extend([str(subtarefa_id), str(tenant_id), str(diagnostico_id)])
            cur.execute(
                f"""
                UPDATE diagnostico_plano_subtarefa
                SET {", ".join(sets)}
                WHERE id = %s AND tenant_id = %s AND diagnostico_id = %s
                RETURNING *
                """,
                vals,
            )
            row = cur.fetchone()
        conn.commit()
        return _subtarefa_row_para_http(dict(row)) if row else None
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
