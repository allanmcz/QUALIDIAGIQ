"""
Guardrails de entrada/saída para tarefas normativas (RAG) e relatório executivo.

Camada: Infrastructure
Regras (ADR-022): RAG sem evidência ou saída sem citação de dispositivo bloqueiam;
``RELATORIO_EXECUTIVO`` exige ``contexto_executivo`` não vazio na entrada.
"""

from __future__ import annotations

from src.domain.ports.llm_gateway import LlmGatewayRequest, LlmGatewayResponse
from src.domain.value_objects.llm_task_type import LlmTaskType


class RagGuardrailService:
    """Validações complementares à ``RoutingPolicy``."""

    def validate_input(self, request: LlmGatewayRequest) -> str | None:
        """
        Retorna motivo de bloqueio ou ``None`` se permitido.

        Duplica a verificação de evidências para RAG — defesa em profundidade.
        """
        if request.task_type == LlmTaskType.ANALISE_NORMATIVA_RAG and not request.evidencias:
            return "rag_sem_evidencias"
        if (
            request.task_type == LlmTaskType.RELATORIO_EXECUTIVO
            and not str(request.input_data.get("contexto_executivo", "")).strip()
        ):
            return "contexto_executivo_obrigatorio"
        return None

    def validate_output(
        self, request: LlmGatewayRequest, response: LlmGatewayResponse
    ) -> str | None:
        """
        Valida saída para tarefas normativas: exige menção aos dispositivos das evidências.
        """
        if response.blocked_by_guardrail:
            return None
        if request.task_type != LlmTaskType.ANALISE_NORMATIVA_RAG:
            return None
        if not request.evidencias:
            return "rag_sem_evidencias"
        texto = response.text.casefold()
        for ev in request.evidencias:
            if ev.dispositivo.strip().casefold() not in texto:
                return "rag_saida_sem_citacao_dispositivo"
        return None
