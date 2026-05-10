"""
Montagem do payload canónico de export portável (LGPD art. 18, V — ADR-012 §4).

Camada: Domain (puro — sem I/O)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.domain.entities.diagnostico import Diagnostico, StatusDiagnostico


def montar_payload_export_v1(
    diagnostico: Diagnostico,
    *,
    exportado_em: datetime | None = None,
) -> dict[str, Any]:
    """
    Constrói o dicionário serializável alinhado a ``docs/schemas/qdi-diagnostico-export-v1.schema.json``.

    Analogia: como serializar um ``TPedido`` para XML canónico antes do ``UPDATE`` —
    aqui é só leitura / cópia estruturada para portabilidade.
    """
    ts = exportado_em or datetime.now(UTC)
    export_iso = ts.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    emp = diagnostico.empresa
    empresa_out: dict[str, Any] = {
        "cnpj": emp.cnpj,
        "razao_social": emp.razao_social,
        "porte": emp.porte.value,
        "regime": emp.regime.value,
        "cnae_principal": emp.cnae_principal,
        "uf": emp.uf,
        "setor_macro": emp.setor_macro.value,
        "faixa_faturamento": emp.faixa_faturamento.value if emp.faixa_faturamento else None,
    }
    resp = diagnostico.respondente
    respondente_out: dict[str, Any] = {
        "email": resp.email,
        "nome": resp.nome,
        "cargo": resp.cargo,
        "telefone": resp.telefone,
    }
    score_blob: dict[str, Any] | None = None
    if diagnostico.score_completo_snapshot is not None:
        score_blob = diagnostico.score_completo_snapshot.para_dict_serializavel()

    fin = diagnostico.finalizado_em
    aceite = diagnostico.aceite_termos_privacidade_em

    return {
        "schema_id": "qdi-diagnostico-export-v1",
        "schema_version": "1.0.0",
        "exportado_em": export_iso,
        "diagnostico_id": str(diagnostico.id),
        "tenant_id": str(diagnostico.tenant_id),
        "status": diagnostico.status.value,
        "plano": diagnostico.plano.value,
        "hash_evidencia_sha256": diagnostico.hash_evidencia,
        "score_geral": diagnostico.score_geral,
        "score_completo": score_blob,
        "relatorio_pdf_url": diagnostico.relatorio_pdf_url,
        "locale_relatorio": diagnostico.locale_relatorio,
        "versao_otimista": diagnostico.versao_otimista,
        "criado_em": diagnostico.criado_em.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        "finalizado_em": (
            fin.astimezone(UTC).isoformat().replace("+00:00", "Z") if fin is not None else None
        ),
        "aceite_termos_privacidade_em": (
            aceite.astimezone(UTC).isoformat().replace("+00:00", "Z") if aceite else None
        ),
        "checklist_m12_estado": diagnostico.checklist_m12_estado,
        "empresa": empresa_out,
        "respondente": respondente_out,
        "quadro_implantacao_anotacoes": diagnostico.quadro_implantacao_anotacoes,
        "bloqueios_export": {
            "apenas_finalizado_com_evidencia": diagnostico.status == StatusDiagnostico.FINALIZADO
            and bool(diagnostico.hash_evidencia),
        },
    }
