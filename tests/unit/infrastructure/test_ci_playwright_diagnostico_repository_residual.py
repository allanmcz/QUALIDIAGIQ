"""Cobertura residual do repositório em memória CI Playwright (painel integrado)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest

from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
    StatusDiagnostico,
)
from src.domain.value_objects.plano_painel_serializado import PlanoPainelSerializado
from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico
from src.infrastructure.repositories.ci_playwright_diagnostico_repository import (
    _ID_LISTA_CI,
    _TENANT_PADRAO_CI,
    CiPlaywrightDiagnosticoRepository,
)


def _empresa() -> EmpresaInfo:
    return EmpresaInfo(
        cnpj="",
        razao_social="CI Playwright SA",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )


def _score() -> ScoreCompleto:
    return ScoreCompleto(
        score_geral=ScoreNumerico(valor=70.0, peso_total_aplicado=1.0),
        score_por_dimensao={Dimensao.FISCAL: ScoreNumerico(valor=70.0, peso_total_aplicado=1.0)},
    )


def _diag_finalizado(*, tid: UUID | None = None, criado: datetime | None = None) -> Diagnostico:
    d = Diagnostico(
        tenant_id=tid or _TENANT_PADRAO_CI,
        empresa=_empresa(),
        respondente=Respondente(email="x@y.com"),
        criado_em=criado or datetime(2026, 5, 10, 12, 0, tzinfo=UTC),
    )
    d.finalizar_e_registrar_evidencia(_score())
    return d


@pytest.mark.asyncio
class TestCiPlaywrightDiagnosticoRepositoryConsultas:
    async def test_buscar_por_id_outro_tenant_retorna_none(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        assert await repo.buscar_por_id(_ID_LISTA_CI, uuid4()) is None

    async def test_listar_respeita_limit_e_offset(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        d2 = _diag_finalizado(criado=datetime(2026, 5, 10, 15, 0, tzinfo=UTC))
        await repo.salvar(d2)
        lst = await repo.listar_por_tenant(_TENANT_PADRAO_CI, limit=1, offset=1)
        assert len(lst) == 1
        assert lst[0].id == _ID_LISTA_CI

    async def test_listar_filtra_por_empresa_cnpj(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        emp = EmpresaInfo(
            cnpj="12345678000195",
            razao_social="Filtrada LTDA",
            porte=PorteEmpresa.MICRO,
            regime=RegimeTributario.SIMPLES_NACIONAL,
            cnae_principal="1234567",
            uf="SP",
            setor_macro=SetorMacro.COMERCIO,
        )
        d = Diagnostico(
            tenant_id=_TENANT_PADRAO_CI,
            empresa=emp,
            respondente=Respondente(email="f@z.com"),
            criado_em=datetime(2026, 5, 11, 12, 0, tzinfo=UTC),
        )
        d.finalizar_e_registrar_evidencia(_score())
        await repo.salvar(d)
        lst_ok = await repo.listar_por_tenant(_TENANT_PADRAO_CI, empresa_cnpj="12345678000195")
        assert any(x.id == d.id for x in lst_ok)
        lst_other = await repo.listar_por_tenant(_TENANT_PADRAO_CI, empresa_cnpj="11222333000181")
        assert d.id not in {x.id for x in lst_other}


@pytest.mark.asyncio
class TestCiPlaywrightDiagnosticoRepositoryMutacoesVersao:
    async def test_atualizar_relatorio_pdf_falha_versao(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        out = await repo.atualizar_relatorio_pdf_com_versao(
            _ID_LISTA_CI, _TENANT_PADRAO_CI, "https://pdf", versao_esperada=99
        )
        assert out is None

    async def test_atualizar_relatorio_pdf_sucesso_incrementa_versao(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        out = await repo.atualizar_relatorio_pdf_com_versao(
            _ID_LISTA_CI, _TENANT_PADRAO_CI, "https://pdf/ci.pdf", versao_esperada=1
        )
        assert out is not None
        assert out.relatorio_pdf_url == "https://pdf/ci.pdf"
        assert out.versao_otimista == 2

    async def test_atualizar_checklist_m12_falha_e_sucesso(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        itens = [5] + [1] * 9
        assert (
            await repo.atualizar_checklist_m12_com_versao(
                _ID_LISTA_CI, _TENANT_PADRAO_CI, itens, versao_esperada=0
            )
            is None
        )
        row = await repo.buscar_por_id(_ID_LISTA_CI, _TENANT_PADRAO_CI)
        assert row is not None
        v = row.versao_otimista
        out = await repo.atualizar_checklist_m12_com_versao(
            _ID_LISTA_CI, _TENANT_PADRAO_CI, itens, versao_esperada=v
        )
        assert out is not None
        assert out.checklist_m12_estado == itens

    async def test_atualizar_quadro_implantacao_falha_e_sucesso(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        blob = {"f0_a0": {"prazo_meta": "", "comentarios": []}}
        assert (
            await repo.atualizar_quadro_implantacao_com_versao(
                _ID_LISTA_CI, _TENANT_PADRAO_CI, blob, versao_esperada=0
            )
            is None
        )
        row = await repo.buscar_por_id(_ID_LISTA_CI, _TENANT_PADRAO_CI)
        assert row is not None
        out = await repo.atualizar_quadro_implantacao_com_versao(
            _ID_LISTA_CI, _TENANT_PADRAO_CI, blob, versao_esperada=row.versao_otimista
        )
        assert out is not None
        assert out.quadro_implantacao_anotacoes is not None


@pytest.mark.asyncio
class TestCiPlaywrightDiagnosticoRepositoryPlano:
    async def test_buscar_plano_none_quando_inexistente(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        assert await repo.buscar_plano_painel_serializado(uuid4(), _TENANT_PADRAO_CI) is None

    async def test_salvar_e_materializar_e_buscar_merge_subtarefas(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        d = _diag_finalizado()
        sc = _score()
        plano = await repo.salvar_e_materializar_plano_painel(d, sc)
        assert plano.versao_plano >= 1
        pid_acao = None
        for frente in plano.checklist:
            for ac in frente.get("acoes", []):
                if isinstance(ac, dict) and isinstance(ac.get("plano_acao_id"), str):
                    pid_acao = UUID(ac["plano_acao_id"])
                    break
            if pid_acao:
                break
        assert pid_acao is not None
        await repo.inserir_subtarefa_plano(d.tenant_id, d.id, pid_acao, "Sub", ordem=1)
        out2 = await repo.buscar_plano_painel_serializado(d.id, d.tenant_id)
        assert out2 is not None
        encontrou = False
        for frente in out2.checklist:
            for ac in frente.get("acoes", []):
                if not isinstance(ac, dict):
                    continue
                subs = ac.get("subtarefas") or []
                if subs and subs[0].get("titulo") == "Sub":
                    encontrou = True
        assert encontrou

    async def test_materializar_backfill_early_exit_plano_existe(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        d = _diag_finalizado()
        await repo.salvar_e_materializar_plano_painel(d, _score())
        assert await repo.materializar_plano_painel_idempotente_backfill(d.id, d.tenant_id) is None

    async def test_materializar_backfill_sem_diagnostico(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        assert (
            await repo.materializar_plano_painel_idempotente_backfill(uuid4(), _TENANT_PADRAO_CI)
            is None
        )

    async def test_materializar_backfill_nao_finalizado(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        d = Diagnostico(
            tenant_id=_TENANT_PADRAO_CI,
            empresa=_empresa(),
            respondente=Respondente(email="aberta@y.com"),
            status=StatusDiagnostico.EM_ANDAMENTO,
        )
        await repo.salvar(d)
        assert await repo.materializar_plano_painel_idempotente_backfill(d.id, d.tenant_id) is None

    async def test_materializar_backfill_sem_score_snapshot(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        d = Diagnostico(
            tenant_id=_TENANT_PADRAO_CI,
            empresa=_empresa(),
            respondente=Respondente(email="sem@score.com"),
            status=StatusDiagnostico.FINALIZADO,
            score_geral=50.0,
            finalizado_em=datetime(2026, 1, 1, tzinfo=UTC),
        )
        await repo.salvar(d)
        assert await repo.materializar_plano_painel_idempotente_backfill(d.id, d.tenant_id) is None

    async def test_materializar_backfill_sucesso(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        d = _diag_finalizado()
        await repo.salvar(d)
        plano = await repo.materializar_plano_painel_idempotente_backfill(d.id, d.tenant_id)
        assert plano is not None
        assert plano.versao_plano >= 1


class TestCiPlaywrightMergeSubtarefas:
    def test_merge_ignora_acao_nao_dict_e_preserva_ids_invalidos(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        did, tid = uuid4(), uuid4()
        base = PlanoPainelSerializado(
            versao_plano=1,
            checklist=(
                {
                    "nome": "F",
                    "acoes": [
                        "ignorada_nao_dict",
                        {"x": 1},
                        {"plano_acao_id": "zz-invalido"},
                        {"plano_acao_id": 42},
                    ],
                },
            ),
            matriz_impacto=(),
            cronograma=(),
        )
        out = repo._merge_subtarefas_no_plano(base, did, tid)
        acoes = out.checklist[0]["acoes"]
        assert len(acoes) == 3
        assert acoes[0] == {"x": 1}
        assert acoes[1]["plano_acao_id"] == "zz-invalido"
        assert acoes[2]["plano_acao_id"] == 42

    def test_merge_injeta_subtarefas_para_plano_acao_id_uuid(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        did, tid = uuid4(), uuid4()
        aid = uuid4()
        repo._subs_por_chave[(did, tid, aid)] = [{"id": "s1", "titulo": "T"}]
        base = PlanoPainelSerializado(
            versao_plano=1,
            checklist=({"nome": "F", "acoes": [{"plano_acao_id": str(aid), "txt": "a"}]},),
            matriz_impacto=(),
            cronograma=(),
        )
        out = repo._merge_subtarefas_no_plano(base, did, tid)
        ac = out.checklist[0]["acoes"][0]
        assert ac["subtarefas"][0]["titulo"] == "T"


@pytest.mark.asyncio
class TestCiPlaywrightSubtarefas:
    async def test_atualizar_subtarefa_sem_campos_opcionais_cobre_ifs(self) -> None:
        """Todos os ``if campo is not None`` falsos — devolve cópia sem alterar campos."""
        repo = CiPlaywrightDiagnosticoRepository()
        d = _diag_finalizado()
        await repo.salvar(d)
        await repo.salvar_e_materializar_plano_painel(d, _score())
        plano = await repo.buscar_plano_painel_serializado(d.id, d.tenant_id)
        assert plano is not None
        pid_str = next(
            ac["plano_acao_id"]
            for frente in plano.checklist
            for ac in frente.get("acoes", [])
            if isinstance(ac, dict) and isinstance(ac.get("plano_acao_id"), str)
        )
        sub = await repo.inserir_subtarefa_plano(d.tenant_id, d.id, UUID(pid_str), "S", ordem=0)
        sid = UUID(sub["id"])
        out = await repo.atualizar_subtarefa_plano(d.tenant_id, d.id, sid)
        assert out is not None
        assert out["titulo"] == "S"

    async def test_atualizar_subtarefa_chave_mesmo_tenant_lista_vazia_depois_acerta(self) -> None:
        """Laço interno sem match (lista vazia) — segue para outra chave com mesmo tenant/diag."""
        repo = CiPlaywrightDiagnosticoRepository()
        d = _diag_finalizado()
        await repo.salvar(d)
        await repo.salvar_e_materializar_plano_painel(d, _score())
        plano = await repo.buscar_plano_painel_serializado(d.id, d.tenant_id)
        assert plano is not None
        pid_str = next(
            ac["plano_acao_id"]
            for frente in plano.checklist
            for ac in frente.get("acoes", [])
            if isinstance(ac, dict) and isinstance(ac.get("plano_acao_id"), str)
        )
        pid = UUID(pid_str)
        repo._subs_por_chave[(d.id, d.tenant_id, uuid4())] = []
        sub = await repo.inserir_subtarefa_plano(d.tenant_id, d.id, pid, "Ok", ordem=0)
        sid = UUID(sub["id"])
        assert (await repo.atualizar_subtarefa_plano(d.tenant_id, d.id, sid, titulo="Novo"))[
            "titulo"
        ] == "Novo"

    async def test_atualizar_subtarefa_segundo_item_na_mesma_chave(self) -> None:
        """Primeira linha da lista não é o id procurado — cobre continuação do ``for`` interno."""
        repo = CiPlaywrightDiagnosticoRepository()
        d = _diag_finalizado()
        await repo.salvar(d)
        await repo.salvar_e_materializar_plano_painel(d, _score())
        plano = await repo.buscar_plano_painel_serializado(d.id, d.tenant_id)
        assert plano is not None
        pid_str = next(
            ac["plano_acao_id"]
            for frente in plano.checklist
            for ac in frente.get("acoes", [])
            if isinstance(ac, dict) and isinstance(ac.get("plano_acao_id"), str)
        )
        pid = UUID(pid_str)
        await repo.inserir_subtarefa_plano(d.tenant_id, d.id, pid, "Primeira", ordem=0)
        sub2 = await repo.inserir_subtarefa_plano(d.tenant_id, d.id, pid, "Segunda", ordem=1)
        sid2 = UUID(sub2["id"])
        assert (await repo.atualizar_subtarefa_plano(d.tenant_id, d.id, sid2, titulo="X"))[
            "titulo"
        ] == "X"

    async def test_atualizar_subtarefa_continue_ate_chave_certa(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        d = _diag_finalizado()
        await repo.salvar(d)
        await repo.salvar_e_materializar_plano_painel(d, _score())
        plano = await repo.buscar_plano_painel_serializado(d.id, d.tenant_id)
        assert plano is not None
        pid_str = next(
            ac["plano_acao_id"]
            for frente in plano.checklist
            for ac in frente.get("acoes", [])
            if isinstance(ac, dict) and isinstance(ac.get("plano_acao_id"), str)
        )
        pid = UUID(pid_str)
        # Chave com tenant errado forçada primeiro — laço externo deve ``continue``.
        repo._subs_por_chave[(d.id, uuid4(), pid)] = []
        sub = await repo.inserir_subtarefa_plano(d.tenant_id, d.id, pid, "Real", ordem=1)
        sid = UUID(sub["id"])
        assert (await repo.atualizar_subtarefa_plano(d.tenant_id, d.id, sid, titulo="Alt"))[
            "titulo"
        ] == "Alt"

    async def test_atualizar_subtarefa_nao_encontrada(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        assert (
            await repo.atualizar_subtarefa_plano(
                _TENANT_PADRAO_CI, _ID_LISTA_CI, uuid4(), titulo="Novo"
            )
            is None
        )

    async def test_atualizar_subtarefa_campos(self) -> None:
        repo = CiPlaywrightDiagnosticoRepository()
        d = _diag_finalizado()
        await repo.salvar(d)
        await repo.salvar_e_materializar_plano_painel(d, _score())
        plano = await repo.buscar_plano_painel_serializado(d.id, d.tenant_id)
        assert plano is not None
        pid_str = None
        for frente in plano.checklist:
            for ac in frente.get("acoes", []):
                if isinstance(ac, dict) and isinstance(ac.get("plano_acao_id"), str):
                    pid_str = ac["plano_acao_id"]
                    break
            if pid_str:
                break
        assert pid_str is not None
        pid = UUID(pid_str)
        sub = await repo.inserir_subtarefa_plano(d.tenant_id, d.id, pid, "Uma", ordem=0)
        sid = UUID(sub["id"])
        upd = await repo.atualizar_subtarefa_plano(
            d.tenant_id,
            d.id,
            sid,
            titulo=" Dois ",
            status=" feita ",
            prazo=date(2026, 6, 1),
            comentarios="nota",
            ordem=3,
        )
        assert upd is not None
        assert upd["titulo"] == "Dois"
        assert upd["status"] == "feita"
        assert upd["prazo"] == "2026-06-01"
        assert upd["comentarios"] == "nota"
        assert upd["ordem"] == 3
