"""
Hash de senha para administradores — Argon2id (atual) com verificação legada bcrypt.

Camada: Infrastructure (criptografia; sem I/O de rede).
ADR-010 — substitui dependência de passlib/bcrypt frágil em runtime.

Parâmetros Argon2id alinhados ao OWASP Password Storage Cheat Sheet (time_cost=2,
memory_cost=64 MiB, parallelism=2).

Analogia: migração gradual como manter dois login triggers no Oracle até deprecar o antigo.
"""

from __future__ import annotations

import bcrypt
import structlog
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

logger = structlog.get_logger(__name__)

_PH = PasswordHasher(
    time_cost=2,
    memory_cost=64 * 1024,
    parallelism=2,
    hash_len=32,
    salt_len=16,
)


def gerar_hash_senha(senha: str) -> tuple[str, str]:
    """
    Gera hash Argon2id da senha em texto claro.

    Returns:
        Tupla (hashed_password, algoritmo) com algoritmo sempre ``argon2id``.
    """
    return _PH.hash(senha), "argon2id"


def resolver_algoritmo_armazenado(
    hash_armazenado: str,
    hash_algoritmo_coluna: str | None,
) -> str:
    """
    Resolve qual algoritmo usar na verificação.

    Prioriza a coluna ``hash_algoritmo`` quando confiável; caso contrário infere pelo prefixo PHC.
    """
    c = (hash_algoritmo_coluna or "").strip().lower()
    if c in ("argon2id", "bcrypt"):
        return c
    h = hash_armazenado.strip()
    if h.startswith("$argon2"):
        return "argon2id"
    if h.startswith("$2"):
        return "bcrypt"
    return "bcrypt"


def verificar_senha(senha_clara: str, hash_armazenado: str, algoritmo: str) -> bool:
    """Verifica senha contra hash (Argon2id ou bcrypt legado)."""
    algo = algoritmo.strip().lower()
    if algo == "argon2id":
        try:
            _PH.verify(hash_armazenado, senha_clara)
            return True
        except VerifyMismatchError:
            return False
        except InvalidHashError:
            logger.error("hash_argon2_invalido")
            return False
    if algo == "bcrypt":
        return _verificar_bcrypt(senha_clara, hash_armazenado)
    logger.error("algoritmo_hash_desconhecido", algoritmo=algoritmo)
    return False


def _verificar_bcrypt(senha_clara: str, hash_armazenado: str) -> bool:
    try:
        return bcrypt.checkpw(
            senha_clara.encode("utf-8"),
            hash_armazenado.encode("utf-8"),
        )
    except Exception:
        logger.exception("falha_verificar_bcrypt")
        return False


def precisa_rehash(hash_armazenado: str, algoritmo: str) -> bool:
    """Indica se deve persistir novo hash Argon2id (migração ou parâmetros desatualizados)."""
    algo = algoritmo.strip().lower()
    if algo != "argon2id":
        return True
    try:
        return _PH.check_needs_rehash(hash_armazenado)
    except InvalidHashError:
        return True
