"""Testes — serialização canónica na rota CNPJ."""

from src.presentation.api.routers.cnpj_router import _canonico_schema


def test_canonico_schema_mapeia_campos() -> None:
    s = _canonico_schema(
        {
            "cnpj": "33014556000196",
            "razao_social": "ACME",
            "porte": "medio",
            "uf": "RJ",
        }
    )
    assert s.cnpj == "33014556000196"
    assert s.razao_social == "ACME"
    assert s.porte == "medio"
    assert s.nome_fantasia is None
