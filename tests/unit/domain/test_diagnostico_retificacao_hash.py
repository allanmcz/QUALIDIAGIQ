"""Testes do canónico + SHA-256 de retificação (domain — ADR-012 §5)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from src.domain.services.diagnostico_retificacao_hash import (
    calcular_hash_retificacao_sha256,
    montar_canonical_retificacao,
)


class TestDiagnosticoRetificacaoHash:
    """Invariantes da cadeia auditável (NF-e / CC-e mental model)."""

    def test_hash_deterministic_para_payload_fixo(self) -> None:
        """Mesmo canónico ⇒ mesmo SHA-256 hex (64 chars)."""
        tid = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")
        did = uuid.UUID("11111111-2222-3333-4444-555555555555")
        rid = uuid.UUID("66666666-7777-8888-9999-aaaaaaaaaaaa")
        uid = uuid.UUID("bbbbbbbb-cccc-dddd-eeee-ffffffffffff")
        ts = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)
        canon = montar_canonical_retificacao(
            tenant_id=tid,
            diagnostico_original_id=did,
            hash_diagnostico_original_sha256="ab" * 32,
            motivo_retificacao="  Ajuste documental após revisão interna.  ",
            payload_retificacao={"campo": "x"},
            retificacao_id=rid,
            criado_em=ts,
            actor_user_id=uid,
        )
        h1 = calcular_hash_retificacao_sha256(canon)
        h2 = calcular_hash_retificacao_sha256(canon)
        assert h1 == h2
        assert len(h1) == 64
        assert h1 == h1.lower()

    def test_referencia_diagnostico_original_normalizada_minusculas(self) -> None:
        """Hash do original no JSON canónico deve estar lower-case."""
        tid = uuid.uuid4()
        did = uuid.uuid4()
        rid = uuid.uuid4()
        ts = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
        upper_hash = "AA" * 32
        canon = montar_canonical_retificacao(
            tenant_id=tid,
            diagnostico_original_id=did,
            hash_diagnostico_original_sha256=upper_hash,
            motivo_retificacao="motivo",
            payload_retificacao={},
            retificacao_id=rid,
            criado_em=ts,
            actor_user_id=None,
        )
        assert canon["referencia_diagnostico_original"] == upper_hash.lower()

    def test_payload_vazio_actor_none_serializa(self) -> None:
        canon = montar_canonical_retificacao(
            tenant_id=uuid.uuid4(),
            diagnostico_original_id=uuid.uuid4(),
            hash_diagnostico_original_sha256="cc" * 32,
            motivo_retificacao="texto mínimo para retificação",
            payload_retificacao={},
            retificacao_id=uuid.uuid4(),
            criado_em=datetime(2026, 5, 9, 15, 30, 0, tzinfo=UTC),
            actor_user_id=None,
        )
        assert canon["actor_user_id"] is None
        h = calcular_hash_retificacao_sha256(canon)
        assert len(h) == 64
