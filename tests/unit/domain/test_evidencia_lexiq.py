"""Testes de ``EvidenciaLexiq`` (recusa controlada)."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

import pytest

from src.domain.value_objects.evidencia_lexiq import EvidenciaLexiq


class TestEvidenciaLexiq:
    def test_aceita_curadoria_com_score_pleno(self) -> None:
        e = EvidenciaLexiq(
            norma="LC 214/2025",
            dispositivo="art. 5º",
            versao="v1",
            vigencia_inicio=date(2026, 1, 1),
            vigencia_fim=None,
            chunk_id=uuid4(),
            citacao_texto="Previsibilidade ao contribuinte.",
            score_similaridade=1.0,
        )
        assert e.score_similaridade == 1.0

    def test_rejeita_score_baixo(self) -> None:
        with pytest.raises(ValueError, match="limiar"):
            EvidenciaLexiq(
                norma="X",
                dispositivo="Y",
                versao="v1",
                vigencia_inicio=date(2026, 1, 1),
                vigencia_fim=None,
                chunk_id=uuid4(),
                citacao_texto="Z",
                score_similaridade=0.1,
            )

    def test_rejeita_citacao_vazia(self) -> None:
        with pytest.raises(ValueError, match="citacao_texto"):
            EvidenciaLexiq(
                norma="X",
                dispositivo="Y",
                versao="v1",
                vigencia_inicio=date(2026, 1, 1),
                vigencia_fim=None,
                chunk_id=uuid4(),
                citacao_texto="",
                score_similaridade=0.7,
            )
