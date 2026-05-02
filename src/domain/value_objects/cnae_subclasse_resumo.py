"""
Value object — linha mínima de subclass CNAE 2.3 para lookup na UI/API.

Camada: Domain (sem deps externas).

Base: Resolução CONCLA nº 02/2023 (CNAE 2.3).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CnaeSubclasseResumo:
    """Identificador de 7 dígitos + descrição oficial IBGE/CONCLA."""

    subclasse_id: str
    descricao: str

    def __post_init__(self) -> None:
        sid = (self.subclasse_id or "").strip()
        if len(sid) != 7 or not sid.isdigit():
            raise ValueError("subclasse_id deve ter exatamente 7 dígitos numéricos")
        if not (self.descricao or "").strip():
            raise ValueError("descricao não pode ser vazia")
