"""
Completa texto LLM via ``LlmServicePort`` (fábrica ADR-021) a partir de ``LlmGatewayRequest``.

Camada: Infrastructure
**ADR-022 Fase 2:** reutiliza ``gerar_recomendacao`` (prompt canónico + guardrails nos adapters)
sem duplicar SDK — o router convergente governa política e métricas antes/depois.
"""

from __future__ import annotations

from src.application.ports.llm_service import LlmServicePort
from src.domain.ports.llm_gateway import LlmGatewayRequest

_ANCORA_PADRAO = (
    "Âncoras: EC 132/2023; LC 214/2025; ABNT NBR 17301:2026. "
    "Sugira medidas práticas citando dispositivo aplicável quando possível."
)


def _montar_base_normativa(request: LlmGatewayRequest) -> str:
    """Junta evidências citáveis ou texto normativo extra + âncora fixa."""
    if request.evidencias:
        blocos: list[str] = []
        for ev in request.evidencias:
            linha = f"- {ev.dispositivo} | {ev.fonte} | {ev.titulo}"
            if ev.url:
                linha += f" | {ev.url}"
            blocos.append(linha)
        return "\n".join(blocos) + f"\n\n{_ANCORA_PADRAO}"
    extra = request.input_data.get("base_normativa")
    if isinstance(extra, str) and extra.strip():
        return f"{extra.strip()}\n\n{_ANCORA_PADRAO}"
    return _ANCORA_PADRAO


def _montar_contexto_empresa(request: LlmGatewayRequest) -> str:
    """Serializa metadados + ``input_data`` para o contrato ``gerar_recomendacao``."""
    linhas = [
        f"tarefa: {request.task_type}",
        f"prompt_key: {request.prompt_key}",
        f"trace_id: {request.trace_id}",
        f"tenant_id: {request.tenant_id}",
    ]
    for chave, valor in request.input_data.items():
        linhas.append(f"{chave}: {valor}")
    return "\n".join(linhas)


class LlmServiceGatewayCompleter:
    """Delega geração ao adapter real (Ollama/Anthropic/OpenAI) via porto de aplicação."""

    def __init__(self, llm_service: LlmServicePort) -> None:
        self._llm = llm_service

    async def complete(self, request: LlmGatewayRequest) -> str:
        """Mapeia pedido canónico para o par contexto/base do motor de recomendação."""
        ctx_direct = request.input_data.get("contexto_executivo")
        if isinstance(ctx_direct, str) and ctx_direct.strip():
            contexto = ctx_direct.strip()
        else:
            contexto = _montar_contexto_empresa(request)
        base = _montar_base_normativa(request)
        return await self._llm.gerar_recomendacao(
            contexto_empresa=contexto,
            base_normativa=base,
        )
