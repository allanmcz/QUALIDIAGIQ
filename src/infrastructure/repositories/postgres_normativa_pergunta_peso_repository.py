"""
Adapter PostgreSQL — pesos por pergunta versionados (overlay M03).

Camada: Infrastructure
Implementa: NormativaPerguntaPesoRepository

Tabela: ``qdi.normativa_pergunta_peso`` (migração 0042).
"""

from __future__ import annotations

from datetime import date

import psycopg2
import psycopg2.errors
import structlog

from src.domain.repositories.normativa_pergunta_peso_repository import (
    NormativaPerguntaPesoRepository,
)
from src.domain.value_objects.normativa_pergunta_peso import PesoPerguntaNormativoVigente

logger = structlog.get_logger(__name__)

_SQL = """
SELECT DISTINCT ON (pergunta_codigo)
    pergunta_codigo,
    peso::float8 AS peso,
    vigencia_inicio,
    vigencia_fim,
    rotulo_versao
FROM qdi.normativa_pergunta_peso
WHERE pergunta_codigo = ANY(%(codigos)s::text[])
  AND vigencia_inicio <= %(ref)s
  AND (vigencia_fim IS NULL OR vigencia_fim >= %(ref)s)
ORDER BY pergunta_codigo, vigencia_inicio DESC
"""


class PostgresNormativaPerguntaPesoRepository(NormativaPerguntaPesoRepository):
    """Resolve a última ``vigencia_inicio`` por ``pergunta_codigo`` na data."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn.strip()

    def obter_metadados_por_codigo_validos_na_data(
        self,
        data_referencia: date,
        codigos: frozenset[str],
    ) -> dict[str, PesoPerguntaNormativoVigente]:
        if not codigos:
            return {}
        try:
            conn = psycopg2.connect(self._dsn, connect_timeout=8)
        except Exception as e:
            logger.error("normativa_pergunta_peso_conexao_falhou", erro=str(e))
            raise RuntimeError(
                "Falha ao conectar ao Postgres para ler pesos normativos por pergunta."
            ) from e

        lista = sorted(codigos)
        try:
            try:
                with conn.cursor() as cur:
                    cur.execute(_SQL, {"ref": data_referencia, "codigos": lista})
                    rows = cur.fetchall()
            except psycopg2.errors.UndefinedTable as e:
                logger.warning(
                    "normativa_pergunta_peso_tabela_ausente_fallback_json",
                    erro=str(e),
                )
                return {}
        finally:
            conn.close()

        out: dict[str, PesoPerguntaNormativoVigente] = {}
        for cod_raw, peso_raw, vig_ini, vig_fim, rotulo in rows:
            codigo = str(cod_raw)
            if vig_ini is None:
                raise ValueError(f"vigencia_inicio nula para pergunta_codigo {codigo!r}.")
            ini = vig_ini if isinstance(vig_ini, date) else date.fromisoformat(str(vig_ini))
            fim_d: date | None
            if vig_fim is None:
                fim_d = None
            else:
                fim_d = vig_fim if isinstance(vig_fim, date) else date.fromisoformat(str(vig_fim))
            rotulo_s = str(rotulo).strip() if rotulo is not None and str(rotulo).strip() else None
            out[codigo] = PesoPerguntaNormativoVigente(
                peso=float(peso_raw),
                vigencia_inicio=ini,
                vigencia_fim=fim_d,
                rotulo_versao=rotulo_s,
            )
        return out
