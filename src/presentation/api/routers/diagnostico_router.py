"""
Rotas HTTP para o domínio de Diagnóstico.

Camada: Presentation
Responsabilidade: Roteamento HTTP, conversão Pydantic -> Domain.
"""

import asyncio
import json
import secrets
from datetime import UTC, datetime
from typing import Annotated, Any, cast
from uuid import UUID

import psycopg2
import structlog
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, status

from src.application.errors import ConflitoVersaoOtimistaError, DiagnosticoNaoEncontradoError
from src.application.ports.email_service import EmailServicePort
from src.application.use_cases.anexar_relatorio_otimista import (
    AnexarRelatorioOtimista,
    ComandoAnexarRelatorioOtimista,
)
from src.application.use_cases.atualizar_checklist_m12_autoconf import (
    AtualizarChecklistM12Autoconf,
    ComandoAtualizarChecklistM12Autoconf,
)
from src.application.use_cases.atualizar_quadro_implantacao import (
    AtualizarQuadroImplantacao,
    ComandoAtualizarQuadroImplantacao,
)
from src.application.use_cases.gerar_questionario_adaptativo import (
    GerarQuestionarioAdaptativoUseCase,
)
from src.application.use_cases.realizar_diagnostico import (
    ComandoRealizarDiagnostico,
    EntradaRespostaDiagnostico,
    RealizarDiagnostico,
)
from src.application.use_cases.vincular_diagnosticos_lead_self_service import (
    ComandoVincularDiagnosticosLeadSelfService,
    VincularDiagnosticosLeadSelfService,
)
from src.domain.entities.diagnostico import Diagnostico, EmpresaInfo, Respondente
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.domain.value_objects.score import ScoreCompleto
from src.infrastructure.auth.postgres_admin_login import buscar_email_admin_por_id_e_tenant_postgres
from src.infrastructure.config.settings import get_settings
from src.infrastructure.email_verificacao import codigo_store
from src.infrastructure.questionario.banco_cache import (
    get_banco_perguntas_cached,
    versao_catalogo_lida,
)
from src.infrastructure.repositories.postgres_diagnostico_leitura_publica_self_service import (
    buscar_diagnostico_conclusao_publica_sync,
    inserir_leitura_publica_self_service_sync,
)
from src.infrastructure.repositories.postgres_rascunho_self_service import (
    buscar_rascunho_ativo_por_token_sync,
    inserir_rascunho_sync,
    marcar_rascunho_consumido_sync,
)
from src.presentation.api.dependencies import (
    get_anexar_relatorio_otimista_use_case,
    get_atualizar_checklist_m12_autoconf_use_case,
    get_atualizar_quadro_implantacao_use_case,
    get_current_user_tenant,
    get_diagnostico_repository,
    get_email_service,
    get_gerar_questionario_adaptativo_use_case,
    get_realizar_diagnostico_use_case,
    get_self_service_diagnostico_claims,
    get_vincular_diagnosticos_lead_self_service_use_case,
    perfil_empresa_para_questionario,
    pesos_macro_dimensao_iso_para_http,
)
from src.presentation.api.openapi_examples import OPENAPI_EXAMPLES_POST_DIAGNOSTICO
from src.presentation.api.schemas import (
    ConcluirRascunhoDiagnosticoSelfServiceRequest,
    DiagnosticoConclusaoPublicaDimensaoSchema,
    DiagnosticoConclusaoSelfServicePublicoResponse,
    DiagnosticoRascunhoResumoResponse,
    DiagnosticoResponse,
    DiagnosticoResumoSchema,
    IniciarDiagnosticoRequest,
    ManifestoPesoPerguntaSchema,
    ManifestoPesosResponse,
    MetodologiaResponse,
    PatchChecklistM12AutoconfRequest,
    PatchQuadroImplantacaoRequest,
    PatchRelatorioPdfRequest,
    QuestionarioDisponivelResponse,
    QuestionarioPerguntaItemSchema,
    RascunhoDiagnosticoSelfServiceResponse,
    ScoreCompletoSchema,
    ScoreDimensaoSchema,
    VincularLeadsSelfServiceResponse,
    VincularRascunhoContaPlataformaRequest,
)

router = APIRouter(prefix="/diagnosticos", tags=["Diagnósticos"])

logger = structlog.get_logger(__name__)

_VALIDADE_OTP_MINUTOS = 10


def _payload_json_como_dict(value: object) -> dict[str, Any] | None:
    """jsonb via psycopg2 costuma vir como dict; em alguns drivers/versões pode vir como str JSON."""
    if value is None:
        return None
    if isinstance(value, dict):
        return cast("dict[str, Any]", value)
    if isinstance(value, str):
        try:
            parsed: object = json.loads(value)
        except json.JSONDecodeError:
            return None
        return cast("dict[str, Any]", parsed) if isinstance(parsed, dict) else None
    return None


def _mascarar_email_norm(email_norm: str) -> str:
    """Exibe domínio completo e ofusca o local-part (LGPD / UX)."""
    if "@" not in email_norm:
        return "***"
    local, _, dom = email_norm.partition("@")
    if len(local) <= 1:
        return f"*@{dom}"
    return f"{local[0]}***@{dom}"


