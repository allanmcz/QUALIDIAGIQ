"""Testes do caso de uso CompararQuestionarioDiagnosticos."""

from __future__ import annotations

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.use_cases.comparar_questionario_diagnosticos import (
    ComandoCompararQuestionario,
    CompararQuestionarioDiagnosticos,
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


def _diag(did, tenant_id, cnpj: str = "11222333000181") -> Diagnostico:
    return Diagnostico(
        id=did,
        tenant_id=tenant_id,
        empresa=EmpresaInfo(
            cnpj=cnpj,
            razao_social="Teste SA",
            porte=PorteEmpresa.MEDIO,
            regime=RegimeTributario.LUCRO_REAL,
            cnae_principal="6201500",
            uf="SP",
            setor_macro=SetorMacro.SERVICOS,
        ),
        respondente=Respondente(email="t@t.com", nome="T"),
        plano=PlanoDiagnostico.GRATUITO,
        status=StatusDiagnostico.FINALIZADO,
        score_geral=60.0,
    )


@pytest.mark.asyncio
async def test_comparar_alinha_por_codigo() -> None:
    tid = uuid4()
    d1, d2 = uuid4(), uuid4()
    repo = AsyncMock()
    repo.buscar_por_id = AsyncMock(side_effect=lambda did, t: _diag(did, t) if t == tid else None)
    repo.listar_respostas_questionario = AsyncMock(
        side_effect=lambda did, t: (
            [
                {
                    "pergunta_codigo": "Q-A-001",
                    "texto_pergunta": "P1",
                    "dimensao": "fiscal",
                    "valor_exibicao": "Sim",
                    "pontuacao_item": 100.0,
                    "excluida_calculo": False,
                    "ordem_exibicao": 0,
                    "base_legal": None,
                }
            ]
            if did == d1
            else [
                {
                    "pergunta_codigo": "Q-A-001",
                    "texto_pergunta": "P1",
                    "dimensao": "fiscal",
                    "valor_exibicao": "Não",
                    "pontuacao_item": 0.0,
                    "excluida_calculo": False,
                    "ordem_exibicao": 0,
                    "base_legal": None,
                }
            ]
        )
    )
    uc = CompararQuestionarioDiagnosticos(repo)
    out = await uc.execute(ComandoCompararQuestionario(tenant_id=tid, diagnostico_ids=(d1, d2)))
    assert len(out["linhas"]) == 1
    vals = out["linhas"][0]["valores_por_diagnostico"]
    assert vals[str(d1)]["valor_exibicao"] == "Sim"
    assert vals[str(d2)]["valor_exibicao"] == "Não"


@pytest.mark.asyncio
async def test_comparar_rejeita_cnpj_diferente() -> None:
    tid = uuid4()
    d1, d2 = uuid4(), uuid4()
    repo = AsyncMock()

    async def _buscar(did, t):
        cnpj = "11111111000191" if did == d2 else "11222333000181"
        return _diag(did, t, cnpj)

    repo.buscar_por_id = _buscar
    repo.listar_respostas_questionario = AsyncMock(return_value=[])
    uc = CompararQuestionarioDiagnosticos(repo)
    with pytest.raises(ValueError, match="mesma empresa"):
        await uc.execute(ComandoCompararQuestionario(tenant_id=tid, diagnostico_ids=(d1, d2)))
