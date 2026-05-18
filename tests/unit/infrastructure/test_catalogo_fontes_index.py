"""Testes do índice ``catalogo_fontes.yml``."""

from __future__ import annotations

from src.infrastructure.rag.catalogo_fontes_index import (
    carregar_entradas_catalogo,
    resolver_entrada_por_caminho,
)


class TestCatalogoFontesIndex:
    """Metadados do corpus piloto."""

    def test_carrega_fonte_prd(self) -> None:
        entradas = carregar_entradas_catalogo()
        assert any(e.id == "FONTE-020" for e in entradas)

    def test_resolve_docs_refs(self) -> None:
        ent = resolver_entrada_por_caminho("docs/refs/01_PRD_BASE.md")
        assert ent is not None
        assert ent.id == "FONTE-020"
        assert ent.classe == "B"