async def _enviar_otp_verificacao_para_email(
    email_norm: str,
    email_service: EmailServicePort,
) -> str:
    """Gera OTP, envia via SMTP e regista em ``codigo_store`` (paridade com /auth/verificar-email/solicitar)."""
    settings = get_settings()
    if not codigo_store.pode_reenviar(email_norm):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Aguarde alguns segundos antes de pedir novo código.",
        )
    codigo = f"{secrets.randbelow(1_000_000):06d}"
    ok = await email_service.enviar_codigo_verificacao_email(
        email_norm, codigo, _VALIDADE_OTP_MINUTOS
    )
    if settings.app_env == "development":
        logger.info(
            "email_verificacao_codigo_dev_rascunho",
            email=email_norm,
            codigo=codigo,
            smtp_ok=ok,
        )
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Não foi possível enviar o e-mail. Se a API roda no Docker: confira se o serviço "
                "mailpit está no ar (make dev) e SMTP_HOST=mailpit. No host: Mailpit em "
                "127.0.0.1:1025 e SMTP_HOST=127.0.0.1. Mensagens de dev: http://127.0.0.1:8025 ."
            ),
        )
    codigo_store.registrar_envio(email_norm, codigo)
    return f"Código enviado. Válido por {_VALIDADE_OTP_MINUTOS} minutos."


def _plano_efetivo_para_criacao(
    payload: IniciarDiagnosticoRequest, perfil_limite: str | None
) -> str:
    """
    Define o plano persistido conforme o perfil da conta (JWT), não confiando só no corpo HTTP.

    - Self-service (`perfil_limite` None): sempre gratuito (lead / OTP).
    - Conta `gratuito`: sempre gratuito.
    - Conta `avancado`: aceita `gratuito` ou `avancado` declarado no payload.
    """
    raw = (payload.plano or "gratuito").strip().lower()
    if raw not in ("gratuito", "avancado"):
        raw = "gratuito"
    if perfil_limite is None:
        return "gratuito"
    if perfil_limite == "gratuito":
        return "gratuito"
    return raw


def _campos_auditoria_http(entity: object) -> tuple[str | None, int | None]:
    """Extrai hash/versão apenas se tipos forem válidos (evita MagicMock nos testes unitários)."""
    raw_h = getattr(entity, "hash_evidencia", None)
    hash_out: str | None = raw_h if isinstance(raw_h, str) else None
    raw_v = getattr(entity, "versao_otimista", None)
    versao_out: int | None = raw_v if isinstance(raw_v, int) else None
    return hash_out, versao_out


def _parse_if_match_versao(raw: str | None) -> int:
    """
    Interpreta If-Match como inteiro (versao_otimista).

    Aceita formas comuns: `3`, `"3"`, `W/"3"` (usa apenas o primeiro valor se houver lista).
    """
    if raw is None or not str(raw).strip():
        raise ValueError('Header If-Match obrigatório com a versão otimista atual (ex.: 1 ou "1").')
    s = str(raw).strip()
    if "," in s:
        s = s.split(",", 1)[0].strip()
    if s.upper().startswith("W/"):
        s = s[2:].strip()
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        s = s[1:-1]
    try:
        v = int(s)
    except ValueError as e:
        raise ValueError("If-Match deve ser um inteiro (versão otimista).") from e
    if v < 1:
        raise ValueError("Versão otimista inválida.")
    return v


def _quadro_implantacao_para_http(diagnostico: Diagnostico) -> dict[str, dict[str, str]] | None:
    raw = getattr(diagnostico, "quadro_implantacao_anotacoes", None)
    if not raw:
        return None
    return {str(k): dict(v) for k, v in raw.items()}


def _checklist_m12_para_http(diagnostico: Diagnostico) -> list[bool] | None:
    """Extrai lista persistida para o contrato HTTP (evita `MagicMock` nos testes)."""
    raw = getattr(diagnostico, "checklist_m12_estado", None)
    if not isinstance(raw, list) or len(raw) != 10:
        return None
    if not all(isinstance(x, bool) for x in raw):
        return None
    return list(raw)


def _aceite_lgpd_para_http(diagnostico: Diagnostico) -> datetime | None:
    """Instante do aceite LGPD persistido (somente `datetime` real)."""
    raw = getattr(diagnostico, "aceite_termos_privacidade_em", None)
    return raw if isinstance(raw, datetime) else None


def _para_resumo(diagnostico: Diagnostico) -> DiagnosticoResumoSchema:
    """Monta linha da listagem do painel (P7 — sem recomputar checklist/matriz)."""
    return DiagnosticoResumoSchema(
        id=diagnostico.id,
        empresa_razao_social=diagnostico.empresa.razao_social,
        status=diagnostico.status.value,
        plano=diagnostico.plano.value,
        score_geral=diagnostico.score_geral,
        criado_em=diagnostico.criado_em,
        finalizado_em=diagnostico.finalizado_em,
        relatorio_pdf_url=diagnostico.relatorio_pdf_url,
    )


