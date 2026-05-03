"""
Cache em memória para PDF quando o upload ao Supabase Storage falha (dev/MVP).

Camada: Infrastructure
Analogia: fila em memória antes de gravar no disco — aqui só para o link do e-mail funcionar em demo local.
"""

from __future__ import annotations

import threading
from collections import OrderedDict

_MAX_ITENS = 64

_lock = threading.Lock()
_store: OrderedDict[str, bytes] = OrderedDict()


def registrar_pdf_mock(caminho_relativo: str, dados: bytes) -> None:
    """
    Guarda bytes do PDF; chave = caminho «tenant_id/diagnostico_id.pdf».

    LRU simples quando excede `_MAX_ITENS`.
    """
    chave = caminho_relativo.strip().lstrip("/")
    with _lock:
        if chave in _store:
            _store.move_to_end(chave)
        _store[chave] = dados
        while len(_store) > _MAX_ITENS:
            _store.popitem(last=False)


def obter_pdf_mock(caminho_relativo: str) -> bytes | None:
    """Devolve bytes ou None se não existir / expirado (evict LRU)."""
    chave = caminho_relativo.strip().lstrip("/")
    with _lock:
        dados = _store.get(chave)
        if dados is not None:
            _store.move_to_end(chave)
        return dados
