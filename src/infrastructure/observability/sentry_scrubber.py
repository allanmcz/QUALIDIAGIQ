"""
Mascaramento de PII antes de enviar eventos ao Sentry (terceiro).

Camada: Infrastructure
Base legal: LGPD art. 46 (segurança e boas práticas); minimização de dados a terceiros.

Analogia: como uma view Oracle com colunas mascaradas antes de exportar para outro schema.
"""

from __future__ import annotations

import re
from typing import Any

# Regex para detectar e mascarar PII em strings livres
_REGEX_CNPJ = re.compile(r"\b\d{2}[.\-/]?\d{3}[.\-/]?\d{3}[.\-/]?\d{4}[.\-/]?\d{2}\b")
_REGEX_CPF = re.compile(r"\b\d{3}[.\-]?\d{3}[.\-]?\d{3}[.\-]?\d{2}\b")
_REGEX_EMAIL = re.compile(r"\b[\w._%+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
_REGEX_TELEFONE = re.compile(r"\b\(?\d{2}\)?[\s\-]?9?\d{4}[\s\-]?\d{4}\b")

# Campos cujo valor deve ser redatado (chave case-insensitive)
_CAMPOS_SENSIVEIS = frozenset(
    {
        "password",
        "senha",
        "hashed_password",
        "hash_senha",
        "token",
        "access_token",
        "refresh_token",
        "jwt",
        "secret",
        "api_key",
        "apikey",
        "authorization",
        "respondente_email",
        "respondente_nome",
        "respondente_telefone",
        "respondente_cargo",
        "empresa_cnpj",
        "empresa_razao_social",
        "credit_card",
        "cartao",
    }
)


def _mascarar_string(s: str) -> str:
    """Aplica regexes de mascaramento em string livre."""
    s = _REGEX_EMAIL.sub("[EMAIL_REDACTED]", s)
    s = _REGEX_CNPJ.sub("[CNPJ_REDACTED]", s)
    s = _REGEX_CPF.sub("[CPF_REDACTED]", s)
    s = _REGEX_TELEFONE.sub("[TEL_REDACTED]", s)
    return s


def _scrub_item(x: Any) -> Any:
    if isinstance(x, dict):
        return _scrub_dict(x)
    if isinstance(x, str):
        return _mascarar_string(x)
    return x


def _scrub_dict(d: dict[str, Any] | None) -> dict[str, Any] | None:
    """Mascara campos sensíveis e PII em strings, recursivamente."""
    if d is None or not isinstance(d, dict):
        return d
    out: dict[str, Any] = {}
    for k, v in d.items():
        if k.lower() in _CAMPOS_SENSIVEIS:
            out[k] = "[REDACTED]"
        elif isinstance(v, dict):
            out[k] = _scrub_dict(v)
        elif isinstance(v, list):
            out[k] = [_scrub_item(i) for i in v]
        elif isinstance(v, str):
            out[k] = _mascarar_string(v)
        else:
            out[k] = v
    return out


def _scrub_request_data(raw: Any) -> Any:
    """Normaliza body da request no payload do Sentry."""
    if isinstance(raw, dict):
        return _scrub_dict(raw)
    if isinstance(raw, str):
        return _mascarar_string(raw)
    return raw


def scrubber_sentry(event: Any, _hint: Any) -> Any:
    """
    Filtro `before_send` do Sentry SDK.

    Retorna o evento modificado. Não descartamos o evento (visibilidade de erros com PII
    removida).
    """
    if "request" in event:
        req = event["request"]
        if isinstance(req, dict):
            if "data" in req:
                req["data"] = _scrub_request_data(req.get("data"))
            if "cookies" in req:
                req["cookies"] = "[REDACTED]"
            if "headers" in req and isinstance(req.get("headers"), dict):
                h = req["headers"]
                req["headers"] = {
                    k: (
                        "[REDACTED]"
                        if k.lower() in {"authorization", "cookie", "idempotency-key"}
                        else _mascarar_string(v) if isinstance(v, str) else v
                    )
                    for k, v in h.items()
                }
            if "query_string" in req and isinstance(req["query_string"], str):
                req["query_string"] = _mascarar_string(req["query_string"])

    if "exception" in event and isinstance(event.get("exception"), dict):
        exc_block = event["exception"]
        if "values" in exc_block and isinstance(exc_block["values"], list):
            for exc in exc_block["values"]:
                if isinstance(exc, dict) and "value" in exc and isinstance(exc["value"], str):
                    exc["value"] = _mascarar_string(exc["value"])

    if "breadcrumbs" in event and isinstance(event.get("breadcrumbs"), dict):
        bc_block = event["breadcrumbs"]
        if "values" in bc_block and isinstance(bc_block["values"], list):
            for bc in bc_block["values"]:
                if isinstance(bc, dict):
                    if "message" in bc and isinstance(bc["message"], str):
                        bc["message"] = _mascarar_string(bc["message"])
                    if "data" in bc:
                        bc["data"] = (
                            _scrub_dict(bc["data"]) if isinstance(bc["data"], dict) else bc["data"]
                        )

    if "user" in event and isinstance(event["user"], dict):
        u = event["user"]
        if "email" in u:
            u["email"] = "[REDACTED]"

    if "extra" in event and isinstance(event["extra"], dict):
        event["extra"] = _scrub_dict(event["extra"]) or {}

    return event
