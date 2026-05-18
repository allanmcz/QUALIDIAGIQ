"""Testes do use case RefazerQuestionarioDiagnostico."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.dto.entrada_resposta_diagnostico import EntradaRespostaDiagnostico
from src.application.ports.diagnostico_retificacao_port import DiagnosticoRetificacaoRegisto
from src.application.use_cases.refazer_questionario_diagnostico import (
    ComandoRefazerQuestionarioDiagnostico,
    RefazerQuestionarioDiagnostico,
)
from src.domain.entities.questionario import TipoPergunta
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
from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico


def _diagnostico_finalizado_avancado() -> Diagnostico:
    d = Diagnostico(
        tenant_id=uuid4(),
        empresa=EmpresaInfo(
            cnpj="11222333000181",
            razao_social="Empresa Teste",
            porte=PorteEmpresa.MEDIO,
            regime=RegimeTributario.LUCRO_PRESUMIDO,
            cnae_principal="6201500",
            uf="SP",
            setor_macro=SetorMacro.SERVICOS,
        ),
        respondente=Respondente(email="a@b.com"),
        plano=PlanoDiagnostico.AVANCADO,
        status=StatusDiagnostico.FINALIZADO,
    )
    d.hash_evidencia = "a" * 64
    return d


class TestRefazerQuestionarioDiagnostico:
    """Refazer no mesmo ciclo — retificação + lote de respostas."""

    @pytest.mark.asyncio
    async def test_rejeita_plano_gratuito(self) -> None:
        repo = AsyncMock()
        d = _diagnostico_finalizado_avancado()
        d.plano = PlanoDiagnostico.GRATUITO
        repo.buscar_por_id.return_value = d
        uc = RefazerQuestionarioDiagnostico(
            diagnostico_repository=repo,
            calcular_score_use_case=MagicMock(),
            registrar_retificacao=AsyncMock(),
        )
        with pytest.raises(ValueError, match="plano avançado"):
            await uc.execute(
                ComandoRefazerQuestionarioDiagnostico(
                    tenant_id=d.tenant_id,
                    actor_user_id=uuid4(),
                    diagnostico_id=d.id,
                    entradas_resposta=[],
                    aceite_termos_privacidade=True,
                )
            )

    @pytest.mark.asyncio
    async def test_executa_com_retificacao_e_lote(self) -> None:
        d = _diagnostico_finalizado_avancado()
        pergunta = MagicMock()
        pergunta.id = uuid4()
        pergunta.tipo = TipoPergunta.BINARIA
        pergunta.codigo = "Q-FIS-001"
        pergunta.texto = "Pergunta teste"
        pergunta.dimensao = Dimensao.FISCAL
        pergunta.peso = 5.0
        pergunta.base_legal = "LC 214/2025"
        pergunta.pilar_abnt = None
        pergunta.multipla_total = None
        entrada = EntradaRespostaDiagnostico(pergunta=pergunta, valor_bruto="sim")

        score_mock = ScoreCompleto(
            score_geral=ScoreNumerico(valor=72.5, peso_total_aplicado=10.0),
            score_por_dimensao={
                Dimensao.FISCAL: ScoreNumerico(valor=70.0, peso_total_aplicado=5.0),
            },
        )
        calcular = MagicMock()
        calcular.execute.return_value = score_mock

        ret_id = uuid4()
        registrar = AsyncMock()
        registrar.execute.return_value = DiagnosticoRetificacaoRegisto(
            id=ret_id,
            tenant_id=d.tenant_id,
            diagnostico_original_id=d.id,
            hash_diagnostico_original_sha256=d.hash_evidencia or "",
            motivo_retificacao="Refazer questionário (painel)",
            payload_retificacao={},
            hash_retificacao_sha256="b" * 64,
            actor_user_id=uuid4(),
            criado_em=datetime.now(UTC),
        )

        repo = AsyncMock()
        repo.buscar_por_id.return_value = d
        repo.proximo_refazer_lote_respostas.return_value = 2

        uc = RefazerQuestionarioDiagnostico(
            diagnostico_repository=repo,
            calcular_score_use_case=calcular,
            registrar_retificacao=registrar,
        )
        resultado = await uc.execute(
            ComandoRefazerQuestionarioDiagnostico(
                tenant_id=d.tenant_id,
                actor_user_id=uuid4(),
                diagnostico_id=d.id,
                entradas_resposta=[entrada],
                aceite_termos_privacidade=True,
            )
        )

        assert resultado.score_geral == 72.5
        assert resultado.refazer_lote == 2
        assert resultado.retificacao_id == ret_id
        repo.inserir_respostas_questionario_refazer.assert_awaited_once()
        repo.limpar_explicacao_score_llm.assert_awaited_once()
