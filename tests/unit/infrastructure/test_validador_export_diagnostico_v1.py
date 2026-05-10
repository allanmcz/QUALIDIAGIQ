"""Validação JSON Schema do pacote de export (infraestrutura)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)
from src.domain.services.diagnostico_export_v1 import montar_payload_export_v1
from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico
from src.infrastructure.exportacao.validador_export_diagnostico_v1 import (
    validar_payload_export_diagnostico_v1,
)


@pytest.fixture
def _empresa() -> EmpresaInfo:
    return EmpresaInfo(
        cnpj="12345678000195",
        razao_social="Schema LTDA",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )


class TestValidadorExportDiagnosticoV1:
    """Garante que o payload de domínio cumpre ``qdi-diagnostico-export-v1``."""

    def test_payload_montado_passa_validador(self, _empresa: EmpresaInfo) -> None:
        diag = Diagnostico(
            tenant_id=uuid.uuid4(),
            empresa=_empresa,
            respondente=Respondente(email="a@b.com"),
        )
        sc = ScoreCompleto(
            score_geral=ScoreNumerico(valor=55.0, peso_total_aplicado=10.0),
            score_por_dimensao={
                Dimensao.CONTABIL: ScoreNumerico(valor=55.0, peso_total_aplicado=10.0),
            },
        )
        diag.finalizar_e_registrar_evidencia(sc)
        payload = montar_payload_export_v1(
            diag, exportado_em=datetime(2026, 5, 9, 8, 0, 0, tzinfo=UTC)
        )
        validar_payload_export_diagnostico_v1(payload)

    def test_payload_invalido_levanta_validation_error(self) -> None:
        import jsonschema

        with pytest.raises(jsonschema.ValidationError):
            validar_payload_export_diagnostico_v1({"schema_id": "nao-e-o-export-v1"})
