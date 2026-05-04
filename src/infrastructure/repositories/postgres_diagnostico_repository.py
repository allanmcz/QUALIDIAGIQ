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
from datetime import UTC, datetime
from typing import Any, cast
from uuid import UUID

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    FaixaFaturamentoDeclarada,
    PlanoDiagnostico,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
    StatusDiagnostico,
)
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.domain.value_objects.score import ScoreCompleto


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
    checklist_m12: list[bool] | None = None
    if isinstance(m12_raw, list):
        try:
            checklist_m12 = [bool(x) for x in m12_raw]
        except (TypeError, ValueError):
            checklist_m12 = None

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
    }


_UPSERT_SQL = """
INSERT INTO diagnosticos (
    id, tenant_id,
    respondente_email, respondente_nome, respondente_cargo, respondente_telefone,
    empresa_cnpj, empresa_razao_social, empresa_porte, empresa_regime,
    empresa_cnae, empresa_uf, empresa_setor_macro, empresa_faixa_faturamento,
    status, plano, score_geral, relatorio_pdf_url,
    criado_em, finalizado_em,
    hash_sha256, score_completo, versao_otimista, checklist_m12_estado,
    quadro_implantacao_anotacoes,
    aceite_termos_privacidade_em, locale_relatorio
) VALUES (
    %(id)s, %(tenant_id)s,
    %(respondente_email)s, %(respondente_nome)s, %(respondente_cargo)s, %(respondente_telefone)s,
    %(empresa_cnpj)s, %(empresa_razao_social)s, %(empresa_porte)s, %(empresa_regime)s,
    %(empresa_cnae)s, %(empresa_uf)s, %(empresa_setor_macro)s, %(empresa_faixa_faturamento)s,
    %(status)s, %(plano)s, %(score_geral)s, %(relatorio_pdf_url)s,
    %(criado_em)s, %(finalizado_em)s,
    %(hash_sha256)s, %(score_completo)s, %(versao_otimista)s, %(checklist_m12_estado)s,
    %(quadro_implantacao_anotacoes)s,
    %(aceite_termos_privacidade_em)s, %(locale_relatorio)s
)
ON CONFLICT (id) DO UPDATE SET
    tenant_id = EXCLUDED.tenant_id,
    respondente_email = EXCLUDED.respondente_email,
    respondente_nome = EXCLUDED.respondente_nome,
    respondente_cargo = EXCLUDED.respondente_cargo,
    respondente_telefone = EXCLUDED.respondente_telefone,
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
    locale_relatorio = EXCLUDED.locale_relatorio
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


def _listar_sync(dsn: str, tenant_id: UUID, limit: int, offset: int) -> list[Diagnostico]:
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT * FROM diagnosticos
                WHERE tenant_id = %s
                ORDER BY criado_em DESC
                LIMIT %s OFFSET %s
                """,
                (str(tenant_id), limit, offset),
            )
            rows = cur.fetchall()
        return [_row_dict_para_entity(cast("dict[str, Any]", dict(r))) for r in rows]
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


def _patch_m12_sync(
    dsn: str,
    diagnostico_id: UUID,
    tenant_id: UUID,
    checklist_m12_estado: list[bool],
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


class PostgresDiagnosticoRepository(DiagnosticoRepository):
    """Adapter Postgres síncrono por baixo de ``asyncio.to_thread``."""

    def __init__(self, dsn_sync: str) -> None:
        self._dsn = dsn_sync

    async def salvar(self, diagnostico: Diagnostico) -> None:
        await asyncio.to_thread(_salvar_sync, self._dsn, diagnostico)

    async def buscar_por_id(self, diagnostico_id: UUID, tenant_id: UUID) -> Diagnostico | None:
        return await asyncio.to_thread(_buscar_sync, self._dsn, diagnostico_id, tenant_id)

    async def listar_por_tenant(
        self, tenant_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[Diagnostico]:
        return await asyncio.to_thread(_listar_sync, self._dsn, tenant_id, limit, offset)

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
        checklist_m12_estado: list[bool],
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
