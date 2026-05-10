"""Referência operacional LGPD (SLA) — espelho da decisão J3 DEV_09052026_V2."""

from src.application.services.privacidade_operacao import LGPD_PRAZO_RESPOSTA_ART18_DIAS_UTEIS


def test_prazo_resposta_art18_baseline() -> None:
    assert LGPD_PRAZO_RESPOSTA_ART18_DIAS_UTEIS == 15
