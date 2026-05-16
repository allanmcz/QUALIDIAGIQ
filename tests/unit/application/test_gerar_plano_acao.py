"""Testes do caso de uso ``GerarPlanoAcaoUseCase``."""

from __future__ import annotations

from uuid import uuid4

import pytest

from src.application.services.plano_painel_derivacao import (
    DerivacaoPlanoMaterializado,
    LinhaPlanoAcaoParaPersistir,
    LinhaPlanoCronogramaParaPersistir,
    LinhaPlanoMatrizParaPersistir,
)
from src.application.use_cases.gerar_plano_acao import GerarPlanoAcaoUseCase
from src.domain.value_objects.plano_painel_serializado import PlanoPainelSerializado


def _deriv_min() -> DerivacaoPlanoMaterializado:
    ln = LinhaPlanoAcaoParaPersistir(
        id=uuid4(),
        ordem_exibicao=0,
        frente_indice=0,
        acao_indice=0,
        frente_nome="F",
        texto_acao="Ação teste",
        responsavel_sugerido="Resp",
        prazo_sugerido_texto="30 dias",
        criticidade="Alta",
        base_legal="LC 214/2025",
        origem_motor="M07",
        prioridade_motor=1,
        fase_pdca="DO",
        horizonte_planejado="IMEDIATO",
        criticidade_codigo="ALTA",
        dimensao_origem="fiscal",
        peso_motor=40.0,
    )
    mat = LinhaPlanoMatrizParaPersistir(
        id=uuid4(),
        ordem_exibicao=0,
        departamento="F",
        impacto_resumo="I",
        criticidade="alta",
        base_legal=None,
    )
    cro = LinhaPlanoCronogramaParaPersistir(
        id=uuid4(),
        ordem_exibicao=0,
        fase="1",
        foco="X",
        referencia_normativa="EC 132/2023",
    )
    ser = PlanoPainelSerializado(
        versao_plano=1,
        checklist=(),
        matriz_impacto=(),
        cronograma=(),
    )
    return DerivacaoPlanoMaterializado(
        versao_plano=1,
        linhas_acao=(ln,),
        linhas_matriz=(mat,),
        linhas_cronograma=(cro,),
        serializado_http=ser,
    )


class TestGerarPlanoAcaoUseCase:
    def test_construir_itens(self) -> None:
        tid, did = uuid4(), uuid4()
        uc = GerarPlanoAcaoUseCase()
        itens = uc.construir_itens(tid, did, _deriv_min())
        assert len(itens) == 1
        assert itens[0].criticidade.value == "ALTA"

    def test_construir_itens_rejeita_validador(self) -> None:
        from unittest.mock import MagicMock

        from src.application.services.validador_recusa_controlada import ResultadoValidacaoPlano

        tid, did = uuid4(), uuid4()
        mock_val = MagicMock()
        mock_val.validar.return_value = ResultadoValidacaoPlano.recusa(
            "norma_fora_vigencia", norma="X"
        )
        uc = GerarPlanoAcaoUseCase(validador=mock_val)
        with pytest.raises(ValueError, match="norma_fora_vigencia"):
            uc.construir_itens(tid, did, _deriv_min())

    def test_validar_derivacao_recusa(self) -> None:
        from unittest.mock import MagicMock

        from src.application.services.validador_recusa_controlada import ResultadoValidacaoPlano

        tid, did = uuid4(), uuid4()
        mock_val = MagicMock()
        mock_val.validar.return_value = ResultadoValidacaoPlano.recusa(
            "norma_fora_vigencia", norma="X"
        )
        uc = GerarPlanoAcaoUseCase(validador=mock_val)
        r = uc.validar_derivacao(tid, did, _deriv_min())
        assert r.aprovado is False
        assert r.motivo == "derivacao_invalida"

    def test_validar_derivacao_ok(self) -> None:
        tid, did = uuid4(), uuid4()
        uc = GerarPlanoAcaoUseCase()
        r = uc.validar_derivacao(tid, did, _deriv_min())
        assert r.aprovado is True
