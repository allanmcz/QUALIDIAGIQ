"""
Adapter Postgres (asyncpg) para consulta CNAE em qdi.cnae_subclasse.

Camada: Infrastructure
Implementa: CnaeSubclasseConsultaPort

Nota: conexão usa papel com permissão SELECT (tipicamente postgres em dev ou pool serviço em prod).
RLS Supabase para role authenticated não se aplica ao superuser — endpoint HTTP já exige JWT.
"""

from __future__ import annotations

import re

import asyncpg
import structlog

from src.application.ports.cnae_subclasse_consulta_port import CnaeSubclasseConsultaPort
from src.domain.value_objects.cnae_subclasse_resumo import CnaeSubclasseResumo

logger = structlog.get_logger(__name__)

_DIGITOS = re.compile(r"^\d+$")


def _escape_like(valor: str) -> str:
    """Escapa `%`, `_` e `\` para uso em ILIKE ... ESCAPE '\\'."""
    return valor.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


class PostgresCnaeSubclasseRepository(CnaeSubclasseConsultaPort):
    """Busca parametrizada por prefixo numérico e/ou texto na descrição."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn.strip().replace("postgresql+asyncpg://", "postgresql://", 1)

    async def buscar(self, *, consulta: str, limite: int) -> list[CnaeSubclasseResumo]:
        q = consulta.strip()
        condicoes: list[str] = []
        args: list[object] = []
        n = 1

        if _DIGITOS.fullmatch(q):
            condicoes.append(f"subclasse_id::text LIKE ${n}")
            args.append(f"{q}%")
            n += 1

        condicoes.append(f"descricao ILIKE ${n} ESCAPE '\\'")
        args.append(f"%{_escape_like(q)}%")
        n += 1

        where_sql = " OR ".join(condicoes)
        sql = f"""
            SELECT subclasse_id::text AS sid, descricao::text AS dsc
            FROM qdi.cnae_subclasse
            WHERE deleted_at IS NULL
              AND ({where_sql})
            ORDER BY subclasse_id
            LIMIT ${n}
        """
        args.append(limite)

        try:
            conn = await asyncpg.connect(self._dsn, timeout=8)
        except Exception as e:
            logger.error("cnae_conexao_falhou", erro=str(e))
            raise RuntimeError("Falha ao conectar ao Postgres para consulta CNAE.") from e

        try:
            try:
                rows = await conn.fetch(sql, *args)
            except asyncpg.exceptions.UndefinedTableError as e:
                logger.warning("cnae_tabela_ausente", erro=str(e))
                raise RuntimeError(
                    "Tabela qdi.cnae_subclasse ausente. Aplique migrações 0013/0014."
                ) from e
        finally:
            await conn.close()

        out: list[CnaeSubclasseResumo] = []
        for row in rows:
            try:
                out.append(CnaeSubclasseResumo(subclasse_id=row["sid"], descricao=row["dsc"]))
            except ValueError:
                continue
        return out
