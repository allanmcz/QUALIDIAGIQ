"""Rotas HTTP — lookup CNAE 2.3 (referência global).

Camada: Presentation
Público (somente leitura): o wizard M01 pode ser preenchido sem login; o autocomplete não deve depender de JWT.
Rate limit: prefixo `/referencia/cnae` em ``PublicRateLimitMiddleware``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.application.use_cases.buscar_cnae_subclasses import BuscarCnaeSubclasses
from src.presentation.api.dependencies import get_buscar_cnae_subclasses_use_case
from src.presentation.api.schemas import CnaeBuscaResponse, CnaeSubclasseItemSchema

router = APIRouter(prefix="/referencia/cnae", tags=["Referência CNAE"])


@router.get(
    "/subclasses",
    response_model=CnaeBuscaResponse,
    summary="Buscar subclasses CNAE (autocomplete)",
    description=(
        "Consulta somente leitura em `qdi.cnae_subclasse` (CONCLA/IBGE). "
        "Não exige autenticação. Exige `DATABASE_URL` no backend. Base: Resolução CONCLA nº 02/2023."
    ),
)
async def buscar_subclasses_cnae(
    use_case: Annotated[BuscarCnaeSubclasses, Depends(get_buscar_cnae_subclasses_use_case)],
    q: Annotated[
        str,
        Query(min_length=2, max_length=120, description="Prefixo numérico ou trecho da descrição."),
    ],
    limite: Annotated[int, Query(ge=1, le=50, description="Máximo de linhas (default 20).")] = 20,
) -> CnaeBuscaResponse:
    """Autocomplete para o wizard (M01) — CNAE principal com 7 dígitos."""
    try:
        linhas = await use_case.execute(consulta=q, limite=limite)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e

    return CnaeBuscaResponse(
        itens=[
            CnaeSubclasseItemSchema(subclasse_id=r.subclasse_id, descricao=r.descricao)
            for r in linhas
        ]
    )
