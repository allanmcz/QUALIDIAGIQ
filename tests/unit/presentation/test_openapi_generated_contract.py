"""Contrato mínimo do `docs/api/openapi.generated.json` (paths ADR-012 + núcleo público).

Garante que o snapshot versionado inclui rotas críticas LGPD e retificação append-only.
CI já bloqueia drift via regeneração; este teste falha se paths forem renomeados sem atualizar o artefacto.
"""

from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
_OPENAPI_PATH = _ROOT / "docs" / "api" / "openapi.generated.json"

# path OpenAPI → métodos HTTP em minúsculas (exclui chaves auxiliares como "parameters")
_REQUIRED_PATHS_METHODS: dict[str, frozenset[str]] = {
    "/health": frozenset({"get"}),
    "/public/institucional": frozenset({"get"}),
    "/diagnosticos/metodologia": frozenset({"get"}),
    "/privacidade/solicitacoes": frozenset({"get", "post"}),
    "/privacidade/solicitacoes/{solicitacao_id}/status": frozenset({"patch"}),
    "/privacidade/diagnosticos/{diagnostico_id}/anonimizar-respondente": frozenset({"post"}),
    "/privacidade/diagnosticos/{diagnostico_id}/export-portabilidade": frozenset({"get"}),
    "/diagnosticos/{diagnostico_id}/retificacoes": frozenset({"get"}),
    "/diagnosticos/{diagnostico_id}/retificacao": frozenset({"post"}),
}


class TestOpenapiGeneratedContract:
    """Leitura estática do JSON OpenAPI exportado pelo FastAPI."""

    def test_arquivo_presente(self) -> None:
        assert _OPENAPI_PATH.is_file(), (
            f"Falta {_OPENAPI_PATH.relative_to(_ROOT)} — execute make openapi-export e faça commit."
        )

    def test_openapi_paths_adicionados_com_metodos(self) -> None:
        raw = json.loads(_OPENAPI_PATH.read_text(encoding="utf-8"))
        version = raw.get("openapi", "")
        assert str(version).startswith("3."), f"Esperado OpenAPI 3.x, obtido: {version!r}"

        paths = raw.get("paths")
        assert isinstance(paths, dict), "paths deve ser um object"

        http_verbs = frozenset({"get", "post", "put", "patch", "delete", "options", "head", "trace"})
        for path, expected_methods in _REQUIRED_PATHS_METHODS.items():
            assert path in paths, f"path ausente no contrato: {path}"
            entry = paths[path]
            assert isinstance(entry, dict), f"path {path}: entrada inválida"
            methods_only = frozenset(k.lower() for k in entry if k.lower() in http_verbs)
            missing = expected_methods - methods_only
            assert not missing, f"{path}: faltam métodos {missing} (tem {methods_only})"
