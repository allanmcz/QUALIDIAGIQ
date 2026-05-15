"""
Circuit breaker em memória por provider LLM (ADR-022 Fase 4 — MVP).

Camada: Infrastructure
"""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class _CircuitState:
    failures: int = 0
    open_until: float = 0.0


class LlmCircuitBreaker:
    """
    Abre o circuito após ``failure_threshold`` falhas consecutivas;
    permanece aberto ``cooldown_seconds``.
    """

    def __init__(self, *, failure_threshold: int = 5, cooldown_seconds: float = 60.0) -> None:
        self._threshold = max(1, failure_threshold)
        self._cooldown = max(1.0, cooldown_seconds)
        self._states: dict[str, _CircuitState] = {}

    def _state(self, key: str) -> _CircuitState:
        if key not in self._states:
            self._states[key] = _CircuitState()
        return self._states[key]

    def is_open(self, provider: str) -> bool:
        st = self._state(provider)
        if st.open_until <= 0:
            return False
        if time.monotonic() >= st.open_until:
            st.open_until = 0.0
            st.failures = 0
            return False
        return True

    def record_success(self, provider: str) -> None:
        st = self._state(provider)
        st.failures = 0
        st.open_until = 0.0

    def record_failure(self, provider: str) -> None:
        st = self._state(provider)
        st.failures += 1
        if st.failures >= self._threshold:
            st.open_until = time.monotonic() + self._cooldown


# Singleton process-local (MVP)
_breaker: LlmCircuitBreaker | None = None


def get_llm_circuit_breaker(
    *, failure_threshold: int = 5, cooldown_seconds: float = 60.0
) -> LlmCircuitBreaker:
    global _breaker
    if _breaker is None:
        _breaker = LlmCircuitBreaker(
            failure_threshold=failure_threshold,
            cooldown_seconds=cooldown_seconds,
        )
    return _breaker


def reset_llm_circuit_breaker_for_tests() -> None:
    """Limpa estado global (pytest)."""
    global _breaker
    _breaker = None
