"""
Cálculo de hash canónico para registo de retificação (ADR-012 §5 — append-only).

Camada: Domain
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID


def montar_canonical_retificacao(
    *,
    tenant_id: UUID,
    diagnostico_original_id: UUID,
    hash_diagnostico_original_sha256: str,
    motivo_retificacao: str,
    payload_retificacao: dict[str, Any],
    retificacao_id: UUID,
    criado_em: datetime,
    actor_user_id: UUID | None,
) -> dict[str, Any]:
    """Monta o dicionário canónico antes do SHA-256 (ordenado, UTF-8)."""
    iso = criado_em.astimezone(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "tipo": "RETIFICACAO",
        "schema_retificacao": "qdi-retificacao-v1",
        "referencia_diagnostico_original": hash_diagnostico_original_sha256.strip().lower(),
        "motivo_retificacao": motivo_retificacao.strip(),
        "payload_retificacao": payload_retificacao,
        "diagnostico_original_id": str(diagnostico_original_id),
        "tenant_id": str(tenant_id),
        "retificacao_id": str(retificacao_id),
        "criado_em": iso,
        "actor_user_id": str(actor_user_id) if actor_user_id else None,
    }


def calcular_hash_retificacao_sha256(payload_canonico: dict[str, Any]) -> str:
    """SHA-256 hex (64 chars) do JSON canónico."""
    raw = json.dumps(payload_canonico, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()
