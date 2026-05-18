"""
Refazer questionário no mesmo ciclo (painel — plano avançado).

Camada: Application

Persiste novo score via retificação append-only (ADR-012) e novo lote de respostas
materializadas; a linha WORM do diagnóstico original mantém o hash de evidência inicial.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from src.application.constants.refazer_questionario import (
    MOTIVO_REFAZER_QUESTIONARIO_PAINEL,
    PAYLOAD_TIPO_REFAZER_QUESTIONARIO,
)
from src.application.dto.entrada_resposta_diagnostico import EntradaRespostaDiagnostico
from src.application.services.diagnostico_resposta_materializacao import derivar_respostas_e_linhas
from src.application.use_cases.registrar_retificacao_diagnostico import (
    ComandoRegistrarRetificacaoDiagnostico,
    RegistrarRetificacaoDiagnostico,
)
from src.domain.entities.diagnostico import PlanoDiagnostico, StatusDiagnostico


@dataclass(frozen=True)
class ComandoRefazerQuestionarioDiagnostico:
    """Entrada — mesmo conjunto de respostas que um POST novo, mas no ciclo existente."""

    tenant_id: UUID
    actor_user_id: UUID
    diagnostico_id: UUID
    entradas_resposta: list[EntradaRespostaDiagnostico]
    aceite_termos_privacidade: bool


@dataclass(frozen=True)
class ResultadoRefazerQuestionarioDiagnostico:
    """Saída — score recalculado e registo de retificação."""

    diagnostico_id: UUID
    retificacao_id: UUID
    score_geral: float
    refazer_lote: int


if TYPE_CHECKING:
    from uuid import UUID

    from src.application.use_cases.calcular_score_use_case import CalcularScoreUseCase
    from src.domain.repositories.diagnostico_repository import DiagnosticoRepository


class RefazerQuestionarioDiagnostico:
    """Recalcula score e grava evidência em cadeia sem criar novo diagnostico_id."""

    def __init__(
        self,
        *,
        diagnostico_repository: DiagnosticoRepository,
        calcular_score_use_case: CalcularScoreUseCase,
        registrar_retificacao: RegistrarRetificacaoDiagnostico,
    ) -> None:
        self._repo = diagnostico_repository
        self._calcular = calcular_score_use_case
        self._registrar_retificacao = registrar_retificacao

    async def execute(
        self, comando: ComandoRefazerQuestionarioDiagnostico
    ) -> ResultadoRefazerQuestionarioDiagnostico:
        if not comando.aceite_termos_privacidade:
            raise ValueError(
                "É obrigatório declarar aceite dos termos de uso e da política de privacidade (LGPD)."
            )

        diagnostico = await self._repo.buscar_por_id(comando.diagnostico_id, comando.tenant_id)
        if diagnostico is None:
            raise ValueError("Diagnóstico não encontrado.")
        if diagnostico.status != StatusDiagnostico.FINALIZADO:
            raise ValueError("Só é possível refazer o questionário de um ciclo já finalizado.")
        if diagnostico.plano != PlanoDiagnostico.AVANCADO:
            raise ValueError(
                "Refazer questionário no mesmo ciclo exige plano avançado. "
                "Use um novo ciclo de diagnóstico para outra leitura."
            )

        perguntas_aplicadas = [e.pergunta for e in comando.entradas_resposta]
        respostas, linhas = derivar_respostas_e_linhas(diagnostico.id, comando.entradas_resposta)

        score_completo = self._calcular.execute(
            perguntas=perguntas_aplicadas,
            respostas=list(respostas),
            data_referencia_normativa=datetime.now(UTC).date(),
        )
        score_geral = float(score_completo.score_geral.valor)

        refazer_lote = await self._repo.proximo_refazer_lote_respostas(
            diagnostico.id, comando.tenant_id
        )

        payload_retificacao: dict[str, Any] = {
            "tipo": PAYLOAD_TIPO_REFAZER_QUESTIONARIO,
            "refazer_lote": refazer_lote,
            "score_geral": score_geral,
            "score_completo": score_completo.para_dict_serializavel(),
            "total_respostas": len(comando.entradas_resposta),
        }

        registo = await self._registrar_retificacao.execute(
            ComandoRegistrarRetificacaoDiagnostico(
                tenant_id=comando.tenant_id,
                actor_user_id=comando.actor_user_id,
                diagnostico_original_id=diagnostico.id,
                motivo_retificacao=MOTIVO_REFAZER_QUESTIONARIO_PAINEL,
                payload_retificacao=payload_retificacao,
            )
        )

        await self._repo.inserir_respostas_questionario_refazer(
            diagnostico.id,
            comando.tenant_id,
            linhas,
            refazer_lote=refazer_lote,
        )
        await self._repo.limpar_explicacao_score_llm(diagnostico.id, comando.tenant_id)

        return ResultadoRefazerQuestionarioDiagnostico(
            diagnostico_id=diagnostico.id,
            retificacao_id=registo.id,
            score_geral=score_geral,
            refazer_lote=refazer_lote,
        )
