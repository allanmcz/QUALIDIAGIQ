"""Testes do hash canónico SHA-256 de comentários Kanban."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from src.application.services.plano_acao_comentario_hash import (
    calcular_sha256_payload_comentario,
    montar_payload_hash_comentario,
)

PID = UUID("11111111-1111-1111-1111-111111111111")
DID = UUID("22222222-2222-2222-2222-222222222222")
TID = UUID("33333333-3333-3333-3333-333333333333")
UID = UUID("44444444-4444-4444-4444-444444444444")
CRIADO = datetime(2026, 5, 16, 12, 0, 0, tzinfo=UTC)


class TestPlanoAcaoComentarioHash:
    """Hash determinístico para evidência WORM."""

    def test_hash_estavel_para_mesmo_payload(self) -> None:
        payload = montar_payload_hash_comentario(
            plano_acao_id=PID,
            diagnostico_id=DID,
            tenant_id=TID,
            autor_label="Consultor",
            autor_email="c@teste.com",
            autor_user_id=UID,
            comentario="Texto auditável",
            criado_em=CRIADO,
        )
        h1 = calcular_sha256_payload_comentario(payload)
        h2 = calcular_sha256_payload_comentario(payload)
        assert h1 == h2
        assert len(h1) == 64
        assert all(c in "0123456789abcdef" for c in h1)

    def test_hash_muda_quando_comentario_muda(self) -> None:
        base = {
            "plano_acao_id": PID,
            "diagnostico_id": DID,
            "tenant_id": TID,
            "autor_label": "Consultor",
            "autor_email": None,
            "autor_user_id": None,
            "criado_em": CRIADO,
        }
        p1 = montar_payload_hash_comentario(**base, comentario="A")
        p2 = montar_payload_hash_comentario(**base, comentario="B")
        assert calcular_sha256_payload_comentario(p1) != calcular_sha256_payload_comentario(p2)
