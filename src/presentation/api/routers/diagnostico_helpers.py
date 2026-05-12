"""
Funções auxiliares compartilhadas dos routers de Diagnóstico.

Camada: Presentation
Responsabilidade: montagem de respostas HTTP, parsing de headers e núcleo de criação
de diagnóstico — **sem** registro de rotas (evita import circular com sub-routers).

Analogia: unit Delphi só com ``implementation`` de rotinas usadas por vários ``TWebActionItem``.
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime
from typing import Any, cast
from uuid import UUID

import structlog
from fastapi import HTTPException, Request, status

from src.application.ports.email_service import EmailServicePort
from src.application.services.consultoria_service import ConsultoriaService
from src.application.use_cases.realizar_diagnostico import (
    ComandoRealizarDiagnostico,
    EntradaRespostaDiagnostico,
    RealizarDiagnostico,
)
from src.domain.entities.diagnostico import Diagnostico, EmpresaInfo, Respondente
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.domain.value_objects.score import ScoreCompleto
from src.infrastructure.config.settings import get_settings
from src.infrastructure.email_verificacao import codigo_store
from src.infrastructure.questionario.banco_cache import get_banco_perguntas_cached
from src.presentation.api.schemas import (
    DiagnosticoConclusaoPublicaDimensaoSchema,
    DiagnosticoConclusaoSelfServicePublicoResponse,
    DiagnosticoResponse,
    DiagnosticoResumoSchema,
    IniciarDiagnosticoRequest,
    ScoreCompletoSchema,
    ScoreDimensaoSchema,
)

logger = structlog.get_logger(__name__)

_VALIDADE_OTP_MINUTOS = 10


def extrair_ip_cliente_http(request: Request) -> str | None:
    """
    Melhor esforço do IP observado na camada ASGI (proxies: primeiro hop de X-Forwarded-For).

    Trunca a 45 caracteres (IPv6 textual). Não substitui política de confiança no reverse proxy.
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        primeiro = xff.split(",")[0].strip()
        if primeiro:
            return primeiro[:45]
    client = request.client
    if client and client.host:
        return client.host[:45]
    return None


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


def _quadro_implantacao_para_http(diagnostico: Diagnostico) -> dict[str, dict[str, Any]] | None:
    raw = getattr(diagnostico, "quadro_implantacao_anotacoes", None)
    if not raw:
        return None
    return {str(k): dict(v) for k, v in raw.items()}


def _checklist_m12_para_http(diagnostico: Diagnostico) -> list[int] | None:
    """Extrai lista persistida Likert 1-5 para o contrato HTTP (evita `MagicMock` nos testes)."""
    raw = getattr(diagnostico, "checklist_m12_estado", None)
    if not isinstance(raw, list) or len(raw) != 10:
        return None
    if not all(isinstance(x, int) and 1 <= x <= 5 for x in raw):
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
        empresa_cnpj=diagnostico.empresa.cnpj,
        status=diagnostico.status.value,
        plano=diagnostico.plano.value,
        score_geral=diagnostico.score_geral,
        criado_em=diagnostico.criado_em,
        finalizado_em=diagnostico.finalizado_em,
        relatorio_pdf_url=diagnostico.relatorio_pdf_url,
    )


async def _montar_diagnostico_response(
    repo: DiagnosticoRepository,
    diagnostico: Diagnostico,
    *,
    recomendacao_ia: str | None = None,
) -> DiagnosticoResponse:
    """Monta o payload HTTP canônico — prioriza plano materializado na BD (fallback motor legado)."""
    from dataclasses import asdict

    blob = await repo.buscar_plano_painel_serializado(diagnostico.id, diagnostico.tenant_id)
    if blob is not None:
        checklist_data = list(blob.checklist)
        matriz_data = list(blob.matriz_impacto)
        cronograma_data = list(blob.cronograma)
        versao_plano = blob.versao_plano
    else:
        logger.info(
            "plano_painel_resposta_fallback_motor_legado",
            diagnostico_id=str(diagnostico.id),
            tenant_id=str(diagnostico.tenant_id),
            evento="plano_materializado_ausente",
        )
        snap_chk = getattr(diagnostico, "score_completo_snapshot", None)
        checklist_entities = ConsultoriaService.gerar_checklist(
            diagnostico,
            snap_chk if isinstance(snap_chk, ScoreCompleto) else None,
        )
        matriz_entities = ConsultoriaService.gerar_matriz_impacto(diagnostico)
        cronograma_data = ConsultoriaService.gerar_cronograma_cinco_fases()
        checklist_data = [asdict(f) for f in checklist_entities]
        matriz_data = [asdict(m) for m in matriz_entities]
        versao_plano = int(getattr(diagnostico, "versao_plano", 1) or 1)
    h_aud, v_aud = _campos_auditoria_http(diagnostico)
    return DiagnosticoResponse(
        id=diagnostico.id,
        status=diagnostico.status.value,
        plano=diagnostico.plano.value,
        empresa_razao_social=diagnostico.empresa.razao_social,
        empresa_cnpj=diagnostico.empresa.cnpj,
        criado_em=diagnostico.criado_em,
        finalizado_em=diagnostico.finalizado_em,
        empresa_faixa_faturamento=(
            diagnostico.empresa.faixa_faturamento.value
            if diagnostico.empresa.faixa_faturamento is not None
            else None
        ),
        locale_relatorio=getattr(diagnostico, "locale_relatorio", "pt-BR"),
        score=_score_completo_para_http(diagnostico),
        relatorio_pdf_url=diagnostico.relatorio_pdf_url,
        recomendacao_ia=recomendacao_ia,
        checklist=checklist_data,
        matriz_impacto=matriz_data,
        cronograma=cronograma_data,
        checklist_m12_autoconf=_checklist_m12_para_http(diagnostico),
        quadro_implantacao_anotacoes=_quadro_implantacao_para_http(diagnostico),
        aceite_termos_privacidade_em=_aceite_lgpd_para_http(diagnostico),
        hash_evidencia=h_aud,
        versao_otimista=v_aud,
        versao_plano=versao_plano,
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
    repo: DiagnosticoRepository,
    trace_id: str | None = None,
    respondente_ip_origem: str | None = None,
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
        ip_origem=respondente_ip_origem,
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
        force_refresh_cnpj=payload.force_refresh_cnpj,
        trace_id=trace_id,
    )

    try:
        resultado = await use_case.execute(comando)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return await _montar_diagnostico_response(
        repo, resultado.diagnostico, recomendacao_ia=resultado.recomendacao_ia
    )