def _montar_diagnostico_response(diagnostico: Diagnostico) -> DiagnosticoResponse:
    """Monta o payload HTTP canônico (checklist/matriz derivados do domínio)."""
    from dataclasses import asdict

    from src.application.services.consultoria_service import ConsultoriaService

    snap_chk = getattr(diagnostico, "score_completo_snapshot", None)
    checklist_entities = ConsultoriaService.gerar_checklist(
        diagnostico,
        snap_chk if isinstance(snap_chk, ScoreCompleto) else None,
    )
    matriz_entities = ConsultoriaService.gerar_matriz_impacto(diagnostico)
    cronograma_data = ConsultoriaService.gerar_cronograma_cinco_fases()
    checklist_data = [asdict(f) for f in checklist_entities]
    matriz_data = [asdict(m) for m in matriz_entities]
    h_aud, v_aud = _campos_auditoria_http(diagnostico)
    return DiagnosticoResponse(
        id=diagnostico.id,
        status=diagnostico.status.value,
        plano=diagnostico.plano.value,
        empresa_razao_social=diagnostico.empresa.razao_social,
        empresa_faixa_faturamento=(
            diagnostico.empresa.faixa_faturamento.value
            if diagnostico.empresa.faixa_faturamento is not None
            else None
        ),
        locale_relatorio=getattr(diagnostico, "locale_relatorio", "pt-BR"),
        score=_score_completo_para_http(diagnostico),
        relatorio_pdf_url=diagnostico.relatorio_pdf_url,
        recomendacao_ia=None,
        checklist=checklist_data,
        matriz_impacto=matriz_data,
        cronograma=cronograma_data,
        checklist_m12_autoconf=_checklist_m12_para_http(diagnostico),
        quadro_implantacao_anotacoes=_quadro_implantacao_para_http(diagnostico),
        aceite_termos_privacidade_em=_aceite_lgpd_para_http(diagnostico),
        hash_evidencia=h_aud,
        versao_otimista=v_aud,
    )


def _score_completo_para_http(diagnostico: Diagnostico) -> ScoreCompletoSchema | None:
    """Monta o schema HTTP a partir do snapshot persistido (JSONB), se existir."""
    snap = getattr(diagnostico, "score_completo_snapshot", None)
    if snap is None or not isinstance(snap, ScoreCompleto):
        return None
    return ScoreCompletoSchema(
        score_geral=ScoreDimensaoSchema(
            valor=snap.score_geral.valor,
            peso_total_aplicado=snap.score_geral.peso_total_aplicado,
        ),
        score_por_dimensao={
            dim.value: ScoreDimensaoSchema(
                valor=sn.valor, peso_total_aplicado=sn.peso_total_aplicado
            )
            for dim, sn in snap.score_por_dimensao.items()
        },
    )


def _conclusao_publica_row_para_schema(
    row: dict[str, Any],
) -> DiagnosticoConclusaoSelfServicePublicoResponse:
    """Monta resposta pública a partir da linha ``diagnosticos`` (JSONB ``score_completo``)."""
    sc_raw = row.get("score_completo")
    score_geral: float | None = None
    items: list[DiagnosticoConclusaoPublicaDimensaoSchema] = []
    if isinstance(sc_raw, dict):
        try:
            snap = ScoreCompleto.desde_dict(sc_raw)
            score_geral = snap.score_geral.valor
            for dim, sn in snap.score_por_dimensao.items():
                items.append(
                    DiagnosticoConclusaoPublicaDimensaoSchema(
                        dimensao=dim.value,
                        valor=sn.valor,
                        peso_total_aplicado=sn.peso_total_aplicado,
                    )
                )
        except (KeyError, TypeError, ValueError):
            pass
    loc_raw = row.get("locale_relatorio")
    loc = str(loc_raw).strip() if loc_raw is not None else "pt-BR"
    if not loc:
        loc = "pt-BR"
    return DiagnosticoConclusaoSelfServicePublicoResponse(
        id=UUID(str(row["id"])),
        status=str(row["status"]),
        empresa_razao_social=str(row["empresa_razao_social"]),
        locale_relatorio=loc,
        score_geral=score_geral,
        scores_por_dimensao=items,
    )


async def _executar_criar_diagnostico_core(
    *,
    tenant_id: UUID,
    payload: IniciarDiagnosticoRequest,
    use_case: RealizarDiagnostico,
    perfil_limite: str | None,
) -> DiagnosticoResponse:
    """Núcleo compartilhado entre POST com conta na plataforma e POST self-service (JWT após OTP)."""
    empresa_domain = EmpresaInfo(
        cnpj=payload.empresa.cnpj,
        razao_social=payload.empresa.razao_social,
        porte=payload.empresa.porte,
        regime=payload.empresa.regime,
        cnae_principal=payload.empresa.cnae_principal,
        uf=payload.empresa.uf,
        setor_macro=payload.empresa.setor_macro,
        faixa_faturamento=payload.empresa.faixa_faturamento,
    )

    respondente_domain = Respondente(
        email=payload.respondente.email,
        nome=payload.respondente.nome,
        cargo=payload.respondente.cargo,
        telefone=payload.respondente.telefone,
    )

    banco = get_banco_perguntas_cached()
    mapa_perguntas = {p.id: p for p in banco}

    entradas_resposta: list[EntradaRespostaDiagnostico] = []
    for resp_payload in payload.respostas:
        pergunta = mapa_perguntas.get(resp_payload.pergunta_id)
        if not pergunta:
            raise HTTPException(
                status_code=400, detail=f"Pergunta não encontrada: {resp_payload.pergunta_id}"
            )
        entradas_resposta.append(
            EntradaRespostaDiagnostico(pergunta=pergunta, valor_bruto=resp_payload.valor)
        )

    plano_efetivo = _plano_efetivo_para_criacao(payload, perfil_limite)

    comando = ComandoRealizarDiagnostico(
        tenant_id=tenant_id,
        empresa=empresa_domain,
        respondente=respondente_domain,
        entradas_resposta=entradas_resposta,
        plano=plano_efetivo,
        aceite_termos_privacidade=payload.aceite_termos_privacidade,
        locale_relatorio=payload.locale_relatorio,
    )

    try:
        resultado = await use_case.execute(comando)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    score_por_dimensao_schema = {
        dim.value: ScoreDimensaoSchema(valor=sn.valor, peso_total_aplicado=sn.peso_total_aplicado)
        for dim, sn in resultado.score.score_por_dimensao.items()
    }

    score_completo_schema = ScoreCompletoSchema(
        score_geral=ScoreDimensaoSchema(
            valor=resultado.score.score_geral.valor,
            peso_total_aplicado=resultado.score.score_geral.peso_total_aplicado,
        ),
        score_por_dimensao=score_por_dimensao_schema,
    )

    d = resultado.diagnostico
    h_aud, v_aud = _campos_auditoria_http(d)
    return DiagnosticoResponse(
        id=d.id,
        status=d.status.value,
        plano=d.plano.value,
        empresa_razao_social=d.empresa.razao_social,
        empresa_faixa_faturamento=(
            d.empresa.faixa_faturamento.value if d.empresa.faixa_faturamento is not None else None
        ),
        locale_relatorio=getattr(d, "locale_relatorio", "pt-BR"),
        score=score_completo_schema,
        relatorio_pdf_url=resultado.relatorio_pdf_url,
        recomendacao_ia=resultado.recomendacao_ia,
        checklist=resultado.checklist,
        matriz_impacto=resultado.matriz_impacto,
        cronograma=resultado.cronograma,
        checklist_m12_autoconf=_checklist_m12_para_http(d),
        quadro_implantacao_anotacoes=_quadro_implantacao_para_http(d),
        aceite_termos_privacidade_em=_aceite_lgpd_para_http(d),
        hash_evidencia=h_aud,
        versao_otimista=v_aud,
    )


