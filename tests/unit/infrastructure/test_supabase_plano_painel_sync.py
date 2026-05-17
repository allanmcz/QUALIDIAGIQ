"""Testes de ``supabase_plano_painel_sync`` com cliente PostgREST em memória (sem rede)."""

from __future__ import annotations

from datetime import UTC, date, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from src.application.services.plano_painel_derivacao import (
    DerivacaoPlanoMaterializado,
    LinhaPlanoAcaoParaPersistir,
    LinhaPlanoCronogramaParaPersistir,
    LinhaPlanoMatrizParaPersistir,
)
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)
from src.domain.value_objects.plano_painel_serializado import PlanoPainelSerializado
from src.domain.value_objects.score import Dimensao, ScoreCompleto, ScoreNumerico
from src.infrastructure.repositories.supabase_plano_painel_sync import (
    _sub_http,
    atualizar_subtarefa_supabase,
    buscar_plano_painel_serializado_supabase,
    inserir_subtarefa_supabase,
    materializar_plano_painel_supabase,
)


class _Exec:
    def __init__(self, data: list | None) -> None:
        self.data = data


class _Chain:
    def __init__(self, execute_result: _Exec) -> None:
        self._result = execute_result

    def select(self, *_a: object, **_k: object) -> _Chain:
        return self

    def eq(self, *_a: object, **_k: object) -> _Chain:
        return self

    def order(self, *_a: object, **_k: object) -> _Chain:
        return self

    def limit(self, *_a: object, **_k: object) -> _Chain:
        return self

    def delete(self) -> _Chain:
        return self

    def insert(self, *_a: object, **_k: object) -> _Chain:
        return self

    def update(self, *_a: object, **_k: object) -> _Chain:
        return self

    def execute(self) -> _Exec:
        return self._result


class _TableRouter:
    """Roteia ``table(name)`` para respostas fixas por nome de tabela."""

    def __init__(self, por_tabela: dict[str, _Exec]) -> None:
        self._por = por_tabela

    def table(self, name: str) -> _Chain:
        return _Chain(self._por.get(name, _Exec([])))


class TestSubHttpSupabase:
    def test_prazo_none(self) -> None:
        r = {"id": str(uuid4()), "titulo": "T", "status": "aberta", "ordem": 1}
        assert _sub_http(r)["prazo"] is None

    def test_prazo_str(self) -> None:
        r = {
            "id": str(uuid4()),
            "titulo": "T",
            "status": "aberta",
            "ordem": 1,
            "prazo": "2026-01-02xyz",
        }
        assert _sub_http(r)["prazo"] == "2026-01-02"

    def test_prazo_datetime(self) -> None:
        r = {
            "id": str(uuid4()),
            "titulo": "T",
            "status": "aberta",
            "ordem": 1,
            "prazo": datetime(2026, 3, 15, 10, 0, 0, tzinfo=UTC),
        }
        assert _sub_http(r)["prazo"] == "2026-03-15"

    def test_prazo_outro_tipo_coerce_str(self) -> None:
        r = {"id": str(uuid4()), "titulo": "T", "status": "aberta", "ordem": 1, "prazo": 20260315}
        assert _sub_http(r)["prazo"] == "20260315"[:10]


def _diag_sc() -> tuple[Diagnostico, ScoreCompleto]:
    emp = EmpresaInfo(
        cnpj="12345678000195",
        razao_social="Supa",
        porte=PorteEmpresa.MICRO,
        regime=RegimeTributario.SIMPLES_NACIONAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.COMERCIO,
    )
    d = Diagnostico(tenant_id=uuid4(), empresa=emp, respondente=Respondente(email="a@b.com"))
    d.finalizar(70.0)
    sc = ScoreCompleto(
        score_geral=ScoreNumerico(valor=70.0, peso_total_aplicado=1.0),
        score_por_dimensao={Dimensao.FISCAL: ScoreNumerico(valor=70.0, peso_total_aplicado=1.0)},
    )
    d.registrar_score_completo_para_evidencia(sc)
    return d, sc


def _deriv_stub(acao_id, ser: PlanoPainelSerializado | None = None) -> DerivacaoPlanoMaterializado:
    ln = LinhaPlanoAcaoParaPersistir(
        id=acao_id,
        ordem_exibicao=1,
        frente_indice=0,
        acao_indice=0,
        frente_nome="F",
        texto_acao="A",
        responsavel_sugerido="R",
        prazo_sugerido_texto="p",
        criticidade="c",
        base_legal="LC 214/2025",
        origem_motor="OUTROS",
        prioridade_motor=1,
    )
    mat = LinhaPlanoMatrizParaPersistir(
        id=uuid4(),
        ordem_exibicao=1,
        departamento="d",
        impacto_resumo="i",
        criticidade="c",
        base_legal=None,
    )
    cro = LinhaPlanoCronogramaParaPersistir(
        id=uuid4(), ordem_exibicao=1, fase="1", foco="f", referencia_normativa="EC 132/2023"
    )
    ser = ser or PlanoPainelSerializado(
        versao_plano=1, checklist=(), matriz_impacto=(), cronograma=()
    )
    return DerivacaoPlanoMaterializado(
        versao_plano=ser.versao_plano,
        linhas_acao=(ln,),
        linhas_matriz=(mat,),
        linhas_cronograma=(cro,),
        serializado_http=ser,
    )


