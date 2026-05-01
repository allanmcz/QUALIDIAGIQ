"""Testes do serviço determinístico de consultoria (M06/M07/M08/M12)."""

from __future__ import annotations

import uuid

from src.application.services.consultoria_service import ConsultoriaService
from src.domain.entities.diagnostico import (
    Diagnostico,
    EmpresaInfo,
    PorteEmpresa,
    RegimeTributario,
    Respondente,
    SetorMacro,
)


def _empresa(porte: PorteEmpresa) -> EmpresaInfo:
    return EmpresaInfo(
        cnpj="12345678000195",
        razao_social="Consultoria Teste SA",
        porte=porte,
        regime=RegimeTributario.LUCRO_REAL,
        cnae_principal="1234567",
        uf="SP",
        setor_macro=SetorMacro.INDUSTRIA,
    )


def _diagnostico(porte: PorteEmpresa) -> Diagnostico:
    return Diagnostico(
        tenant_id=uuid.uuid4(),
        empresa=_empresa(porte),
        respondente=Respondente(email="fiscal@empresa.com"),
    )


def test_cronograma_cinco_fases_chaves_lc214() -> None:
    fases = ConsultoriaService.gerar_cronograma_cinco_fases()
    assert len(fases) == 5
    for linha in fases:
        assert set(linha.keys()) == {"fase", "foco", "referencia_normativa"}
        assert len(linha["fase"]) > 5


def test_checklist_abnt_dez_itens_com_base_legal() -> None:
    d = _diagnostico(PorteEmpresa.MICRO)
    frentes = ConsultoriaService.gerar_checklist(d)
    abnt = next(f for f in frentes if "17301" in f.nome and "10" in f.nome)
    assert len(abnt.acoes) == 10
    assert all(a.base_legal and "ABNT NBR 17301" in (a.base_legal or "") for a in abnt.acoes)
    assert sorted(a.prioridade for a in abnt.acoes) == list(range(1, 11))


def test_porte_medio_inclui_frentes_ti_cadastro() -> None:
    d = _diagnostico(PorteEmpresa.MEDIO)
    frentes = ConsultoriaService.gerar_checklist(d)
    nomes = {f.nome for f in frentes}
    assert "TI / ERP / Sistema Fiscal" in nomes
    assert "Cadastros Mestres" in nomes


def test_porte_micro_nao_inclui_ti_nem_cadastro_estendido() -> None:
    d = _diagnostico(PorteEmpresa.MICRO)
    frentes = ConsultoriaService.gerar_checklist(d)
    nomes = {f.nome for f in frentes}
    assert "TI / ERP / Sistema Fiscal" not in nomes
    assert "Cadastros Mestres" not in nomes


def test_acoes_tem_prioridade_e_ancoragem_normativa() -> None:
    d = _diagnostico(PorteEmpresa.GRANDE)
    frentes = ConsultoriaService.gerar_checklist(d)
    todas = [a for f in frentes for a in f.acoes]
    assert all(isinstance(a.prioridade, int) for a in todas)
    com_ref = [a for a in todas if a.base_legal]
    assert len(com_ref) >= 8


def test_matriz_impacto_quatro_departamentos() -> None:
    d = _diagnostico(PorteEmpresa.PEQUENO)
    m = ConsultoriaService.gerar_matriz_impacto(d)
    assert len(m) == 4
    assert {x.departamento for x in m} == {"Fiscal", "Comercial", "TI", "Jurídico"}
