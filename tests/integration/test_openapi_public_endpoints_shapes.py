"""
Contratos JSON dos endpoints públicos usados por integradores (handoff §11 T1).

Camada: Integration — ASGI in-process, sem Postgres obrigatório para estes GET/POST.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from src.presentation.api.main import app


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


class TestOpenApiPublicEndpointShapes:
    """Valida shape mínimo estável para documentação e clientes gerados."""

    @pytest.mark.asyncio
    async def test_get_metodologia_shape(self, async_client: AsyncClient) -> None:
        r = await async_client.get("/diagnosticos/metodologia")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["versao_normativa"], str)
        macros = data["pesos_macro_dimensao_score_geral"]
        assert isinstance(macros, dict)
        for _k, v in macros.items():
            assert isinstance(v, (int, float))
        assert isinstance(data["nota_metodologica"], str)
        assert isinstance(data["recomendacoes_gaps_criticos"], list)
        assert all(isinstance(x, str) for x in data["recomendacoes_gaps_criticos"])

    @pytest.mark.asyncio
    async def test_get_manifesto_pesos_shape(self, async_client: AsyncClient) -> None:
        r = await async_client.get("/diagnosticos/manifesto-pesos")
        assert r.status_code == 200
        body = r.json()
        assert isinstance(body["versao_catalogo"], str)
        assert isinstance(body["formula_score_geral"], str)
        assert isinstance(body["nota_calibracao_m02"], str)
        pmd = body["pesos_macro_dimensao"]
        assert isinstance(pmd, dict)
        for _k, v in pmd.items():
            assert isinstance(v, (int, float))
        perguntas = body["perguntas"]
        assert isinstance(perguntas, list)
        assert len(perguntas) >= 1
        p0 = perguntas[0]
        for key in ("codigo", "dimensao", "tipo", "peso"):
            assert key in p0
        assert isinstance(p0["codigo"], str)
        assert isinstance(p0["peso"], (int, float))
        if p0.get("base_legal") is not None:
            assert isinstance(p0["base_legal"], str)

    @pytest.mark.asyncio
    async def test_post_normativa_validar_ancora_shape_positivo(
        self, async_client: AsyncClient
    ) -> None:
        r = await async_client.post(
            "/normativa/validar-ancora",
            json={"texto": "Conforme LC 214/2025 art. 5º."},
        )
        assert r.status_code == 200
        out = r.json()
        assert "valido" in out
        assert isinstance(out["valido"], bool)
        assert out["valido"] is True
        assert out.get("motivo_rejeicao") in (None, "")

    @pytest.mark.asyncio
    async def test_post_normativa_validar_ancora_shape_negativo(
        self, async_client: AsyncClient
    ) -> None:
        r = await async_client.post(
            "/normativa/validar-ancora",
            json={"texto": "Melhore a governanca sem citar norma."},
        )
        assert r.status_code == 200
        out = r.json()
        assert isinstance(out["valido"], bool)
        assert out["valido"] is False
        assert isinstance(out.get("motivo_rejeicao"), (str, type(None)))
        assert out.get("motivo_rejeicao")
