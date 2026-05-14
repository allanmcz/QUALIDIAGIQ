"""
Adapter PostgreSQL — pesos macro por dimensão versionados por vigência.

Camada: Infrastructure
Implementa: NormativaScoreMacroRepository

Tabela: qdi.normativa_score_macro_dimensao (migração 0015).

Analogia Winthor: é como ler alíquotas/parametrizações por vigência na filial —
 aqui a vigência está nas colunas `vigencia_inicio` / `vigencia_fim`.
"""

from __future__ import annotations

from datetime import date

import psycopg2
import psycopg2.errors
import structlog

from src.domain.repositories.normativa_score_macro_repository import NormativaScoreMacroRepository
from src.domain.value_objects.score import (
    Dimensao,
    PesoMacroNormativoVigente,
    exigir_mapa_pesos_macro_completo,
)

logger = structlog.get_logger(__name__)

_SQL_DISTINCT_ON = """
SELECT DISTINCT ON (dimensao)
    dimensao,
    peso::float8 AS peso,
    vigencia_inicio,
    vigencia_fim,
    rotulo_versao
FROM qdi.normativa_score_macro_dimensao
WHERE vigencia_inicio <= %(ref)s
  AND (vigencia_fim IS NULL OR vigencia_fim >= %(ref)s)
ORDER BY dimensao, vigencia_inicio DESC
"""


class PostgresNormativaScoreMacroRepository(NormativaScoreMacroRepository):
    """Resolve vigência na data via `DISTINCT ON` (última vigência_início por dimensão)."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn.strip()

    def obter_metadados_macro_validos_na_data(
        self, data_referencia: date
    ) -> dict[Dimensao, PesoMacroNormativoVigente]:
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

        out: dict[Dimensao, PesoMacroNormativoVigente] = {}
        for dim_raw, peso_raw, vig_ini, vig_fim, rotulo in rows:
            try:
                dim = Dimensao(str(dim_raw))
            except ValueError as e:
                raise ValueError(
                    f"Dimensão desconhecida na normativa_score_macro: {dim_raw!r}."
                ) from e
            if vig_ini is None:
                raise ValueError(f"vigencia_inicio nula para dimensão {dim_raw!r}.")
            ini = vig_ini if isinstance(vig_ini, date) else date.fromisoformat(str(vig_ini))
            fim_d: date | None
            if vig_fim is None:
                fim_d = None
            else:
                fim_d = vig_fim if isinstance(vig_fim, date) else date.fromisoformat(str(vig_fim))
            rotulo_s = str(rotulo).strip() if rotulo is not None and str(rotulo).strip() else None
            out[dim] = PesoMacroNormativoVigente(
                peso=float(peso_raw),
                vigencia_inicio=ini,
                vigencia_fim=fim_d,
                rotulo_versao=rotulo_s,
            )

        exigir_mapa_pesos_macro_completo({d: m.peso for d, m in out.items()})
        return out
