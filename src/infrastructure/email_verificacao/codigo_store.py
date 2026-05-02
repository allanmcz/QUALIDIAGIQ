"""
Armazenamento em processo dos códigos de verificação de e-mail (MVP).

Camada: Infrastructure — não usar para multi-instância sem Redis/DB; um único worker OK.

Analogia: TTL como sessão curta no Oracle (flash cache), só que em RAM.
"""

from __future__ import annotations

import threading
import time
from typing import Final

from cachetools import TTLCache

_MAX_EMAILS: Final[int] = 20_000
_CODIGO_TTL_SEC: Final[int] = 600  # 10 min
_RATE_SEGUNDOS: Final[int] = 45

_codigos = TTLCache(maxsize=_MAX_EMAILS, ttl=_CODIGO_TTL_SEC)
_ultimo_envio: TTLCache[str, float] = TTLCache(maxsize=_MAX_EMAILS, ttl=_CODIGO_TTL_SEC)
_lock = threading.Lock()


def normalizar_email(email: str) -> str:
    return email.strip().lower()


def pode_reenviar(email_norm: str) -> bool:
    """Evita flood no mesmo inbox."""
    with _lock:
        ultimo = _ultimo_envio.get(email_norm)
        if ultimo is None:
            return True
        return time.monotonic() - ultimo >= _RATE_SEGUNDOS


def registrar_envio(email_norm: str, codigo: str) -> None:
    with _lock:
        _codigos[email_norm] = codigo
        _ultimo_envio[email_norm] = time.monotonic()


def validar_e_consumir(email_norm: str, codigo_informado: str) -> bool:
    """Comparação em tempo constante; remove o código após sucesso (uso único)."""
    import secrets

    limpo = codigo_informado.strip().replace(" ", "")
    with _lock:
        esperado = _codigos.get(email_norm)
        if esperado is None:
            return False
        if not secrets.compare_digest(esperado, limpo):
            return False
        del _codigos[email_norm]
        return True


def codigo_ativo_para_debug(email_norm: str) -> str | None:
    """Somente testes — não expor em produção."""
    with _lock:
        return _codigos.get(email_norm)


def limpar_para_testes() -> None:
    """Limpa caches em memória — usar apenas em pytest (isolamento entre casos)."""
    with _lock:
        _codigos.clear()
        _ultimo_envio.clear()
