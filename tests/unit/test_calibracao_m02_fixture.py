"""Validação estrutural do fixture de calibração M02 (sem motor completo)."""

from __future__ import annotations

import json
from pathlib import Path


class TestCalibracaoM02Fixture:
    """Garante que o JSON de casos permanece válido para futura ACT-E04."""

    def test_cinco_casos_com_faixas(self) -> None:
        root = Path(__file__).resolve().parents[1]  # diretório tests/
        path = root / "fixtures/calibracao_m02_casos.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        casos = raw["casos"]
        assert len(casos) == 5
        for c in casos:
            faixa = c["faixa_score_geral_esperada"]
            assert len(faixa) == 2
            lo, hi = float(faixa[0]), float(faixa[1])
            assert 0 <= lo <= hi <= 100
