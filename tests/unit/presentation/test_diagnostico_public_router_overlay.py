"""Cobertura de helpers do manifesto público (overlay por pergunta)."""

from __future__ import annotations

from datetime import date

from src.domain.value_objects.normativa_pergunta_peso import PesoPerguntaNormativoVigente
from src.presentation.api.routers import diagnostico_public_router as pub


def test_peso_pergunta_overlay_para_schema_mapeia_vo() -> None:
    """Garante conversão VO → schema HTTP (transparência M03)."""
    meta = PesoPerguntaNormativoVigente(
        peso=9.0,
        vigencia_inicio=date(2026, 1, 1),
        vigencia_fim=date(2026, 12, 31),
        rotulo_versao="overlay-test",
    )
    dto = pub._peso_pergunta_overlay_para_schema(7.5, meta)
    assert dto.peso_catalogo_json == 7.5
    assert dto.peso_normativo_db == 9.0
    assert dto.vigencia_inicio == date(2026, 1, 1)
    assert dto.vigencia_fim == date(2026, 12, 31)
    assert dto.rotulo_versao == "overlay-test"
