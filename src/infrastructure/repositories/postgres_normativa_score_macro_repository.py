"""
Adapter PostgreSQL — pesos macro por dimensão versionados por vigência.

Camada: Infrastructure
Implementa: NormativaScoreMacroRepository

Tabela: qdi.normativa_score_macro_dimensao (migração 0015).

Analogia Winthor: é como ler alíquotas/parametrizações por vigência na filial —
 aqui a vigência está nas colunas `vigencia_inicio` / `vigencia_fim`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import psycopg2
import psycopg2.errors
import structlog

from src.domain.repositories.normativa_score_macro_repository import NormativaScoreMacroRepository
from src.domain.value_objects.score import Dimensao

logger = structlog.get_logger(__name__)

if TYPE_CHECKING:
    from datetime import date

_SQL_DISTINCT_ON = """
SELECT DISTINCT ON (dimensao)
    dimensao,
    peso::float8 AS peso
FROM qdi.normativa_score_macro_dimensao
WHERE vigencia_inicio <= %(ref)s
  AND (vigencia_fim IS NULL OR vigencia_fim >= %(ref)s)
ORDER BY dimensao, vigencia_inicio DESC
"""


class PostgresNormativaScoreMacroRepository(NormativaScoreMacroRepository):
    """Resolve vigência na data via `DISTINCT ON` (última vigência_início por dimensão)."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn.strip()

    def obter_pesos_macro_validos_na_data(self, data_referencia: date) -> dict[Dimensao, float]:
        try:
            conn = psycopg2.connect(self._dsn, connect_timeout=8)
        except Exception as e:
            logger.error("normativa_score_macro_conexao_falhou", erro=str(e))
            raise RuntimeError(
                "Falha ao conectar ao Postgres para ler pesos macro versionados."
            ) from e

        try:
            try:
                with conn.cursor() as cur:
                    cur.execute(_SQL_DISTINCT_ON, {"ref": data_referencia})
                    rows = cur.fetchall()
            except psycopg2.errors.UndefinedTable as e:
                logger.warning("normativa_score_macro_tabela_ausente", erro=str(e))
                raise RuntimeError(
                    "Tabela qdi.normativa_score_macro_dimensao ausente. Aplique a migração 0015."
                ) from e
        finally:
            conn.close()

        out: dict[Dimensao, float] = {}
        for dim_raw, peso_raw in rows:
            try:
                dim = Dimensao(str(dim_raw))
            except ValueError as e:
                raise ValueError(
                    f"Dimensão desconhecida na normativa_score_macro: {dim_raw!r}."
                ) from e
            out[dim] = float(peso_raw)

        return out
