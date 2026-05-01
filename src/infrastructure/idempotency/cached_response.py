"""DTO interno para replay idempotente (middleware HTTP)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CorpoCacheadoIdempotencia:
    status_code: int
    body: bytes
    headers: tuple[tuple[str, str], ...]
