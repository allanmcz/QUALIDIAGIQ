"""
Tipo de tarefa enviada ao gateway LLM convergente (QDI).

Camada: Domain
Base: ADR-022 — ``LLMTaskType`` identifica o perfil de risco/custo sem acoplar a SDK.
"""

from __future__ import annotations

from enum import StrEnum


class LlmTaskType(StrEnum):
    """Tarefas suportadas pelo router convergente (MVP técnico)."""

    CLASSIFICACAO_RESPOSTA = "classificacao_resposta"
    ANALISE_NORMATIVA_RAG = "analise_normativa_rag"
    RELATORIO_EXECUTIVO = "relatorio_executivo"
    EXTRACAO_ESTRUTURADA = "extracao_estruturada"
    REVISAO_CONSISTENCIA = "revisao_consistencia"
    EXPLICACAO_SCORE = "explicacao_score"
