"""
Hash SHA-256 canónico para comentários WORM do Kanban do plano.

Camada: Application (serviço puro — sem I/O)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID


def montar_payload_hash_comentario(
    *,
    plano_acao_id: UUID,
    diagnostico_id: UUID,
    tenant_id: UUID,
    autor_label: str,
    autor_email: str | None,
    autor_user_id: UUID | None,
    comentario: str,
    criado_em: datetime,
) -> dict[str, Any]:
    """Monta o dicionário com chaves estáveis para serialização JSON."""
    return {
        "plano_acao_id": str(plano_acao_id),
        "diagnostico_id": str(diagnostico_id),
        "tenant_id": str(tenant_id),
        "autor_label": autor_label,
        "autor_email": autor_email,
        "autor_user_id": str(autor_user_id) if autor_user_id is not None else None,
        "comentario": comentario,
        "criado_em": criado_em.isoformat(),
    }


def calcular_sha256_payload_comentario(payload: dict[str, Any]) -> str:
    """JSON ordenado + separadores fixos → SHA-256 hex (64 chars)."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
