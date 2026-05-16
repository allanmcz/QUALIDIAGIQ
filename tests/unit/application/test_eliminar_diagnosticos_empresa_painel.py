"""Testes do caso de uso EliminarDiagnosticosEmpresaPainel."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from src.application.errors import EliminacaoEmpresaSomenteWormError
from src.application.use_cases.eliminar_diagnosticos_empresa_painel import (
    ComandoEliminarDiagnosticosEmpresaPainel,
    EliminarDiagnosticosEmpresaPainel,
)
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


def _diag(
    *,
    tenant_id: UUID,
    cnpj: str,
    status: StatusDiagnostico,
) -> Diagnostico:
    return Diagnostico(
        id=uuid4(),
        tenant_id=tenant_id,
        empresa=EmpresaInfo(
            cnpj=cnpj,
            razao_social="Empresa Teste SA",
            porte=PorteEmpresa.MEDIO,
            regime=RegimeTributario.LUCRO_REAL,
            cnae_principal="6201500",
            uf="SP",
            setor_macro=SetorMacro.SERVICOS,
        ),
        respondente=Respondente(email="a@b.com", nome="A"),
        plano=PlanoDiagnostico.GRATUITO,
        status=status,
        criado_em=datetime(2026, 5, 1, tzinfo=UTC),
    )


class TestEliminarDiagnosticosEmpresaPainel:
    """Orquestração de exclusão em lote por CNPJ."""

    @pytest.mark.asyncio
    async def test_elimina_apenas_nao_finalizados(self) -> None:
        tenant = uuid4()
        cnpj = "11222333000181"
        repo = CiPlaywrightDiagnosticoRepository()
        em_andamento = _diag(tenant_id=tenant, cnpj=cnpj, status=StatusDiagnostico.EM_ANDAMENTO)
        finalizado = _diag(tenant_id=tenant, cnpj=cnpj, status=StatusDiagnostico.FINALIZADO)
        await repo.salvar(em_andamento)
        await repo.salvar(finalizado)

        uc = EliminarDiagnosticosEmpresaPainel(repo=repo)
        out = await uc.execute(
            ComandoEliminarDiagnosticosEmpresaPainel(
                tenant_id=tenant,
                actor_user_id=uuid4(),
                empresa_cnpj=cnpj,
            )
        )
        assert out.total_eliminados == 1
        assert out.mantidos_finalizados == 1
        assert await repo.buscar_por_id(em_andamento.id, tenant) is None
        assert await repo.buscar_por_id(finalizado.id, tenant) is not None

    @pytest.mark.asyncio
    async def test_rejeita_quando_somente_finalizados(self) -> None:
        tenant = uuid4()
        cnpj = "11222333000181"
        repo = CiPlaywrightDiagnosticoRepository()
        d = _diag(tenant_id=tenant, cnpj=cnpj, status=StatusDiagnostico.FINALIZADO)
        await repo.salvar(d)
        uc = EliminarDiagnosticosEmpresaPainel(repo=repo)
        with pytest.raises(EliminacaoEmpresaSomenteWormError):
            await uc.execute(
                ComandoEliminarDiagnosticosEmpresaPainel(
                    tenant_id=tenant,
                    actor_user_id=uuid4(),
                    empresa_cnpj=cnpj,
                )
            )
