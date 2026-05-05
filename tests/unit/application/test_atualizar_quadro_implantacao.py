"""Testes do caso de uso AtualizarQuadroImplantacao."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.errors import ConflitoVersaoOtimistaError, DiagnosticoNaoEncontradoError
from src.application.ports.diagnostico_mutacao_audit_port import TipoMutacaoDiagnostico
from src.application.use_cases.atualizar_quadro_implantacao import (
    AtualizarQuadroImplantacao,
    ComandoAtualizarQuadroImplantacao,
)
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PlanoDiagnostico,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
    StatusDiagnostico,
)
from src.infrastructure.adapters.noop_diagnostico_mutacao_audit_adapter import (
    NoOpDiagnosticoMutacaoAuditAdapter,
)


def _empresa() -> EmpresaInfo:
    return EmpresaInfo(
        cnpj="12345678000195",
        razao_social="X",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="6201500",
        uf="SP",
        setor_macro=SetorMacro.SERVICOS,
    )


def _diag_finalizado() -> Diagnostico:
    return Diagnostico(
        tenant_id=uuid4(),
        empresa=_empresa(),
        respondente=Respondente(email="a@b.com", nome="N"),
        plano=PlanoDiagnostico.GRATUITO,
        status=StatusDiagnostico.FINALIZADO,
        score_geral=50.0,
    )


_NOOP_AUDIT = NoOpDiagnosticoMutacaoAuditAdapter()


@pytest.mark.asyncio
class TestAtualizarQuadroImplantacao:
    """Persistência com lock otimista (port mock)."""

    async def test_nao_encontrado(self) -> None:
        repo = MagicMock()
        repo.buscar_por_id = AsyncMock(return_value=None)
        uc = AtualizarQuadroImplantacao(repo=repo, mutacao_audit=_NOOP_AUDIT)
        cmd = ComandoAtualizarQuadroImplantacao(
            tenant_id=uuid4(),
            diagnostico_id=uuid4(),
            quadro_implantacao_anotacoes={"f0_a0": {"comentarios": ["x"], "prazo_meta": ""}},
            versao_esperada=1,
        )
        with pytest.raises(DiagnosticoNaoEncontradoError):
            await uc.execute(cmd)

    async def test_conflito_versao(self) -> None:
        d = _diag_finalizado()
        repo = MagicMock()
        repo.buscar_por_id = AsyncMock(return_value=d)
        repo.atualizar_quadro_implantacao_com_versao = AsyncMock(return_value=None)
        uc = AtualizarQuadroImplantacao(repo=repo, mutacao_audit=_NOOP_AUDIT)
        cmd = ComandoAtualizarQuadroImplantacao(
            tenant_id=d.tenant_id,
            diagnostico_id=d.id,
            quadro_implantacao_anotacoes={"f0_a0": {"comentarios": ["x"], "prazo_meta": ""}},
            versao_esperada=1,
        )
        with pytest.raises(ConflitoVersaoOtimistaError):
            await uc.execute(cmd)

    async def test_sucesso(self) -> None:
        d = _diag_finalizado()
        repo = MagicMock()
        repo.buscar_por_id = AsyncMock(return_value=d)
        repo.atualizar_quadro_implantacao_com_versao = AsyncMock(return_value=d)
        audit = AsyncMock()
        actor = uuid4()
        uc = AtualizarQuadroImplantacao(repo=repo, mutacao_audit=audit)
        blob = {"f0_a0": {"comentarios": ["Kickoff"], "prazo_meta": "2026-12-31"}}
        cmd = ComandoAtualizarQuadroImplantacao(
            tenant_id=d.tenant_id,
            diagnostico_id=d.id,
            quadro_implantacao_anotacoes=blob,
            versao_esperada=1,
            actor_user_id=actor,
        )
        out = await uc.execute(cmd)
        assert out is d
        repo.atualizar_quadro_implantacao_com_versao.assert_awaited_once()
        audit.registrar.assert_awaited_once()
        kw = audit.registrar.await_args.kwargs
        assert kw["tipo"] == TipoMutacaoDiagnostico.QUADRO_IMPLANTACAO
        assert kw["actor_user_id"] == actor

    async def test_merge_na_mesma_chave_preserva_descricao_quando_parcial_sem_campo(self) -> None:
        d = _diag_finalizado()
        d.quadro_implantacao_anotacoes = {
            "f0_a0": {
                "prazo_meta": "",
                "comentarios": ["a"],
                "descricao_personalizada": "Texto custom",
            },
        }
        repo = MagicMock()
        repo.buscar_por_id = AsyncMock(return_value=d)
        repo.atualizar_quadro_implantacao_com_versao = AsyncMock(return_value=d)
        uc = AtualizarQuadroImplantacao(repo=repo, mutacao_audit=_NOOP_AUDIT)
        await uc.execute(
            ComandoAtualizarQuadroImplantacao(
                tenant_id=d.tenant_id,
                diagnostico_id=d.id,
                quadro_implantacao_anotacoes={"f0_a0": {"comentarios": ["b"], "prazo_meta": ""}},
                versao_esperada=1,
            )
        )
        blob = repo.atualizar_quadro_implantacao_com_versao.call_args[0][2]
        assert blob["f0_a0"]["comentarios"] == ["b"]
        assert blob["f0_a0"]["descricao_personalizada"] == "Texto custom"

    async def test_merge_preserva_outras_chaves(self) -> None:
        d = _diag_finalizado()
        d.quadro_implantacao_anotacoes = {
            "f0_a0": {"prazo_meta": "", "comentarios": ["manter"]},
            "f0_a1": {"prazo_meta": "", "comentarios": ["outra"]},
        }
        repo = MagicMock()
        repo.buscar_por_id = AsyncMock(return_value=d)
        repo.atualizar_quadro_implantacao_com_versao = AsyncMock(return_value=d)
        uc = AtualizarQuadroImplantacao(repo=repo, mutacao_audit=_NOOP_AUDIT)
        cmd = ComandoAtualizarQuadroImplantacao(
            tenant_id=d.tenant_id,
            diagnostico_id=d.id,
            quadro_implantacao_anotacoes={
                "f0_a0": {"comentarios": ["atualizado"], "prazo_meta": ""},
            },
            versao_esperada=1,
        )
        await uc.execute(cmd)
        blob = repo.atualizar_quadro_implantacao_com_versao.call_args[0][2]
        assert blob["f0_a0"]["comentarios"] == ["atualizado"]
        assert blob["f0_a1"]["comentarios"] == ["outra"]

    async def test_rejeita_payload_quadro_vazio(self) -> None:
        d = _diag_finalizado()
        repo = MagicMock()
        repo.buscar_por_id = AsyncMock(return_value=d)
        uc = AtualizarQuadroImplantacao(repo=repo, mutacao_audit=_NOOP_AUDIT)
        with pytest.raises(ValueError, match="pelo menos"):
            await uc.execute(
                ComandoAtualizarQuadroImplantacao(
                    tenant_id=d.tenant_id,
                    diagnostico_id=d.id,
                    quadro_implantacao_anotacoes={},
                    versao_esperada=1,
                )
            )
        repo.atualizar_quadro_implantacao_com_versao.assert_not_called()

    async def test_rejeita_em_andamento(self) -> None:
        d = Diagnostico(
            tenant_id=uuid4(),
            empresa=_empresa(),
            respondente=Respondente(email="a@b.com", nome="N"),
            plano=PlanoDiagnostico.GRATUITO,
            status=StatusDiagnostico.EM_ANDAMENTO,
        )
        repo = MagicMock()
        repo.buscar_por_id = AsyncMock(return_value=d)
        uc = AtualizarQuadroImplantacao(repo=repo, mutacao_audit=_NOOP_AUDIT)
        cmd = ComandoAtualizarQuadroImplantacao(
            tenant_id=d.tenant_id,
            diagnostico_id=d.id,
            quadro_implantacao_anotacoes={"f0_a0": {"comentarios": ["x"], "prazo_meta": ""}},
            versao_esperada=1,
        )
        with pytest.raises(ValueError, match="finalizado"):
            await uc.execute(cmd)

    async def test_merge_quando_item_existente_nao_eh_dict_trata_como_vazio(self) -> None:
        d = _diag_finalizado()
        object.__setattr__(d, "quadro_implantacao_anotacoes", cast("Any", {"f0_a0": "lixo"}))
        repo = MagicMock()
        repo.buscar_por_id = AsyncMock(return_value=d)
        repo.atualizar_quadro_implantacao_com_versao = AsyncMock(return_value=d)
        uc = AtualizarQuadroImplantacao(repo=repo, mutacao_audit=_NOOP_AUDIT)
        await uc.execute(
            ComandoAtualizarQuadroImplantacao(
                tenant_id=d.tenant_id,
                diagnostico_id=d.id,
                quadro_implantacao_anotacoes={"f0_a0": {"comentarios": ["ok"], "prazo_meta": ""}},
                versao_esperada=1,
            )
        )
        blob = repo.atualizar_quadro_implantacao_com_versao.call_args[0][2]
        assert blob["f0_a0"]["comentarios"] == ["ok"]

    async def test_merge_parcial_nao_dict_trata_como_vazio(self) -> None:
        d = _diag_finalizado()
        repo = MagicMock()
        repo.buscar_por_id = AsyncMock(return_value=d)
        repo.atualizar_quadro_implantacao_com_versao = AsyncMock(return_value=d)
        uc = AtualizarQuadroImplantacao(repo=repo, mutacao_audit=_NOOP_AUDIT)
        cmd = ComandoAtualizarQuadroImplantacao(
            tenant_id=d.tenant_id,
            diagnostico_id=d.id,
            quadro_implantacao_anotacoes=cast("Any", {"f0_a0": "não-dict"}),
            versao_esperada=1,
        )
        await uc.execute(cmd)
        blob = repo.atualizar_quadro_implantacao_com_versao.call_args[0][2]
        assert blob["f0_a0"] == {}

    async def test_auditoria_falha_nao_impede_sucesso(self) -> None:
        d = _diag_finalizado()
        repo = MagicMock()
        repo.buscar_por_id = AsyncMock(return_value=d)
        repo.atualizar_quadro_implantacao_com_versao = AsyncMock(return_value=d)
        audit = AsyncMock()
        audit.registrar.side_effect = OSError("audit")
        uc = AtualizarQuadroImplantacao(repo=repo, mutacao_audit=audit)
        out = await uc.execute(
            ComandoAtualizarQuadroImplantacao(
                tenant_id=d.tenant_id,
                diagnostico_id=d.id,
                quadro_implantacao_anotacoes={"f0_a0": {"comentarios": ["x"], "prazo_meta": ""}},
                versao_esperada=1,
            )
        )
        assert out is d
        audit.registrar.assert_awaited_once()
