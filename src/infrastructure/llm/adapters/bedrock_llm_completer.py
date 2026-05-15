"""
Completer Bedrock (stub controlado — ADR-022 Fase 4).

Camada: Infrastructure
Requer ``QDI_LLM_BEDROCK_ENABLED=true`` e dependência opcional ``boto3`` em runtime.
"""

from __future__ import annotations

import json

import structlog

from src.domain.ports.llm_gateway import LlmGatewayRequest
from src.infrastructure.config.settings import Settings

logger = structlog.get_logger(__name__)


class BedrockLlmCompleter:
    """Invoca ``bedrock-runtime`` quando configurado; caso contrário falha de forma explícita."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def complete(self, request: LlmGatewayRequest) -> str:
        if not self._settings.llm_bedrock_enabled:
            raise RuntimeError("bedrock_disabled")
        region = (self._settings.llm_bedrock_region or "").strip()
        model_id = (self._settings.llm_bedrock_model_id or "").strip()
        if not region or not model_id:
            raise RuntimeError("bedrock_misconfigured")

        try:
            import boto3  # type: ignore[import-untyped]
        except ImportError as e:
            raise RuntimeError("bedrock_boto3_missing") from e

        client = boto3.client("bedrock-runtime", region_name=region)
        body = json.dumps(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": json.dumps(request.input_data, ensure_ascii=False)}],
                    }
                ],
                "inferenceConfig": {"maxTokens": 1024},
            }
        )
        response = client.invoke_model(modelId=model_id, body=body)
        raw = response.get("body")
        payload = json.loads(raw.read()) if hasattr(raw, "read") else {}
        output = payload.get("output") or {}
        message = output.get("message") or {}
        parts = message.get("content") or []
        texts = [p.get("text", "") for p in parts if isinstance(p, dict)]
        texto = "\n".join(t for t in texts if t).strip()
        if not texto:
            raise RuntimeError("bedrock_empty_response")
        logger.info(
            "bedrock_complete_ok",
            task_type=str(request.task_type),
            trace_id=request.trace_id,
            model_id=model_id,
        )
        return texto
