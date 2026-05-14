"""
Factories FastAPI para LGPD (titular), export portável, retificações WORM e mutações do painel.

Camada: Presentation (FastAPI)

Extraído de ``dependencies.py`` (Onda 3 — LGPD + plano materializado / relatório).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from src.application.ports.diagnostico_mutacao_audit_port import DiagnosticoMutacaoAuditPort
from src.application.ports.diagnostico_retificacao_port import DiagnosticoRetificacaoPort
from src.application.ports.lead_diagnostico_vinculo_port import LeadDiagnosticoVinculoPort
from src.application.ports.lgpd_anonimizacao_executor_port import LgpdAnonimizacaoExecutorPort
from src.application.ports.lgpd_eliminacao_executor_port import LgpdEliminacaoExecutorPort
from src.application.ports.lgpd_titular_solicitacao_port import LgpdTitularSolicitacaoPort
from src.application.use_cases.anexar_relatorio_otimista import AnexarRelatorioOtimista
from src.application.use_cases.atualizar_checklist_m12_autoconf import AtualizarChecklistM12Autoconf
from src.application.use_cases.atualizar_quadro_implantacao import AtualizarQuadroImplantacao
from src.application.use_cases.atualizar_status_solicitacao_titular_lgpd import (
    AtualizarStatusSolicitacaoTitularLgpd,
)
from src.application.use_cases.executar_anonimizacao_respondente_lgpd import (
    ExecutarAnonimizacaoRespondenteLgpd,
)
from src.application.use_cases.executar_eliminacao_diagnostico_lgpd import (
    ExecutarEliminacaoDiagnosticoLgpd,
)
from src.application.use_cases.gerar_export_portabilidade_diagnostico import (
    GerarExportPortabilidadeDiagnostico,
)
from src.application.use_cases.listar_retificacoes_diagnostico import (
    ListarRetificacoesDiagnostico,
)
from src.application.use_cases.listar_solicitacao_titular_lgpd import (
    ListarSolicitacaoTitularLgpd,
)
from src.application.use_cases.plano_painel_subtarefa import (
    AtualizarSubtarefaPlanoDiagnostico,
    CriarSubtarefaPlanoDiagnostico,
)
from src.application.use_cases.registrar_retificacao_diagnostico import (
    RegistrarRetificacaoDiagnostico,
)
from src.application.use_cases.registrar_solicitacao_titular_lgpd import (
    RegistrarSolicitacaoTitularLgpd,
)
from src.application.use_cases.vincular_diagnosticos_lead_self_service import (
    VincularDiagnosticosLeadSelfService,
)
from src.domain.repositories.diagnostico_repository import DiagnosticoRepository
from src.presentation.api.deps_repositories_core import (
    get_diagnostico_mutacao_audit_port,
    get_diagnostico_repository,
    get_diagnostico_retificacao_port,
    get_lead_diagnostico_vinculo_port,
    get_lgpd_anonimizacao_executor_port,
    get_lgpd_eliminacao_executor_port,
    get_lgpd_titular_solicitacao_port,
)


def get_registrar_solicitacao_titular_lgpd_use_case(
    port: Annotated[
        LgpdTitularSolicitacaoPort,
        Depends(get_lgpd_titular_solicitacao_port),
    ],
) -> RegistrarSolicitacaoTitularLgpd:
    """POST de solicitação do titular (art. 18)."""
    return RegistrarSolicitacaoTitularLgpd(port=port)


def get_listar_solicitacao_titular_lgpd_use_case(
    port: Annotated[
        LgpdTitularSolicitacaoPort,
        Depends(get_lgpd_titular_solicitacao_port),
    ],
) -> ListarSolicitacaoTitularLgpd:
    """GET de solicitações do titular por tenant."""
    return ListarSolicitacaoTitularLgpd(port=port)


def get_atualizar_status_solicitacao_titular_lgpd_use_case(
    port: Annotated[
        LgpdTitularSolicitacaoPort,
        Depends(get_lgpd_titular_solicitacao_port),
    ],
) -> AtualizarStatusSolicitacaoTitularLgpd:
    """PATCH de status operacional de solicitação LGPD."""
    return AtualizarStatusSolicitacaoTitularLgpd(port=port)


def get_executar_anonimizacao_respondente_lgpd_use_case(
    port: Annotated[
        LgpdTitularSolicitacaoPort,
        Depends(get_lgpd_titular_solicitacao_port),
    ],
    executor: Annotated[
        LgpdAnonimizacaoExecutorPort,
        Depends(get_lgpd_anonimizacao_executor_port),
    ],
) -> ExecutarAnonimizacaoRespondenteLgpd:
    """Fluxo técnico pós-deferimento (solicitação tipo anonimizacao)."""
    return ExecutarAnonimizacaoRespondenteLgpd(port_solicitacoes=port, executor=executor)


def get_executar_eliminacao_diagnostico_lgpd_use_case(
    port: Annotated[
        LgpdTitularSolicitacaoPort,
        Depends(get_lgpd_titular_solicitacao_port),
    ],
    executor: Annotated[
        LgpdEliminacaoExecutorPort,
        Depends(get_lgpd_eliminacao_executor_port),
    ],
) -> ExecutarEliminacaoDiagnosticoLgpd:
    """Fluxo técnico pós-deferimento (solicitação tipo eliminacao)."""
    return ExecutarEliminacaoDiagnosticoLgpd(port_solicitacoes=port, executor=executor)


def get_gerar_export_portabilidade_diagnostico_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    lgpd: Annotated[LgpdTitularSolicitacaoPort, Depends(get_lgpd_titular_solicitacao_port)],
) -> GerarExportPortabilidadeDiagnostico:
    """Export JSON (+ PDF com anexo) após solicitação LGPD deferida."""
    from src.infrastructure.exportacao.validador_export_diagnostico_v1 import (
        validar_payload_export_diagnostico_v1,
    )
    from src.infrastructure.pdf.portabilidade_pdf_anexo import (
        gerar_pdf_portabilidade_com_json_embebido,
    )

    return GerarExportPortabilidadeDiagnostico(
        diagnostico_repository=repo,
        solicitacoes=lgpd,
        validar_payload_export_v1=validar_payload_export_diagnostico_v1,
        gerar_pdf_com_anexo_json=lambda jb, did, tid: gerar_pdf_portabilidade_com_json_embebido(
            json_bytes=jb,
            diagnostico_id=did,
            tenant_id=tid,
        ),
    )


def get_registrar_retificacao_diagnostico_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    ret: Annotated[DiagnosticoRetificacaoPort, Depends(get_diagnostico_retificacao_port)],
) -> RegistrarRetificacaoDiagnostico:
    """Regista retificação na cadeia WORM (sem alterar diagnóstico original)."""
    return RegistrarRetificacaoDiagnostico(diagnostico_repository=repo, retificacao=ret)


def get_listar_retificacoes_diagnostico_use_case(
    ret: Annotated[DiagnosticoRetificacaoPort, Depends(get_diagnostico_retificacao_port)],
) -> ListarRetificacoesDiagnostico:
    """Lista retificações do diagnóstico (mais recentes primeiro)."""
    return ListarRetificacoesDiagnostico(retificacao=ret)


def get_vincular_diagnosticos_lead_self_service_use_case(
    vinculo: Annotated[LeadDiagnosticoVinculoPort, Depends(get_lead_diagnostico_vinculo_port)],
) -> VincularDiagnosticosLeadSelfService:
    """Vincula diagnósticos gratuitos do pool OTP ao tenant do JWT."""
    return VincularDiagnosticosLeadSelfService(vinculo=vinculo)


def get_anexar_relatorio_otimista_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    mutacao_audit: Annotated[
        DiagnosticoMutacaoAuditPort,
        Depends(get_diagnostico_mutacao_audit_port),
    ],
) -> AnexarRelatorioOtimista:
    """PATCH de relatório com versão otimista."""
    return AnexarRelatorioOtimista(repo=repo, mutacao_audit=mutacao_audit)


def get_atualizar_checklist_m12_autoconf_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    mutacao_audit: Annotated[
        DiagnosticoMutacaoAuditPort,
        Depends(get_diagnostico_mutacao_audit_port),
    ],
) -> AtualizarChecklistM12Autoconf:
    """PATCH M12 (autoconf ABNT) com versão otimista."""
    return AtualizarChecklistM12Autoconf(repo=repo, mutacao_audit=mutacao_audit)


def get_atualizar_quadro_implantacao_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
    mutacao_audit: Annotated[
        DiagnosticoMutacaoAuditPort,
        Depends(get_diagnostico_mutacao_audit_port),
    ],
) -> AtualizarQuadroImplantacao:
    """PATCH quadro de implantação (comentários e prazos) com versão otimista."""
    return AtualizarQuadroImplantacao(repo=repo, mutacao_audit=mutacao_audit)


def get_criar_subtarefa_plano_diagnostico_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> CriarSubtarefaPlanoDiagnostico:
    """POST subtarefa do plano materializado."""
    return CriarSubtarefaPlanoDiagnostico(repo=repo)


def get_atualizar_subtarefa_plano_diagnostico_use_case(
    repo: Annotated[DiagnosticoRepository, Depends(get_diagnostico_repository)],
) -> AtualizarSubtarefaPlanoDiagnostico:
    """PATCH subtarefa do plano materializado."""
    return AtualizarSubtarefaPlanoDiagnostico(repo=repo)
