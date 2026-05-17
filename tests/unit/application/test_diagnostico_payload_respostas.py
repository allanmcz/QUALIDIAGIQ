"""Testes de extração de respostas do payload JSON (backfill)."""

from __future__ import annotations

import pytest

from src.application.services.diagnostico_payload_respostas import entradas_resposta_de_payload_dict


class TestEntradasRespostaDePayloadDict:
    """Valida mapeamento mínimo para backfill."""

    def test_rejeita_payload_sem_respostas(self) -> None:
        with pytest.raises(ValueError, match="sem lista respostas"):
            entradas_resposta_de_payload_dict({"empresa": {}})

    def test_rejeita_pergunta_inexistente(self) -> None:
        payload = {"respostas": [{"pergunta_id": "00000000-0000-0000-0000-000000000099", "valor": 1}]}
        with pytest.raises(ValueError, match="não encontrada"):
            entradas_resposta_de_payload_dict(payload)
