"""Catálogo ``perguntas_mvp.json`` em memória + overlay de pesos via Postgres (migração 0042)."""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime
from threading import Lock

from src.domain.entities.questionario import Pergunta
from src.domain.repositories.normativa_pergunta_peso_repository import (
    NormativaPerguntaPesoRepository,
)
from src.domain.value_objects.normativa_pergunta_peso import PesoPerguntaNormativoVigente
from src.infrastructure.questionario.json_banco_loader import carregar_banco_mvp

_RAW: list[Pergunta] | None = None


@dataclass(frozen=True, slots=True)
class CatalogoPerguntasEfetivo:
    """
    Catálogo com pesos já fundidos (JSON + overlay DB).

    ``overlay_por_codigo`` mapeia apenas perguntas cuja linha normativa DB substituiu o peso do JSON
    (transparência no manifesto).
    """

    perguntas: tuple[Pergunta, ...]
    overlay_por_codigo: dict[str, tuple[float, PesoPerguntaNormativoVigente]]


# Cache do merge (overlay DB) — reduz SELECT repetidos na mesma janela TTL.
_MERGED_MAX_DATES = 16
_merged_lock = Lock()
_merged_by_date: OrderedDict[date, tuple[float, CatalogoPerguntasEfetivo]] = OrderedDict()


def _raw_catalogo() -> list[Pergunta]:
    """Lê o JSON uma vez por processo (sem overlay)."""
    global _RAW
    if _RAW is None:
        _RAW = carregar_banco_mvp()
    return _RAW


def _normativa_pergunta_repo() -> NormativaPerguntaPesoRepository:
    from src.presentation.api import deps_infra_services as deps

    return deps.get_normativa_pergunta_peso_repository()


def _ttl_segundos_overlay_cache() -> float:
    """Lê TTL de settings; 0 = cache desligado (sempre Postgres quando há adapter com DSN)."""
    from src.infrastructure.config.settings import get_settings

    try:
        s = int(get_settings().qdi_normativa_pergunta_peso_cache_ttl_seconds)
    except Exception:
        return 60.0
    if s <= 0:
        return 0.0
    return float(s)


def _merged_cache_pegar(ref: date) -> CatalogoPerguntasEfetivo | None:
    ttl = _ttl_segundos_overlay_cache()
    if ttl <= 0.0:
        return None
    now_m = time.monotonic()
    with _merged_lock:
        hit = _merged_by_date.get(ref)
        if hit is None:
            return None
        exp, val = hit
        if exp <= now_m:
            del _merged_by_date[ref]
            return None
        _merged_by_date.move_to_end(ref)
        return val


def _merged_cache_guardar(ref: date, val: CatalogoPerguntasEfetivo) -> None:
    ttl = _ttl_segundos_overlay_cache()
    if ttl <= 0.0:
        return
    now_m = time.monotonic()
    exp = now_m + ttl
    with _merged_lock:
        _merged_by_date[ref] = (exp, val)
        _merged_by_date.move_to_end(ref)
        while len(_merged_by_date) > _MERGED_MAX_DATES:
            _merged_by_date.popitem(last=False)


def _merged_cache_limpar() -> None:
    with _merged_lock:
        _merged_by_date.clear()


def get_catalogo_perguntas_efetivo(
    *,
    data_referencia_normativa: date | None = None,
) -> CatalogoPerguntasEfetivo:
    """
    Catálogo com pesos resolvidos na data (UTC do processo se omitido).

    LC 214/2025 — previsibilidade; overlay opcional em ``qdi.normativa_pergunta_peso``.
    Resultado fundido é memorizado por ``data_referencia`` durante ``QDI_NORMATIVA_PERGUNTA_PESO_CACHE_TTL_SECONDS``
    (default 60s) para reduzir carga no Postgres em rajadas de pedidos.
    """
    ref = data_referencia_normativa or datetime.now(UTC).date()
    cached = _merged_cache_pegar(ref)
    if cached is not None:
        return cached

    raw = _raw_catalogo()
    codigos = frozenset(p.codigo for p in raw)
    meta = _normativa_pergunta_repo().obter_metadados_por_codigo_validos_na_data(ref, codigos)

    out: list[Pergunta] = []
    overlay: dict[str, tuple[float, PesoPerguntaNormativoVigente]] = {}
    for p in raw:
        m = meta.get(p.codigo)
        if m is not None:
            overlay[p.codigo] = (p.peso, m)
            out.append(replace(p, peso=m.peso))
        else:
            out.append(p)
    result = CatalogoPerguntasEfetivo(perguntas=tuple(out), overlay_por_codigo=overlay)
    _merged_cache_guardar(ref, result)
    return result


def get_banco_perguntas_cached() -> list[Pergunta]:
    """Lista fundida — mesma ordem e IDs estáveis do JSON (compatível com POST diagnóstico)."""
    return list(get_catalogo_perguntas_efetivo().perguntas)


def reset_catalogo_perguntas_em_memoria() -> None:
    """Testes — força releitura do JSON e invalida cache do merge overlay."""
    global _RAW
    _RAW = None
    _merged_cache_limpar()


def versao_catalogo_lida() -> str:
    """Alias público — mesma origem que o manifesto (JSON versionado no repositório)."""
    from src.infrastructure.questionario.json_banco_loader import versao_catalogo_banco_mvp

    return versao_catalogo_banco_mvp()