@router.get("/", response_model=list[DiagnosticoResumoSchema])
async def listar_diagnosticos(
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[DiagnosticoResumoSchema]:
    """Lista diagnósticos do tenant atual (ordenacao: mais recentes primeiro na camada repo/DB)."""
    _, tenant_id, _ = current
    rows = await repo.listar_por_tenant(tenant_id, limit=limit, offset=offset)
    return [_para_resumo(d) for d in rows]


@router.post(
    "/",
    response_model=DiagnosticoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar diagnóstico",
    description=(
        "Calcula o score e persiste o diagnóstico no tenant do JWT.\n\n"
        "**Headers obrigatórios:** `Authorization: Bearer <JWT>` (claim `tenant_id`) e "
        "`Idempotency-Key` (UUID v4 recomendado). Reexecução com a mesma chave devolve a mesma "
        "resposta 2xx em cache (middleware de idempotência).\n\n"
        "**Corpo:** incluir `aceite_termos_privacidade: true` (LGPD); o servidor persiste "
        "`aceite_termos_privacidade_em` (UTC) na linha do diagnóstico."
    ),
)
async def criar_diagnostico(
    payload: Annotated[
        IniciarDiagnosticoRequest,
        Body(openapi_examples=dict(OPENAPI_EXAMPLES_POST_DIAGNOSTICO)),
    ],
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[RealizarDiagnostico, Depends(get_realizar_diagnostico_use_case)],
) -> DiagnosticoResponse:
    """Inicia um novo diagnóstico e calcula o score com base nas respostas."""
    _, tenant_id, perfil_conta = current
    return await _executar_criar_diagnostico_core(
        tenant_id=tenant_id,
        payload=payload,
        use_case=use_case,
        perfil_limite=perfil_conta,
    )


@router.post(
    "/self-service",
    response_model=DiagnosticoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar diagnóstico (e-mail verificado por OTP)",
    description=(
        "Fluxo: POST /auth/verificar-email/solicitar → POST /auth/self-service/token → este endpoint.\n\n"
        "**Bearer:** JWT self-service (claim `scope=self_service_diagnostico`).\n"
        "**Corpo:** mesmo contrato de POST /diagnosticos/. O e-mail do respondente deve coincidir com o OTP.\n"
        "**Idempotency-Key:** obrigatório."
    ),
)
async def criar_diagnostico_self_service(
    payload: Annotated[
        IniciarDiagnosticoRequest,
        Body(openapi_examples=dict(OPENAPI_EXAMPLES_POST_DIAGNOSTICO)),
    ],
    claims: Annotated[tuple[UUID, UUID, str], Depends(get_self_service_diagnostico_claims)],
    use_case: Annotated[RealizarDiagnostico, Depends(get_realizar_diagnostico_use_case)],
) -> DiagnosticoResponse:
    """Persiste diagnóstico no tenant self-service (verificação de posse do e-mail)."""
    _sub, tenant_id, email_norm = claims
    payload_email = codigo_store.normalizar_email(str(payload.respondente.email))
    if payload_email != email_norm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O e-mail do respondente deve ser o mesmo confirmado por OTP.",
        )
    return await _executar_criar_diagnostico_core(
        tenant_id=tenant_id,
        payload=payload,
        use_case=use_case,
        perfil_limite=None,
    )


