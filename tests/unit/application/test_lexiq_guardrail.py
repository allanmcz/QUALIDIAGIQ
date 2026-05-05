"""Testes do guardrail mínimo Lexiq (âncoras normativas)."""

from src.application.services.lexiq_guardrail import (
    mensagem_rejeicao_guardrail,
    texto_tem_ancora_normativa,
)


def test_detecta_lc214() -> None:
    assert texto_tem_ancora_normativa("Conforme LC 214/2025 art. 5.") is True


def test_detecta_ec132() -> None:
    assert texto_tem_ancora_normativa("Transição EC 132/2023.") is True


def test_detecta_abnt() -> None:
    assert texto_tem_ancora_normativa("ABNT NBR 17301:2026 cap. 7.") is True


def test_detecta_nt() -> None:
    assert texto_tem_ancora_normativa("Campo NT 2025.002.") is True


def test_detecta_lc227() -> None:
    """LC 227/2026 deve ser âncora válida (P0-03 — lei corrigida no regex)."""
    assert texto_tem_ancora_normativa("Transição LC 227/2026 art. 3.") is True


def test_lc225_nao_e_ancora_valida() -> None:
    """LC 225/2026 não existe como lei formal citável neste contexto — não é âncora válida."""
    assert texto_tem_ancora_normativa("Conforme LC 225/2026.") is False


def test_rejeita_sem_fonte() -> None:
    assert texto_tem_ancora_normativa("Melhore seus processos tributários.") is False


def test_mensagem_rejeicao_nao_vazia() -> None:
    assert "Lexiq" in mensagem_rejeicao_guardrail()
