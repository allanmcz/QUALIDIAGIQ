"""
Normalização canónica de endereço de e-mail (LGPD / anti-duplicidade).

Camada: Domain (função pura — sem I/O).

Analogia: equivalente a TRIM + UPPER num campo Oracle antes do UNIQUE index,
só que aqui o canónico é minúsculas (RFC 5321 local-part case-sensitive em teoria,
mas o QDI trata e-mail de login/notificação como case-insensitive no domínio prático MVP).
"""

from __future__ import annotations


def normalizar_email(email: str) -> str:
    """Remove espaços laterais e converte para minúsculas (MVP)."""
    return email.strip().lower()