@patch(
    "src.infrastructure.repositories.supabase_plano_painel_sync.buscar_plano_painel_serializado_supabase",
    return_value=None,
)
@patch(
    "src.infrastructure.repositories.supabase_plano_painel_sync.derivar_plano_painel_materializado"
)
def test_materializar_plano_supabase_usa_serializado_quando_busca_vazia(
    mock_deriv, _mock_buscar: MagicMock
) -> None:
    aid = uuid4()
    ser = PlanoPainelSerializado(versao_plano=2, checklist=(), matriz_impacto=(), cronograma=())
    mock_deriv.return_value = _deriv_stub(aid, ser)
    chain = MagicMock()
    chain.delete.return_value = chain
    chain.eq.return_value = chain
    chain.insert.return_value = chain
    chain.execute.return_value = MagicMock(data=[])
    client = MagicMock()
    client.table.return_value = chain
    diag, sc = _diag_sc()
    out = materializar_plano_painel_supabase(client, diag, sc)
    assert out.versao_plano == 2


@patch(
    "src.infrastructure.repositories.supabase_plano_painel_sync.buscar_plano_painel_serializado_supabase",
    return_value=PlanoPainelSerializado(
        versao_plano=1, checklist=(), matriz_impacto=(), cronograma=()
    ),
)
@patch(
    "src.infrastructure.repositories.supabase_plano_painel_sync.derivar_plano_painel_materializado"
)
def test_materializar_plano_supabase(mock_deriv, _mock_buscar: MagicMock) -> None:
    aid = uuid4()
    mock_deriv.return_value = _deriv_stub(aid)
    chain = MagicMock()
    chain.delete.return_value = chain
    chain.eq.return_value = chain
    chain.insert.return_value = chain
    chain.execute.return_value = MagicMock(data=[])
    client = MagicMock()
    client.table.return_value = chain
    diag, sc = _diag_sc()
    out = materializar_plano_painel_supabase(client, diag, sc)
    assert out.versao_plano == 1
    assert client.table.call_count >= 6


def test_inserir_subtarefa_supabase_ok() -> None:
    row = {
        "id": str(uuid4()),
        "titulo": "T",
        "status": "aberta",
        "ordem": 0,
        "prazo": None,
        "comentarios": None,
    }
    chain_chk = MagicMock()
    chain_chk.select.return_value = chain_chk
    chain_chk.eq.return_value = chain_chk
    chain_chk.limit.return_value = chain_chk
    chain_chk.execute.return_value = MagicMock(data=[{"id": "x"}])

    chain_ins = MagicMock()
    chain_ins.insert.return_value = chain_ins
    chain_ins.execute.return_value = MagicMock(data=[row])

    def table(name: str) -> MagicMock:
        if name == "diagnostico_plano_acao":
            return chain_chk
        if name == "diagnostico_plano_subtarefa":
            return chain_ins
        raise AssertionError(name)

    client = MagicMock()
    client.table.side_effect = table
    out = inserir_subtarefa_supabase(client, uuid4(), uuid4(), uuid4(), "  T  ", 0)
    assert out["titulo"] == "T"


def test_inserir_subtarefa_supabase_insert_sem_data() -> None:
    chain_chk = MagicMock()
    chain_chk.select.return_value = chain_chk
    chain_chk.eq.return_value = chain_chk
    chain_chk.limit.return_value = chain_chk
    chain_chk.execute.return_value = MagicMock(data=[{"id": "x"}])

    chain_ins = MagicMock()
    chain_ins.insert.return_value = chain_ins
    chain_ins.execute.return_value = MagicMock(data=[])

    def table(name: str) -> MagicMock:
        if name == "diagnostico_plano_acao":
            return chain_chk
        if name == "diagnostico_plano_subtarefa":
            return chain_ins
        raise AssertionError(name)

    client = MagicMock()
    client.table.side_effect = table
    with pytest.raises(RuntimeError, match="Falha ao inserir"):
        inserir_subtarefa_supabase(client, uuid4(), uuid4(), uuid4(), "t", 0)


def test_inserir_subtarefa_supabase_sem_acao() -> None:
    chain = MagicMock()
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.limit.return_value = chain
    chain.execute.return_value = MagicMock(data=[])
    client = MagicMock()
    client.table.return_value = chain
    with pytest.raises(ValueError, match="inexistente"):
        inserir_subtarefa_supabase(client, uuid4(), uuid4(), uuid4(), "x", 1)


