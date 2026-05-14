"""
Port — pesos por pergunta do catálogo versionados por vigência (M03).

Camada: Domain (interface — Dependency Inversion Principle)

Implementações:
    src/infrastructure/repositories/embutidas_normativa_pergunta_peso_repository.py
    src/infrastructure/repositories/postgres_normativa_pergunta_peso_repository.py

Tabela: ``qdi.normativa_pergunta_peso`` (migração 0042). Chave de negócio: ``pergunta_codigo``
(ex.: ``Q-EST-001``), alinhado ao JSON ``perguntas_mvp.json``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date

    from src.domain.value_objects.normativa_pergunta_peso import PesoPerguntaNormativoVigente


class NormativaPerguntaPesoRepository(ABC):
    """Resolve pesos por código de pergunta vigentes na data (overlay sobre o catálogo JSON)."""

    @abstractmethod
    def obter_metadados_por_codigo_validos_na_data(
        self,
        data_referencia: date,
        codigos: frozenset[str],
    ) -> dict[str, PesoPerguntaNormativoVigente]:
        """
        Devolve apenas códigos com linha normativa vigente em ``data_referencia``.

        Args:
            data_referencia: Data-canónica (tipicamente UTC do pedido).
            codigos: Conjunto de códigos canónicos presentes no catálogo.

        Returns:
            Subconjunto de ``codigos`` com metadado de peso DB (pode ser vazio).

        Raises:
            ValueError: dados inválidos no backend.
            RuntimeError: falha de infraestrutura (ex.: Postgres).
        """
        ...
