"""
Implementação do port ``LlmGateway`` — router convergente (ADR-022).

Camada: Infrastructure
Orquestra política, guardrails e completer (``FakeLlmAdapter`` ou ``LlmServiceGatewayCompleter``).
"""

from __future__ import annotations

import time

import structlog

from src.application.ports.llm_service import LlmServicePort
from src.domain.ports.llm_gateway import LlmGateway, LlmGatewayRequest, LlmGatewayResponse
from src.infrastructure.config.settings import Settings
from src.infrastructure.llm.adapters.fake_llm_adapter import FakeLlmAdapter
from src.infrastructure.llm.adapters.llm_service_gateway_completer import LlmServiceGatewayCompleter
from src.infrastructure.llm.cost_estimator import CostEstimator
from src.infrastructure.llm.guardrails.rag_guardrail_service import RagGuardrailService
from src.infrastructure.llm.routing_policy import RoutingPolicy
from src.infrastructure.observability.qdi_otel_metrics import record_llm_gateway_completion

logger = structlog.get_logger(__name__)

_Completer = FakeLlmAdapter | LlmServiceGatewayCompleter


def _model_label(settings: Settings) -> str:
    """Identificador legível do modelo activo (sem segredos)."""
    if settings.llm_backend == "openai":
        return settings.openai_chat_model.strip()
    if settings.llm_backend == "anthropic":
        return settings.anthropic_model.strip()
    return settings.ollama_model.strip()


class LlmGatewayRouter(LlmGateway):
    """Router com política determinística, guardrails e adapter fake ou real."""

    def __init__(
        self,
        settings: Settings,
        *,
        policy: RoutingPolicy | None = None,
        guardrails: RagGuardrailService | None = None,
        fake_adapter: FakeLlmAdapter | None = None,
        llm_service: LlmServicePort | None = None,
        cost_estimator: CostEstimator | None = None,
    ) -> None:
        self._settings = settings
        self._policy = policy or RoutingPolicy()
        self._guardrails = guardrails or RagGuardrailService()
        if fake_adapter is not None:
            self._completer: _Completer = fake_adapter
        elif llm_service is not None:
            self._completer = LlmServiceGatewayCompleter(llm_service)
        else:
            self._completer = FakeLlmAdapter()
        self._cost = cost_estimator or CostEstimator()

    def _provider_e_modelo(self) -> tuple[str, str]:
        if isinstance(self._completer, FakeLlmAdapter):
            return "fake", "fake-llm"
        return self._settings.llm_backend.strip(), _model_label(self._settings)

    async def complete(self, request: LlmGatewayRequest) -> LlmGatewayResponse:
        """Executa política → guardrail entrada → (flag) completer → guardrail saída."""
        t0 = time.perf_counter()
        policy_version = (
            self._settings.llm_router_policy_version.strip() or RoutingPolicy.policy_version
        )

        rota = self._policy.select_route(request)
        if rota.blocked:
            record_llm_gateway_completion(
                task_type=str(request.task_type), outcome="blocked_policy"
            )
            logger.info(
                "llm_gateway_bloqueado_politica",
                task_type=str(request.task_type),
                motivo=rota.block_reason,
                policy_version=policy_version,
                trace_id=request.trace_id,
            )
            return LlmGatewayResponse(
                text="",
                provider="none",
                model="none",
                policy_version=policy_version,
                blocked_by_guardrail=True,
                guardrail_reason=rota.block_reason,
                guardrail_status="blocked",
            )

        motivo_in = self._guardrails.validate_input(request)
        if motivo_in is not None:
            record_llm_gateway_completion(
                task_type=str(request.task_type), outcome="blocked_guardrail_input"
            )
            logger.info(
                "llm_gateway_bloqueado_guardrail_entrada",
                task_type=str(request.task_type),
                motivo=motivo_in,
                policy_version=policy_version,
                trace_id=request.trace_id,
            )
            return LlmGatewayResponse(
                text="",
                provider="none",
                model="none",
                policy_version=policy_version,
                blocked_by_guardrail=True,
                guardrail_reason=motivo_in,
                guardrail_status="blocked",
            )

        if not self._settings.llm_router_enabled:
            record_llm_gateway_completion(
                task_type=str(request.task_type), outcome="feature_disabled"
            )
            logger.info(
                "llm_gateway_desligado_flag",
                task_type=str(request.task_type),
                policy_version=policy_version,
                trace_id=request.trace_id,
            )
            return LlmGatewayResponse(
                text="",
                provider="none",
                model="none",
                policy_version=policy_version,
                blocked_by_guardrail=True,
                guardrail_reason="feature_disabled",
                guardrail_status="blocked",
            )

        provider, modelo = self._provider_e_modelo()
        try:
            texto = await self._completer.complete(request)
        except Exception as exc:
            record_llm_gateway_completion(task_type=str(request.task_type), outcome="error")
            logger.error(
                "llm_gateway_adapter_excecao",
                erro=str(exc),
                task_type=str(request.task_type),
                trace_id=request.trace_id,
                exc_info=True,
            )
            return LlmGatewayResponse(
                text="",
                provider=provider,
                model=modelo,
                policy_version=policy_version,
                blocked_by_guardrail=True,
                guardrail_reason="adapter_exception",
                guardrail_status="blocked",
            )

        latency_ms = int((time.perf_counter() - t0) * 1000)
        custo = self._cost.estimate_usd(input_tokens=0, output_tokens=0, model=modelo)

        resp = LlmGatewayResponse(
            text=texto,
            provider=provider,
            model=modelo,
            policy_version=policy_version,
            latency_ms=latency_ms,
            estimated_cost_usd=custo,
            guardrail_status="ok",
        )

        motivo_out = self._guardrails.validate_output(request, resp)
        if motivo_out is not None:
            record_llm_gateway_completion(
                task_type=str(request.task_type), outcome="blocked_guardrail_output"
            )
            logger.info(
                "llm_gateway_bloqueado_guardrail_saida",
                task_type=str(request.task_type),
                motivo=motivo_out,
                policy_version=policy_version,
                trace_id=request.trace_id,
            )
            return LlmGatewayResponse(
                text="",
                provider=resp.provider,
                model=resp.model,
                policy_version=policy_version,
                latency_ms=latency_ms,
                estimated_cost_usd=custo,
                blocked_by_guardrail=True,
                guardrail_reason=motivo_out,
                guardrail_status="blocked",
            )

        record_llm_gateway_completion(task_type=str(request.task_type), outcome="success")
        logger.info(
            "llm_gateway_concluido",
            task_type=str(request.task_type),
            policy_version=policy_version,
            trace_id=request.trace_id,
            tenant_id=request.tenant_id,
            provider=resp.provider,
            model=resp.model,
            latency_ms=latency_ms,
            guardrail_status=resp.guardrail_status,
        )
        return resp
