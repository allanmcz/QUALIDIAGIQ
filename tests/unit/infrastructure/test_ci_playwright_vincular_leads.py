"""Testes de vinculação lead self-service no repositório em memória CI."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PlanoDiagnostico,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
    StatusDiagnostico,
)
from src.infrastructure.repositories.ci_playwright_diagnostico_repository import (
    CiPlaywrightDiagnosticoRepository,
)

_TENANT_SS = UUID("44444444-4444-4444-8444-444444444444")
_TENANT_B2B = UUID("55555555-5555-4555-8555-555555555555")


def _diag_lead(did: UUID, email: str) -> Diagnostico:
    return Diagnostico(
        id=did,
        tenant_id=_TENANT_SS,
        empresa=EmpresaInfo(
            cnpj="",
            razao_social="Lead SA",
            porte=PorteEmpresa.MICRO,
            regime=RegimeTributario.SIMPLES_NACIONAL,
            cnae_principal="1234567",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
        ),
        respondente=Respondente(email=email, nome="Lead"),
        plano=PlanoDiagnostico.GRATUITO,
        status=StatusDiagnostico.FINALIZADO,
        criado_em=datetime(2026, 5, 2, 10, 0, tzinfo=UTC),
        finalizado_em=datetime(2026, 5, 2, 10, 1, tzinfo=UTC),
        score_geral=50.0,
    )


class TestCiPlaywrightVincularLeadsSelfService:
    """Garante que leads OTP (mesmo e-mail) migram para o tenant B2B no dict in-process."""

    @pytest.mark.asyncio
    async def test_vincular_move_gratuito_para_tenant_destino(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        lead_id = uuid4()
        await repo.salvar(_diag_lead(lead_id, "allanmcz@gmail.com"))

        ids = repo.vincular_leads_self_service_em_memoria(
            tenant_self_service=_TENANT_SS,
            tenant_destino=_TENANT_B2B,
            email_admin_normalizado="allanmcz@gmail.com",
        )
        assert lead_id in ids

        moved = await repo.buscar_por_id(lead_id, _TENANT_B2B)
        assert moved is not None
        assert moved.tenant_id == _TENANT_B2B
        assert await repo.buscar_por_id(lead_id, _TENANT_SS) is None

    @pytest.mark.asyncio
    async def test_vincular_ignora_plano_avancado(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        did = uuid4()
        d = _diag_lead(did, "x@y.com")
        d.plano = PlanoDiagnostico.AVANCADO
        await repo.salvar(d)
        ids = repo.vincular_leads_self_service_em_memoria(
            tenant_self_service=_TENANT_SS,
            tenant_destino=_TENANT_B2B,
            email_admin_normalizado="x@y.com",
        )
        assert ids == []
