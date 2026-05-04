"""
Cache em memória + espelho em disco para PDF quando o upload ao Supabase Storage falha (dev/MVP).

Camada: Infrastructure
Analogia: além da fila em RAM, grava em pasta temporária — restart do Uvicorn não perde o ficheiro
se o volume/caminho persistir (ex.: volume Docker em ``/tmp/qdi-mock-pdf``).
"""

from __future__ import annotations

import contextlib
import os
import re
import tempfile
import threading
import uuid
from collections import OrderedDict
from pathlib import Path

import structlog

_MAX_ITENS = 64

logger = structlog.get_logger(__name__)

_lock = threading.Lock()
_store: OrderedDict[str, bytes] = OrderedDict()

# tenant_id/diagnostico_id.pdf — ambos UUID (path traversal safe)
_CHAVE_SEGURA = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/"
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.pdf$",
    re.IGNORECASE,
)


def _diretorio_spool() -> Path:
    from src.infrastructure.config.settings import get_settings

    raw = get_settings().qdi_pdf_mock_spool_dir
    if raw is not None and str(raw).strip():
        return Path(str(raw).strip()).expanduser().resolve()
    return Path(tempfile.gettempdir()) / "qdi-mock-pdf"


def _caminho_arquivo_spool(chave_normalizada: str) -> Path | None:
    if not _CHAVE_SEGURA.match(chave_normalizada):
        return None
    partes = chave_normalizada.split("/")
    if len(partes) != 2:
        return None
    try:
        uuid.UUID(partes[0])
        stem = partes[1][:-4]
        uuid.UUID(stem)
    except ValueError:
        return None
    return _diretorio_spool() / partes[0] / partes[1]


def pdf_mock_existe_em_disco(caminho_relativo: str) -> bool:
    """Indica se o ficheiro existe no spool em disco (chave canónica ``tenant_id/diagnostico_id.pdf``)."""
    chave = caminho_relativo.strip().lstrip("/")
    path_disk = _caminho_arquivo_spool(chave)
    return path_disk is not None and path_disk.is_file()


def registrar_pdf_mock(caminho_relativo: str, dados: bytes) -> None:
    """
    Guarda bytes do PDF em disco primeiro e depois na RAM (LRU).

    Ordem disco → RAM: após restart do Uvicorn (``--reload``) ou eviction do LRU,
    o GET ainda encontra o ficheiro no volume (ex.: ``qdi-mock-pdf-spool`` no Compose).

    Chave canónica: ``tenant_id/diagnostico_id.pdf``.
    """
    chave = caminho_relativo.strip().lstrip("/")
    path_disk = _caminho_arquivo_spool(chave)
    if path_disk is not None:
        try:
            path_disk.parent.mkdir(parents=True, exist_ok=True)
            path_disk.write_bytes(dados)
            with contextlib.suppress(OSError):
                os.chmod(path_disk, 0o600)
        except OSError as e:
            # Disco cheio ou permissão — mantém só RAM; GET pode falhar após restart.
            logger.error(
                "pdf_mock_spool_escrita_falhou",
                chave=chave,
                path=str(path_disk),
                erro=str(e),
            )
    with _lock:
        if chave in _store:
            _store.move_to_end(chave)
        _store[chave] = dados
        while len(_store) > _MAX_ITENS:
            _store.popitem(last=False)


def obter_pdf_mock(caminho_relativo: str) -> bytes | None:
    """Devolve bytes da RAM, senão lê do disco e repovoa o LRU."""
    chave = caminho_relativo.strip().lstrip("/")
    path_disk = _caminho_arquivo_spool(chave)
    with _lock:
        dados = _store.get(chave)
        if dados is not None:
            _store.move_to_end(chave)
            return dados
    if path_disk is not None and path_disk.is_file():
        try:
            blob = path_disk.read_bytes()
        except OSError:
            return None
        with _lock:
            if chave in _store:
                _store.move_to_end(chave)
                return _store[chave]
            _store[chave] = blob
            while len(_store) > _MAX_ITENS:
                _store.popitem(last=False)
        return blob
    return None


def limpar_apenas_memoria_para_teste() -> None:
    """Uso exclusivo em testes — simula reinício da API sem apagar o spool em disco."""
    with _lock:
        _store.clear()
