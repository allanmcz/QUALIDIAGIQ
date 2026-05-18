"""
Índice do ``catalogo_fontes.yml`` — resolução de caminhos para IDs FONTE-xxx.

Camada: Infrastructure (sem regra de negócio — só metadados de corpus).
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

_CATALOGO_REL = Path("dominio_fiscal") / "catalogo_fontes.yml"
_EXTRAIDO_DIR = Path("dominio_fiscal") / "extraido"


@dataclass(frozen=True, slots=True)
class EntradaCatalogoFonte:
    """Metadados mínimos de uma fonte catalogada."""

    id: str
    classe: str
    caminho: str
    titulo: str
    piloto: bool


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


@lru_cache(maxsize=1)
def carregar_entradas_catalogo() -> tuple[EntradaCatalogoFonte, ...]:
    """Carrega entradas do YAML (cache por processo)."""
    path = _repo_root() / _CATALOGO_REL
    if not path.is_file():
        return ()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    fontes = raw.get("fontes") if isinstance(raw, dict) else None
    if not isinstance(fontes, list):
        return ()
    out: list[EntradaCatalogoFonte] = []
    for item in fontes:
        if not isinstance(item, dict):
            continue
        fid = str(item.get("id") or "").strip()
        rel = str(item.get("caminho") or "").strip()
        if not fid or not rel:
            continue
        out.append(
            EntradaCatalogoFonte(
                id=fid,
                classe=str(item.get("classe") or "").strip().upper() or "B",
                caminho=rel.replace("\\", "/"),
                titulo=str(item.get("titulo") or fid).strip(),
                piloto=bool(item.get("piloto")),
            )
        )
    return tuple(out)


def indice_por_caminho() -> dict[str, EntradaCatalogoFonte]:
    """Mapa caminho relativo normalizado → entrada."""
    idx: dict[str, EntradaCatalogoFonte] = {}
    for ent in carregar_entradas_catalogo():
        idx[ent.caminho] = ent
    return idx


def resolver_entrada_por_caminho(caminho_relativo: str) -> EntradaCatalogoFonte | None:
    """Resolve ``docs/refs/...`` ou ``dominio_fiscal/...`` para metadados do catálogo."""
    chave = caminho_relativo.strip().replace("\\", "/")
    return indice_por_caminho().get(chave)


def caminho_extraido_markdown(fonte_id: str) -> Path:
    """Markdown normalizado após extração: ``dominio_fiscal/extraido/FONTE-xxx.md``."""
    return _repo_root() / _EXTRAIDO_DIR / f"{fonte_id}.md"


def caminho_ficheiro_ingestivel(entrada: EntradaCatalogoFonte) -> Path | None:
    """
    Caminho legível para chunking: extraído > original (.md/.txt).

    PDF/XLSX só entram após ``scripts/extrair_fontes_catalogo_rag.py``.
    """
    root = _repo_root()
    extraido = caminho_extraido_markdown(entrada.id)
    if extraido.is_file():
        return extraido
    bruto = root / entrada.caminho
    if bruto.is_file() and bruto.suffix.lower() in {".md", ".txt"}:
        return bruto
    return None


def listar_entradas_piloto_ingestiveis() -> list[tuple[EntradaCatalogoFonte, Path]]:
    """Entradas piloto com ficheiro disponível para índice/ingestão."""
    saida: list[tuple[EntradaCatalogoFonte, Path]] = []
    for ent in carregar_entradas_catalogo():
        if not ent.piloto:
            continue
        path = caminho_ficheiro_ingestivel(ent)
        if path is not None:
            saida.append((ent, path))
    return saida
