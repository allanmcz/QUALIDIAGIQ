"""
Orquestração — consulta CNPJ com TTL triplo, idempotência e persistência auditável.

Camada: Application
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from src.application.ports.cnpj_consulta_repository_port import CnpjConsultaRepositoryPort
from src.application.ports.cnpj_provedor_externo_port import CnpjProvedorExternoPort
from src.application.services.cnpj_consulta_mapeamento import sugestao_desde_payload_receita


def _hash_canonico(canon: dict[str, Any]) -> str:
    blob = json.dumps(canon, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _as_dict_jsonb(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    return {}


@dataclass(frozen=True)
class CnpjTtlSegundos:
    """TTL por volatilidade — valores vindos de ``Settings`` na composição (presentation/DI)."""

    cadastral: int
    qualificacao: int
    situacao: int


def _expiries(ttl: CnpjTtlSegundos, consultado_em: datetime) -> tuple[datetime, datetime, datetime]:
    if consultado_em.tzinfo is None:
        consultado_em = consultado_em.replace(tzinfo=UTC)
    return (
        consultado_em + timedelta(seconds=int(ttl.cadastral)),
        consultado_em + timedelta(seconds=int(ttl.qualificacao)),
        consultado_em + timedelta(seconds=int(ttl.situacao)),
    )


@dataclass(frozen=True)
class ConsultaCnpjMaterializada:
    """Resultado persistido (ou reutilizado por idempotência) para merge/resposta HTTP."""

    consulta_id: UUID
    cnpj_14: str
    payload_bruto: dict[str, Any]
    payload_canonico: dict[str, Any]
    fonte: str
    expira_cadastral_at: datetime
    expira_qualificacao_at: datetime
    expira_situacao_at: datetime


class CnpjConsultaService:
    """Coordena cache TTL, chamadas externas e INSERT em ``cnpj_consultas``."""

    def __init__(
        self,
        repo: CnpjConsultaRepositoryPort,
        provedor: CnpjProvedorExternoPort,
        ttl_segundos: CnpjTtlSegundos,
    ) -> None:
        self._repo = repo
        self._provedor = provedor
        self._ttl = ttl_segundos

    def _row_materializada(self, row: dict[str, Any]) -> ConsultaCnpjMaterializada:
        return ConsultaCnpjMaterializada(
            consulta_id=UUID(str(row["id"])),
            cnpj_14=str(row["cnpj"]),
            payload_bruto=_as_dict_jsonb(row.get("payload_bruto")),
            payload_canonico=_as_dict_jsonb(row.get("payload_canonico")),
            fonte=str(row["fonte"]),
            expira_cadastral_at=row["expira_cadastral_at"],
            expira_qualificacao_at=row["expira_qualificacao_at"],
            expira_situacao_at=row["expira_situacao_at"],
        )

    async def materializar_consulta(
        self,
        *,
        tenant_id: UUID,
        cnpj_14: str,
        idempotency_key: str,
        force_refresh: bool,
        diagnostico_id: UUID | None,
        trace_id: str | None,
    ) -> ConsultaCnpjMaterializada:
        """
        Garante linha em ``cnpj_consultas`` para a chave idempotente ou reutiliza a existente.

        ``force_refresh`` ignora cache TTL e força nova chamada externa.
        """
        existente = self._repo.buscar_por_idempotencia(tenant_id, idempotency_key)
        if existente:
            return self._row_materializada(existente)

        consultado_em = datetime.now(UTC)
        payload_bruto: dict[str, Any]
        fonte: str
        lat_ms: int | None
        http_st: int | None

        if not force_refresh:
            cached = self._repo.buscar_ultimo_cache_valido_triplo_ttl(tenant_id, cnpj_14)
            if cached is not None:
                payload_bruto = _as_dict_jsonb(cached.get("payload_bruto"))
                canon = _as_dict_jsonb(cached.get("payload_canonico"))
                fonte = str(cached["fonte"])
                lat_ms = None
                http_st = None
                consultado_em = datetime.now(UTC)
                exp_c, exp_q, exp_s = _expiries(self._ttl, consultado_em)
                h = _hash_canonico(canon)
                new_id = self._repo.inserir_consulta(
                    tenant_id=tenant_id,
                    idempotency_key=idempotency_key,
                    cnpj=cnpj_14,
                    diagnostico_id=diagnostico_id,
                    payload_bruto=payload_bruto,
                    payload_canonico=canon,
                    payload_hash=h,
                    fonte=fonte,
                    consultado_em=consultado_em,
                    expira_cadastral_at=exp_c,
                    expira_qualificacao_at=exp_q,
                    expira_situacao_at=exp_s,
                    latencia_ms=lat_ms,
                    http_status=http_st,
                    trace_id=trace_id,
                )
                return ConsultaCnpjMaterializada(
                    consulta_id=new_id,
                    cnpj_14=cnpj_14,
                    payload_bruto=payload_bruto,
                    payload_canonico=canon,
                    fonte=fonte,
                    expira_cadastral_at=exp_c,
                    expira_qualificacao_at=exp_q,
                    expira_situacao_at=exp_s,
                )

        payload_bruto, fonte, http_st, lat_ms = await self._provedor.buscar_cnpj(cnpj_14)
        canon = sugestao_desde_payload_receita(payload_bruto)
        if canon.get("cnpj") != cnpj_14:
            canon["cnpj"] = cnpj_14
        h = _hash_canonico(canon)
        exp_c, exp_q, exp_s = _expiries(self._ttl, consultado_em)
        new_id = self._repo.inserir_consulta(
            tenant_id=tenant_id,
            idempotency_key=idempotency_key,
            cnpj=cnpj_14,
            diagnostico_id=diagnostico_id,
            payload_bruto=payload_bruto,
            payload_canonico=canon,
            payload_hash=h,
            fonte=fonte,
            consultado_em=consultado_em,
            expira_cadastral_at=exp_c,
            expira_qualificacao_at=exp_q,
            expira_situacao_at=exp_s,
            latencia_ms=lat_ms,
            http_status=http_st,
            trace_id=trace_id,
        )
        return ConsultaCnpjMaterializada(
            consulta_id=new_id,
            cnpj_14=cnpj_14,
            payload_bruto=payload_bruto,
            payload_canonico=canon,
            fonte=fonte,
            expira_cadastral_at=exp_c,
            expira_qualificacao_at=exp_q,
            expira_situacao_at=exp_s,
        )