@router.post(
    "/rascunho-self-service",
    response_model=RascunhoDiagnosticoSelfServiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gravar rascunho do diagnóstico na base (antes do OTP)",
    description=(
        "Persiste o mesmo corpo de **POST /diagnosticos/self-service** na tabela de rascunhos e envia OTP. "
        "O cliente deve guardar apenas o **resgate_token** (fragmento de URL ou memória de curto prazo) — "
        "não usar o payload completo em sessionStorage como etapa final. "
        "**Idempotency-Key** obrigatório (middleware)."
    ),
)
async def criar_rascunho_diagnostico_self_service(
    payload: Annotated[
        IniciarDiagnosticoRequest,
        Body(openapi_examples=dict(OPENAPI_EXAMPLES_POST_DIAGNOSTICO)),
    ],
    email_service: Annotated[EmailServicePort, Depends(get_email_service)],
) -> RascunhoDiagnosticoSelfServiceResponse:
    """Grava JSON do assistente no Postgres (tenant self-service) e dispara verificação de e-mail."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rascunho indisponível: configure DATABASE_URL na API.",
        )
    tenant_ss = settings.self_service_tenant_id
    email_norm = codigo_store.normalizar_email(str(payload.respondente.email))
    payload_dict = payload.model_dump(mode="json")
    try:
        token_plain, expira_em = await asyncio.to_thread(
            inserir_rascunho_sync,
            dsn,
            tenant_id=tenant_ss,
            email_norm=email_norm,
            payload_dict=payload_dict,
        )
    except psycopg2.Error as e:
        logger.exception("rascunho_self_service_insert_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível gravar o rascunho no PostgreSQL.",
        ) from e

    mensagem = await _enviar_otp_verificacao_para_email(email_norm, email_service)
    return RascunhoDiagnosticoSelfServiceResponse(
        resgate_token=token_plain,
        mensagem=mensagem,
        expira_em=expira_em if expira_em.tzinfo else expira_em.replace(tzinfo=UTC),
    )


@router.get(
    "/rascunho-self-service/resumo",
    response_model=DiagnosticoRascunhoResumoResponse,
    summary="Resumo do rascunho (token opaco)",
    description=(
        "Metadados mínimos para a página de confirmação. **Header obrigatório:** "
        "`X-Rascunho-Token` com o valor devolvido por POST /diagnosticos/rascunho-self-service."
    ),
)
async def resumo_rascunho_diagnostico_self_service(
    x_rascunho_token: Annotated[str, Header(alias="X-Rascunho-Token")],
) -> DiagnosticoRascunhoResumoResponse:
    settings = get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Rascunho indisponível: configure DATABASE_URL na API.",
        )
    row = await asyncio.to_thread(
        buscar_rascunho_ativo_por_token_sync, dsn, x_rascunho_token.strip()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rascunho inválido, expirado ou já utilizado.",
        )
    pj = _payload_json_como_dict(row.get("payload_json"))
    if pj is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Formato de rascunho inconsistente.",
        )
    emp = pj.get("empresa")
    razao = (
        str(emp.get("razao_social", "")).strip() if isinstance(emp, dict) else ""
    ) or "(sem razão social)"
    email_norm = str(row.get("email_norm") or "").strip()
    exp_raw = row.get("expira_em")
    if exp_raw is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rascunho inválido, expirado ou já utilizado.",
        )
    exp_dt = (
        exp_raw
        if isinstance(exp_raw, datetime)
        else datetime.fromisoformat(str(exp_raw).replace("Z", "+00:00"))
    )
    if exp_dt.tzinfo is None:
        exp_dt = exp_dt.replace(tzinfo=UTC)
    return DiagnosticoRascunhoResumoResponse(
        empresa_razao_social=razao,
        email_mascarado=_mascarar_email_norm(email_norm),
        respondente_email=str(email_norm),
        expira_em=exp_dt,
    )


@router.post(
    "/rascunho-self-service/concluir",
    response_model=DiagnosticoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Concluir rascunho com OTP (grava diagnóstico final)",
    description=(
        "Valida o código enviado por e-mail, materializa **POST /diagnosticos/self-service** a partir "
        "do JSON guardado no rascunho e marca o rascunho como consumido. **Idempotency-Key** obrigatório."
    ),
)
async def concluir_rascunho_diagnostico_self_service(
    body: ConcluirRascunhoDiagnosticoSelfServiceRequest,
    use_case: Annotated[RealizarDiagnostico, Depends(get_realizar_diagnostico_use_case)],
) -> DiagnosticoResponse:
    settings = get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operação indisponível: configure DATABASE_URL na API.",
        )
    row = await asyncio.to_thread(
        buscar_rascunho_ativo_por_token_sync, dsn, body.resgate_token.strip()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rascunho inválido, expirado ou já utilizado.",
        )
    email_norm = str(row["email_norm"])
    codigo_limpo = body.codigo.strip().replace(" ", "")
    if not codigo_limpo.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código deve conter apenas números.",
        )
    if not codigo_store.validar_e_consumir(email_norm, codigo_limpo):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Código inválido ou expirado. Solicite um novo código.",
        )
    row2 = await asyncio.to_thread(
        buscar_rascunho_ativo_por_token_sync, dsn, body.resgate_token.strip()
    )
    if not row2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rascunho inválido, expirado ou já utilizado.",
        )
    pj = _payload_json_como_dict(row2.get("payload_json"))
    if pj is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Formato de rascunho inconsistente.",
        )
    payload = IniciarDiagnosticoRequest.model_validate(pj)
    if codigo_store.normalizar_email(str(payload.respondente.email)) != email_norm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inconsistência entre rascunho e respondente.",
        )
    tenant_ss = settings.self_service_tenant_id
    out = await _executar_criar_diagnostico_core(
        tenant_id=tenant_ss,
        payload=payload,
        use_case=use_case,
        perfil_limite=None,
    )
    try:
        await asyncio.to_thread(marcar_rascunho_consumido_sync, dsn, UUID(str(row2["id"])))
    except psycopg2.Error as e:
        logger.exception("rascunho_self_service_consumir_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Diagnóstico criado, mas falhou ao fechar o rascunho — contacte suporte.",
        ) from e
    try:
        leitura_plain = await asyncio.to_thread(
            inserir_leitura_publica_self_service_sync,
            dsn,
            out.id,
            tenant_ss,
        )
    except psycopg2.Error as e:
        logger.exception("leitura_publica_self_service_insert_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Diagnóstico gravado, mas falhou ao emitir token de visualização — contacte suporte.",
        ) from e
    return out.model_copy(update={"leitura_token": leitura_plain})


@router.post(
    "/rascunho-self-service/vincular-conta",
    response_model=DiagnosticoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Materializar rascunho no tenant da conta (JWT)",
    description=(
        "Exige **Bearer** da conta na plataforma. O e-mail do respondente no rascunho deve ser **igual** "
        "ao e-mail do admin (LGPD / prova de posse). **Idempotency-Key** obrigatório."
    ),
)
async def vincular_rascunho_conta_plataforma(
    body: VincularRascunhoContaPlataformaRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[RealizarDiagnostico, Depends(get_realizar_diagnostico_use_case)],
) -> DiagnosticoResponse:
    user_id, tenant_id, perfil_conta = current
    settings = get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operação indisponível: configure DATABASE_URL na API.",
        )
    row = await asyncio.to_thread(
        buscar_rascunho_ativo_por_token_sync, dsn, body.resgate_token.strip()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rascunho inválido, expirado ou já utilizado.",
        )
    try:
        email_admin = buscar_email_admin_por_id_e_tenant_postgres(user_id, tenant_id, dsn)
    except psycopg2.Error as e:
        logger.exception("vincular_rascunho_email_lookup_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível validar o consultor no PostgreSQL.",
        ) from e
    if not email_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token não corresponde a um consultor com e-mail resolvível.",
        )
    email_admin_norm = codigo_store.normalizar_email(email_admin)
    pj = _payload_json_como_dict(row.get("payload_json"))
    if pj is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Formato de rascunho inconsistente.",
        )
    payload = IniciarDiagnosticoRequest.model_validate(pj)
    email_resp = codigo_store.normalizar_email(str(payload.respondente.email))
    if email_resp != email_admin_norm:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="O e-mail do respondente no rascunho deve ser o mesmo da sua conta na plataforma.",
        )
    out = await _executar_criar_diagnostico_core(
        tenant_id=tenant_id,
        payload=payload,
        use_case=use_case,
        perfil_limite=perfil_conta,
    )
    try:
        await asyncio.to_thread(marcar_rascunho_consumido_sync, dsn, UUID(str(row["id"])))
    except psycopg2.Error as e:
        logger.exception("vincular_rascunho_consumir_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Diagnóstico criado, mas falhou ao fechar o rascunho — contacte suporte.",
        ) from e
    return out


@router.get(
    "/metodologia",
    response_model=MetodologiaResponse,
    summary="Metodologia e pesos macro do score geral",
    description=(
        "Endpoint **público** (sem JWT). Expõe `pesos_macro_dimensao_score_geral` usados na "
        "agregação do score 0-100 e texto metodológico. Detalhamento por pergunta: "
        "**GET /diagnosticos/manifesto-pesos**."
    ),
)
async def obter_metodologia(
    pesos_macro_iso: Annotated[dict[str, float], Depends(pesos_macro_dimensao_iso_para_http)],
) -> MetodologiaResponse:
    """Retorna os pesos macro e a metodologia do motor de cálculo (transparência M03)."""
    return MetodologiaResponse(
        versao_normativa="ABNT NBR 17301:2026",
        pesos_macro_dimensao_score_geral=pesos_macro_iso,
        nota_metodologica=(
            "O QualiDiagIQ produz um índice único de 0 a 100 — maturidade tributária frente à Reforma "
            "do Consumo (EC 132/2023, LC 214/2025), com âncora metodológica na ABNT NBR 17301:2026. "
            "Para cada dimensão avaliada, calculamos um resultado a partir das suas respostas ao "
            "questionário, usando os pesos individuais do catálogo (totalmente públicos no manifesto "
            "de perguntas). Em seguida, combinamos esses resultados dimensionais com pesos estratégicos "
            "macro — por exemplo, maior peso na dimensão fiscal, por concentrar exposição normativa e "
            "operacional na transição para CBS/IBS. O mesmo critério é aplicado a todos os diagnósticos "
            "na mesma versão do produto, permitindo comparabilidade e auditoria."
        ),
        recomendacoes_gaps_criticos=[
            "Dimensão fiscal com resultado baixo: priorize revisão de cadastros tributários, "
            "classificações e cenários CBS/IBS com apoio contábil ou consultoria especializada — "
            "pistas de trabalho, não substituem parecer jurídico.",
            "Dimensão tecnológica com resultado baixo: avalie integração entre ERP e registros fiscais "
            "e a robustez dos dados para sustentar o novo arcaboço — frequentemente gargalo em projetos "
            "de adequação.",
        ],
    )


@router.get(
    "/manifesto-pesos",
    response_model=ManifestoPesosResponse,
    summary="Manifesto público de pesos por pergunta",
    description=(
        "Catálogo completo com peso e dimensão por código de pergunta; inclui `versao_catalogo` "
        "e `pesos_macro_dimensao` aplicados ao score geral. **Público**, sem JWT — auditable "
        "(LC 214/2025, ABNT NBR 17301:2026)."
    ),
)
async def obter_manifesto_pesos(
    pesos_macro_iso: Annotated[dict[str, float], Depends(pesos_macro_dimensao_iso_para_http)],
) -> ManifestoPesosResponse:
    """
    Manifesto público de pesos (M03) — catálogo completo + macrodimensões do score geral.

    Endpoint público (sem JWT), coerente com transparência do motor.
    """
    banco = get_banco_perguntas_cached()
    itens = [
        ManifestoPesoPerguntaSchema(
            codigo=p.codigo,
            dimensao=p.dimensao.value,
            tipo=p.tipo.value,
            peso=p.peso,
            base_legal=p.base_legal,
            pilar_abnt=p.pilar_abnt,
        )
        for p in banco
    ]
    return ManifestoPesosResponse(
        versao_catalogo=versao_catalogo_lida(),
        pesos_macro_dimensao=pesos_macro_iso,
        perguntas=itens,
    )


@router.get("/questionario", response_model=QuestionarioDisponivelResponse)
async def obter_questionario_adaptativo(
    empresa: Annotated[EmpresaInfo, Depends(perfil_empresa_para_questionario)],
    use_case: Annotated[
        GerarQuestionarioAdaptativoUseCase,
        Depends(get_gerar_questionario_adaptativo_use_case),
    ],
) -> QuestionarioDisponivelResponse:
    """
    Lista perguntas aplicáveis ao perfil declarado (motor adaptativo).

    Endpoint **público** (sem JWT): catálogo filtrado não expõe dados de tenant.
    POST `/diagnosticos/` continua exigindo Bearer + Idempotency-Key.

    LC 214/2025 — transparência e previsibilidade na coleta de informações do contribuinte.
    """
    try:
        lista = use_case.execute(empresa)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    itens = [
        QuestionarioPerguntaItemSchema(
            id=p.id,
            codigo=p.codigo,
            texto=p.texto,
            tipo=p.tipo.value,
            peso=p.peso,
            dimensao=p.dimensao.value,
            base_legal=p.base_legal,
            multipla_total=p.multipla_total,
            opcoes=list(p.opcoes) if p.opcoes else None,
            rotulos_escala=list(p.rotulos_escala) if p.rotulos_escala else None,
            pilar_abnt=p.pilar_abnt,
        )
        for p in lista
    ]
    return QuestionarioDisponivelResponse(
        versao_catalogo=versao_catalogo_lida(),
        total=len(itens),
        perguntas=itens,
    )


@router.get(
    "/self-service/conclusao-visualizacao",
    response_model=DiagnosticoConclusaoSelfServicePublicoResponse,
    summary="Visualização pública do diagnóstico concluído (self-service)",
    description=(
        "Endpoint **público** (sem JWT). Exige ``diagnostico_id`` e ``leitura_token`` devolvidos por "
        "**POST /diagnosticos/rascunho-self-service/concluir** (token persistido em PostgreSQL, TTL ~7 dias). "
        "Não expõe checklist/PDF — apenas snapshot executivo alinhado à página de conclusão."
    ),
)
async def obter_conclusao_self_service_publica(
    diagnostico_id: Annotated[
        UUID, Query(description="UUID do diagnóstico gravado no tenant self-service.")
    ],
    leitura_token: Annotated[
        str,
        Query(
            min_length=16,
            description="Token opaco devolvido no campo `leitura_token` da resposta de concluir.",
        ),
    ],
) -> DiagnosticoConclusaoSelfServicePublicoResponse:
    """Lê diagnóstico da BD após validar o token de leitura (sem armazenamento no navegador como fonte)."""
    settings = get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operação indisponível: configure DATABASE_URL na API.",
        )
    tenant_ss = settings.self_service_tenant_id
    row = await asyncio.to_thread(
        buscar_diagnostico_conclusao_publica_sync,
        dsn,
        diagnostico_id=diagnostico_id,
        tenant_id_esperado=tenant_ss,
        token_plain=leitura_token.strip(),
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Diagnóstico não encontrado ou token inválido/expirado.",
        )
    return _conclusao_publica_row_para_schema(row)


@router.post(
    "/vincular-leads-self-service",
    response_model=VincularLeadsSelfServiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Vincular diagnósticos gratuitos (self-service) ao tenant da conta na plataforma",
    description=(
        "Reatribui ao tenant do JWT as linhas em `diagnosticos` gravadas no tenant self-service "
        "(fluxo OTP), com `respondente_email` igual ao e-mail do consultor em `admins` e plano gratuito. "
        "Resolve o caso em que o lead concluiu o assistente antes de iniciar sessão no painel. "
        "**Idempotency-Key** obrigatório (mesmo middleware dos outros POST sob `/diagnosticos/`)."
    ),
)
async def vincular_leads_self_service(
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        VincularDiagnosticosLeadSelfService,
        Depends(get_vincular_diagnosticos_lead_self_service_use_case),
    ],
) -> VincularLeadsSelfServiceResponse:
    """Move diagnósticos do pool OTP para o tenant do token (LGPD: e-mail conferido em `admins`)."""
    user_id, tenant_id, _perfil = current
    settings = get_settings()
    dsn = settings.sync_database_url
    if not dsn:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operação indisponível: configure DATABASE_URL na API para validar o consultor.",
        )
    try:
        email = buscar_email_admin_por_id_e_tenant_postgres(user_id, tenant_id, dsn)
    except psycopg2.Error as e:
        logger.exception("vincular_leads_email_lookup_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível validar o consultor no PostgreSQL.",
        ) from e
    if not email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token não corresponde a um consultor com e-mail resolvível para vinculação.",
        )
    comando = ComandoVincularDiagnosticosLeadSelfService(
        email_admin_normalizado=codigo_store.normalizar_email(email),
        tenant_destino=tenant_id,
        tenant_self_service=settings.self_service_tenant_id,
    )
    try:
        ids = await use_case.execute(comando)
    except psycopg2.Error as e:
        logger.exception("vincular_leads_update_falhou", erro=str(e))
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Não foi possível atualizar diagnósticos no PostgreSQL.",
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return VincularLeadsSelfServiceResponse(total_vinculados=len(ids), diagnostico_ids=ids)


@router.get("/{diagnostico_id}", response_model=DiagnosticoResponse)
async def obter_diagnostico(
    diagnostico_id: UUID,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> DiagnosticoResponse:
    """Busca um diagnóstico pelo ID, garantindo o isolamento do tenant."""
    _, tenant_id, _ = current
    diagnostico = await repo.buscar_por_id(diagnostico_id, tenant_id)
    if not diagnostico:
        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado")

    return _montar_diagnostico_response(diagnostico)


@router.patch(
    "/{diagnostico_id}/checklist-m12-autoconf",
    response_model=DiagnosticoResponse,
    summary="Atualizar autoconf ABNT M12",
    description=(
        "Persiste os 10 booleanos da autoconferência (ABNT NBR 17301). "
        "Exige diagnóstico **finalizado** e header **If-Match** com `versao_otimista` atual."
    ),
)
async def atualizar_checklist_m12_autoconf(
    diagnostico_id: UUID,
    payload: PatchChecklistM12AutoconfRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        AtualizarChecklistM12Autoconf,
        Depends(get_atualizar_checklist_m12_autoconf_use_case),
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> DiagnosticoResponse:
    """PATCH M12 — lock otimista alinhado ao PATCH de relatório PDF."""
    _, tenant_id, _ = current
    try:
        versao = _parse_if_match_versao(if_match)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    comando = ComandoAtualizarChecklistM12Autoconf(
        tenant_id=tenant_id,
        diagnostico_id=diagnostico_id,
        checklist_m12_autoconf=list(payload.checklist_m12_autoconf),
        versao_esperada=versao,
    )
    try:
        atualizado = await use_case.execute(comando)
    except DiagnosticoNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado") from None
    except ConflitoVersaoOtimistaError as e:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=str(e),
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return _montar_diagnostico_response(atualizado)


@router.patch(
    "/{diagnostico_id}/quadro-implantacao-anotacoes",
    response_model=DiagnosticoResponse,
    summary="Atualizar anotações do quadro de implantação",
    description=(
        "Persiste comentários e metas de prazo (YYYY-MM-DD) por ação sugerida do checklist derivado. "
        "Chaves: f{índice_frente}_a{índice_ação}. Exige diagnóstico **finalizado** e header **If-Match**."
    ),
)
async def atualizar_quadro_implantacao_anotacoes(
    diagnostico_id: UUID,
    payload: PatchQuadroImplantacaoRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        AtualizarQuadroImplantacao,
        Depends(get_atualizar_quadro_implantacao_use_case),
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> DiagnosticoResponse:
    """PATCH quadro — lock otimista (mesmo contrato do M12)."""
    _, tenant_id, _ = current
    try:
        versao = _parse_if_match_versao(if_match)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    blob = {
        k: {"comentario": v.comentario, "prazo_meta": v.prazo_meta}
        for k, v in payload.quadro_implantacao_anotacoes.items()
    }
    comando = ComandoAtualizarQuadroImplantacao(
        tenant_id=tenant_id,
        diagnostico_id=diagnostico_id,
        quadro_implantacao_anotacoes=blob,
        versao_esperada=versao,
    )
    try:
        atualizado = await use_case.execute(comando)
    except DiagnosticoNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado") from None
    except ConflitoVersaoOtimistaError as e:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=str(e),
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return _montar_diagnostico_response(atualizado)


@router.patch("/{diagnostico_id}", response_model=DiagnosticoResponse)
async def atualizar_relatorio_pdf(
    diagnostico_id: UUID,
    payload: PatchRelatorioPdfRequest,
    current: Annotated[tuple[UUID, UUID, str], Depends(get_current_user_tenant)],
    use_case: Annotated[
        AnexarRelatorioOtimista,
        Depends(get_anexar_relatorio_otimista_use_case),
    ],
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> DiagnosticoResponse:
    """
    Atualiza apenas `relatorio_pdf_url` em diagnóstico **finalizado**.

    Exige `If-Match` com a `versao_otimista` retornada no GET (lock otimista).
    """
    _, tenant_id, _ = current
    try:
        versao = _parse_if_match_versao(if_match)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    comando = ComandoAnexarRelatorioOtimista(
        tenant_id=tenant_id,
        diagnostico_id=diagnostico_id,
        relatorio_pdf_url=payload.relatorio_pdf_url,
        versao_esperada=versao,
    )
    try:
        atualizado = await use_case.execute(comando)
    except DiagnosticoNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Diagnóstico não encontrado") from None
    except ConflitoVersaoOtimistaError as e:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail=str(e),
        ) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return _montar_diagnostico_response(atualizado)