def test_atualizar_subtarefa_supabase_select_sem_linha() -> None:
    chain = MagicMock()
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.limit.return_value = chain
    chain.execute.return_value = MagicMock(data=[])
    client = MagicMock()
    client.table.return_value = chain
    out = atualizar_subtarefa_supabase(
        client,
        uuid4(),
        uuid4(),
        uuid4(),
        titulo=None,
        status=None,
        prazo=None,
        comentarios=None,
        ordem=None,
    )
    assert out is None


def test_atualizar_subtarefa_supabase_sem_patch_select() -> None:
    row = {
        "id": str(uuid4()),
        "titulo": "L",
        "status": "feita",
        "ordem": 0,
        "prazo": None,
        "comentarios": None,
    }
    chain = MagicMock()
    chain.select.return_value = chain
    chain.eq.return_value = chain
    chain.limit.return_value = chain
    chain.execute.return_value = MagicMock(data=[row])
    client = MagicMock()
    client.table.return_value = chain
    out = atualizar_subtarefa_supabase(
        client,
        uuid4(),
        uuid4(),
        uuid4(),
        titulo=None,
        status=None,
        prazo=None,
        comentarios=None,
        ordem=None,
    )
    assert out is not None
    assert out["titulo"] == "L"


def test_atualizar_subtarefa_supabase_com_update() -> None:
    row = {
        "id": str(uuid4()),
        "titulo": "N",
        "status": "aberta",
        "ordem": 1,
        "prazo": "2026-04-01",
        "comentarios": "c",
    }
    chain = MagicMock()
    chain.update.return_value = chain
    chain.eq.return_value = chain
    chain.select.return_value = chain
    chain.limit.return_value = chain
    chain.execute.return_value = MagicMock(data=[row])
    client = MagicMock()
    client.table.return_value = chain
    out = atualizar_subtarefa_supabase(
        client,
        uuid4(),
        uuid4(),
        uuid4(),
        titulo=None,
        status="  feita  ",
        prazo=date(2026, 4, 2),
        comentarios="x",
        ordem=2,
    )
    assert out is not None
    assert out["titulo"] == "N"
    assert out["status"] == "aberta"


def test_atualizar_subtarefa_supabase_update_sem_linha() -> None:
    chain = MagicMock()
    chain.update.return_value = chain
    chain.eq.return_value = chain
    chain.select.return_value = chain
    chain.limit.return_value = chain
    chain.execute.return_value = MagicMock(data=[])
    client = MagicMock()
    client.table.return_value = chain
    out = atualizar_subtarefa_supabase(
        client,
        uuid4(),
        uuid4(),
        uuid4(),
        titulo="só",
        status=None,
        prazo=None,
        comentarios=None,
        ordem=None,
    )
    assert out is None


def test_buscar_plano_supabase_sem_acoes() -> None:
    client = _TableRouter({"diagnostico_plano_acao": _Exec([])})
    assert buscar_plano_painel_serializado_supabase(client, uuid4(), uuid4()) is None


def test_buscar_plano_supabase_com_dados() -> None:
    aid = str(uuid4())
    acao = {
        "id": aid,
        "versao_plano": 1,
        "frente_indice": 0,
        "acao_indice": 1,
        "ordem_exibicao": 1,
        "frente_nome": "F",
        "texto_acao": "A",
        "responsavel_sugerido": "R",
        "prazo_sugerido_texto": "p",
        "criticidade": "c",
        "base_legal": "LC 214/2025",
        "prioridade_motor": 1,
    }
    mat = {"departamento": "d", "impacto_resumo": "i", "criticidade": "c", "base_legal": None}
    cro = {"fase": "1", "foco": "f", "referencia_normativa": "EC 132/2023"}
    sub = {
        "id": str(uuid4()),
        "plano_acao_id": aid,
        "titulo": "s",
        "status": "aberta",
        "ordem": 0,
        "prazo": None,
        "comentarios": None,
    }
    por = {
        "diagnostico_plano_acao": _Exec([acao]),
        "diagnostico_plano_matriz": _Exec([mat]),
        "diagnostico_plano_cronograma": _Exec([cro]),
        "diagnostico_plano_subtarefa": _Exec([sub]),
    }
    out = buscar_plano_painel_serializado_supabase(_TableRouter(por), uuid4(), uuid4())
    assert out is not None
    assert out.versao_plano == 1
    assert aid in out.subtarefas_por_acao
    assert out.checklist[0]["acoes"][0]["ordem_exibicao"] == 1


def test_del_tabela_versao_chama_cadeia() -> None:
    from src.infrastructure.repositories.supabase_plano_painel_sync import _del_tabela_versao

    ex = _Exec([])
    chain = MagicMock()
    chain.delete.return_value = chain
    chain.eq.return_value = chain
    chain.execute.return_value = ex
    client = MagicMock()
    client.table.return_value = chain
    _del_tabela_versao(client, "diagnostico_plano_acao", "d1", "t1", 1)
    client.table.assert_called_with("diagnostico_plano_acao")
    chain.execute.assert_called_once()
