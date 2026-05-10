"""Testes de montagem do payload de export portável v1 (domain — ADR-012 §4)."""

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


@pytest.fixture
def _empresa() -> EmpresaInfo:
    return EmpresaInfo(
        cnpj="12345678000195",
        razao_social="Export Test LTDA",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )


@pytest.fixture
def _respondente() -> Respondente:
    return Respondente(email="titular@example.com", nome="Titular QA")


class TestMontarPayloadExportV1:
    """Campos de contrato e bloqueios de export (validador em teste de infra)."""

    def test_schema_id_version_e_passa_json_schema(
        self, _empresa: EmpresaInfo, _respondente: Respondente
    ) -> None:
        diag = Diagnostico(
            tenant_id=uuid.UUID("22222222-3333-4444-5555-666666666666"),
            empresa=_empresa,
            respondente=_respondente,
            id=uuid.UUID("77777777-8888-9999-aaaa-bbbbbbbbbbbb"),
        )
        sc = ScoreCompleto(
            score_geral=ScoreNumerico(valor=70.0, peso_total_aplicado=10.0),
            score_por_dimensao={
                Dimensao.FISCAL: ScoreNumerico(valor=70.0, peso_total_aplicado=10.0),
            },
        )
        diag.finalizar_e_registrar_evidencia(sc)
        fix_ts = datetime(2026, 5, 9, 10, 0, 0, tzinfo=UTC)
        payload = montar_payload_export_v1(diag, exportado_em=fix_ts)

        assert payload["schema_id"] == "qdi-diagnostico-export-v1"
        assert payload["schema_version"] == "1.0.0"
        assert payload["diagnostico_id"] == str(diag.id)
        assert payload["tenant_id"] == str(diag.tenant_id)
        assert payload["hash_evidencia_sha256"] == diag.hash_evidencia
        assert payload["bloqueios_export"]["apenas_finalizado_com_evidencia"] is True

    def test_respondente_ip_origem_no_export(
        self, _empresa: EmpresaInfo, _respondente: Respondente
    ) -> None:
        resp = Respondente(
            email=_respondente.email,
            nome=_respondente.nome,
            ip_origem="203.0.113.10",
        )
        diag = Diagnostico(
            tenant_id=uuid.UUID("22222222-3333-4444-5555-666666666666"),
            empresa=_empresa,
            respondente=resp,
            id=uuid.UUID("77777777-8888-9999-aaaa-bbbbbbbbbbbb"),
        )
        sc = ScoreCompleto(
            score_geral=ScoreNumerico(valor=70.0, peso_total_aplicado=10.0),
            score_por_dimensao={
                Dimensao.FISCAL: ScoreNumerico(valor=70.0, peso_total_aplicado=10.0),
            },
        )
        diag.finalizar_e_registrar_evidencia(sc)
        payload = montar_payload_export_v1(
            diag, exportado_em=datetime(2026, 5, 9, 10, 0, 0, tzinfo=UTC)
        )
        assert payload["respondente"]["ip_origem"] == "203.0.113.10"

    def test_score_completo_snapshot_ausente_serializa_null(
        self, _empresa: EmpresaInfo, _respondente: Respondente
    ) -> None:
        diag = Diagnostico(
            tenant_id=uuid.UUID("22222222-3333-4444-5555-666666666666"),
            empresa=_empresa,
            respondente=_respondente,
            id=uuid.UUID("77777777-8888-9999-aaaa-bbbbbbbbbbbb"),
        )
        sc = ScoreCompleto(
            score_geral=ScoreNumerico(valor=70.0, peso_total_aplicado=10.0),
            score_por_dimensao={
                Dimensao.FISCAL: ScoreNumerico(valor=70.0, peso_total_aplicado=10.0),
            },
        )
        diag.finalizar_e_registrar_evidencia(sc)
        diag.score_completo_snapshot = None  # ramo coverage: export sem snapshot congelado
        fix_ts = datetime(2026, 5, 9, 10, 0, 0, tzinfo=UTC)
        payload = montar_payload_export_v1(diag, exportado_em=fix_ts)
        assert payload["score_completo"] is None
