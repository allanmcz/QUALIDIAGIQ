"""Rotas HTTP — consulta CNPJ (referência cadastral com cache TTL triplo).

Camada: Presentation
Autenticação: JWT painel ou fluxos que injetam ``get_current_user_tenant``.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID  # noqa: TC003

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from src.application.use_cases.consultar_cnpj import ComandoConsultarCnpj, ConsultarCnpjUseCase
from src.presentation.api.dependencies import get_consultar_cnpj_use_case, get_current_user_tenant
from src.presentation.api.schemas import (
    CnpjCanonicoResponse,
    ConsultarCnpjRequest,
    ConsultarCnpjResponse,
)

router = APIRouter(prefix="/referencia/cnpj", tags=["Referência CNPJ"])


def _opt_str(val: object | None) -> str | None:
    """Normaliza valores JSONB heterogéneos para campo opcional da resposta."""
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _canonico_schema(raw: dict[str, object]) -> CnpjCanonicoResponse:
    return CnpjCanonicoResponse(
        cnpj=str(raw.get("cnpj") or ""),
        razao_social=_opt_str(raw.get("razao_social")),
        nome_fantasia=_opt_str(raw.get("nome_fantasia")),
        cnae_principal=_opt_str(raw.get("cnae_principal")),
        uf=_opt_str(raw.get("uf")),
        situacao_cadastral=_opt_str(raw.get("situacao_cadastral")),
        porte=_opt_str(raw.get("porte")),
        regime=_opt_str(raw.get("regime")),
        setor_macro=_opt_str(raw.get("setor_macro")),
        municipio=_opt_str(raw.get("municipio")),
        logradouro=_opt_str(raw.get("logradouro")),
    )


@router.post(
    "/consulta_cnpj",
    response_model=ConsultarCnpjResponse,
    summary="Consultar CNPJ (BrasilAPI + fallback Minha Receita)",
    description=(
        "Materializa snapshot em ``cnpj_consultas`` com TTL separados por volatilidade (env). "
        "Cache válido reutiliza payload sem chamar rede salvo quando ``force_refresh=false``. "
        "Fallback Minha Receita só após falha/timeout da BrasilAPI — não em HTTP 404.\n\n"
        "**Headers:** ``Authorization`` JWT + ``Idempotency-Key``.\n\n"
        "**Opcional:** ``aplicar_no_diagnostico_id`` mergeia em diagnóstico ``em_andamento`` apenas."
    ),
)
async def consultar_cnpj(
    request: Request,
    body: ConsultarCnpjRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[ConsultarCnpjUseCase, Depends(get_consultar_cnpj_use_case)],
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key")],
) -> ConsultarCnpjResponse:
    """Consulta cadastral com trilha auditável por tenant (multi-tenant por JWT)."""
    _, tenant_id, _perfil = current
    tid = getattr(request.state, "trace_id", None)
    trace_id = str(tid).strip() if tid else None
    raw_key = (idempotency_key or "").strip()
    if not raw_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Header Idempotency-Key obrigatório.",
        )
    cmd = ComandoConsultarCnpj(
        tenant_id=tenant_id,
        cnpj_14=body.cnpj,
        idempotency_key=raw_key[:128],
        force_refresh=body.force_refresh,
        aplicar_no_diagnostico_id=body.aplicar_no_diagnostico_id,
        trace_id=trace_id,
    )
    try:
        mat, aplicado = await use_case.executar_e_materializar(cmd)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e

    canon_raw = dict(mat.payload_canonico)
    return ConsultarCnpjResponse(
        consulta_id=mat.consulta_id,
        cnpj=mat.cnpj_14,
        fonte=mat.fonte,
        canonico=_canonico_schema(canon_raw),
        expira_cadastral_em=mat.expira_cadastral_at,
        expira_qualificacao_em=mat.expira_qualificacao_at,
        expira_situacao_em=mat.expira_situacao_at,
        aplicado_em_diagnostico_em_andamento=aplicado,
    )
