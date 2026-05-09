"""
Mapeamento JSON (BrasilAPI / Minha Receita) → sugestões para ``EmpresaInfo``.

Camada: Application — sem I/O (testável unitariamente).

Base normativa operacional: dados públicos da Receita Federal / cadastro CNPJ (LC 214/2025 — previsibilidade).
"""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Any

from src.domain.entities.diagnostico import EmpresaInfo, PorteEmpresa, RegimeTributario, SetorMacro


def _digits_cnae(raw: Any) -> str | None:
    if raw is None:
        return None
    s = re.sub(r"\D", "", str(raw))
    if len(s) < 7:
        s = s.zfill(7)
    if len(s) != 7 or not s.isdigit():
        return None
    return s


def _inferir_setor_macro_de_cnae(cnae7: str | None) -> SetorMacro | None:
    """Heurística CNAE 2.x → setor macro do questionário (MVP)."""
    if not cnae7 or len(cnae7) < 2 or not cnae7[:2].isdigit():
        return None
    d = int(cnae7[:2])
    if 1 <= d <= 3:
        return SetorMacro.AGRO
    if 5 <= d <= 33:
        return SetorMacro.INDUSTRIA
    if 41 <= d <= 43:
        return SetorMacro.CONSUMO
    if 45 <= d <= 47:
        return SetorMacro.COMERCIO
    return SetorMacro.SERVICOS


def _porte_de_codigo(codigo: Any, porte_txt: Any) -> PorteEmpresa | None:
    try:
        c = int(codigo) if codigo is not None else None
    except (TypeError, ValueError):
        c = None
    if c == 1:
        return PorteEmpresa.MICRO
    if c == 3:
        return PorteEmpresa.PEQUENO
    if c == 5:
        return PorteEmpresa.MEDIO
    txt = str(porte_txt or "").upper()
    if "MEI" in txt:
        return PorteEmpresa.MICRO
    if "MICRO" in txt:
        return PorteEmpresa.MICRO
    if "PEQUENO" in txt or "EPP" in txt:
        return PorteEmpresa.PEQUENO
    if "MÉDIO" in txt or "MEDIO" in txt:
        return PorteEmpresa.MEDIO
    if "GRANDE" in txt or "DEMAIS" in txt:
        return PorteEmpresa.MEDIO
    return None


def _regime_de_payload(payload: dict[str, Any]) -> RegimeTributario | None:
    rt = payload.get("regime_tributario")
    if isinstance(rt, list) and rt:
        try:
            last = max(rt, key=lambda x: int(x.get("ano") or 0))
        except (TypeError, ValueError):
            last = rt[-1]
        ft = str(last.get("forma_de_tributacao") or "").upper()
        if "MEI" in ft:
            return RegimeTributario.MEI
        if "SIMPLES" in ft:
            return RegimeTributario.SIMPLES_NACIONAL
        if "PRESUMIDO" in ft:
            return RegimeTributario.LUCRO_PRESUMIDO
        if "REAL" in ft:
            return RegimeTributario.LUCRO_REAL
    if payload.get("opcao_pelo_mei") is True:
        return RegimeTributario.MEI
    if payload.get("opcao_pelo_simples") is True:
        return RegimeTributario.SIMPLES_NACIONAL
    return None


def sugestao_desde_payload_receita(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Extrai campos canónicos para hash/TTL e merge (valores serializáveis JSON).
    """
    cnae = _digits_cnae(payload.get("cnae_fiscal"))
    uf = str(payload.get("uf") or "").strip().upper()[:2] or None
    rz = str(payload.get("razao_social") or "").strip() or None
    situacao = str(payload.get("descricao_situacao_cadastral") or "").strip() or None
    porte = _porte_de_codigo(payload.get("codigo_porte"), payload.get("porte"))
    regime = _regime_de_payload(payload)
    setor = _inferir_setor_macro_de_cnae(cnae)
    return {
        "cnpj": re.sub(r"\D", "", str(payload.get("cnpj") or "")),
        "razao_social": rz,
        "cnae_principal": cnae,
        "uf": uf if uf and len(uf) == 2 else None,
        "situacao_cadastral": situacao,
        "porte": porte.value if porte else None,
        "regime": regime.value if regime else None,
        "setor_macro": setor.value if setor else None,
        "nome_fantasia": str(payload.get("nome_fantasia") or "").strip() or None,
        "municipio": str(payload.get("municipio") or "").strip() or None,
        "logradouro": str(payload.get("logradouro") or "").strip() or None,
    }


def mesclar_empresa_com_sugestao_cnpj(
    atual: EmpresaInfo,
    sugestao: dict[str, Any],
    *,
    cnpj_consulta_14: str,
) -> tuple[EmpresaInfo, list[tuple[str, str | None, str]]]:
    """
    Preenche vazios e sobrescreve quando o valor consultado difere; devolve trilha para histórico.

    Returns:
        Tupla ``(nova_empresa, [(campo_tabela, valor_anterior, valor_novo), ...])``.
    """
    historico: list[tuple[str, str | None, str]] = []

    def _norm_txt(x: str) -> str:
        return " ".join(x.strip().split()).casefold()

    nova = atual

    # CNPJ — consulta é fonte da verdade cadastral
    if cnpj_consulta_14 and cnpj_consulta_14 != nova.cnpj:
        historico.append(("empresa_cnpj", nova.cnpj or None, cnpj_consulta_14))
        nova = replace(nova, cnpj=cnpj_consulta_14)

    rz = sugestao.get("razao_social")
    if isinstance(rz, str) and rz.strip():
        cur = nova.razao_social.strip()
        if cur == "" or _norm_txt(cur) == "":
            historico.append(("empresa_razao_social", None, rz.strip()))
            nova = replace(nova, razao_social=rz.strip())
        elif _norm_txt(cur) != _norm_txt(rz):
            historico.append(("empresa_razao_social", cur, rz.strip()))
            nova = replace(nova, razao_social=rz.strip())

    cnae = sugestao.get("cnae_principal")
    if isinstance(cnae, str) and len(cnae) == 7 and cnae.isdigit():
        cur = nova.cnae_principal.strip()
        if cur == "":
            historico.append(("empresa_cnae", None, cnae))
            nova = replace(nova, cnae_principal=cnae)
        elif cur != cnae:
            historico.append(("empresa_cnae", cur, cnae))
            nova = replace(nova, cnae_principal=cnae)

    uf = sugestao.get("uf")
    if isinstance(uf, str) and len(uf) == 2 and uf.isalpha():
        u = uf.upper()
        cur = nova.uf.strip().upper()
        if cur == "":
            historico.append(("empresa_uf", None, u))
            nova = replace(nova, uf=u)
        elif cur != u:
            historico.append(("empresa_uf", cur, u))
            nova = replace(nova, uf=u)

    ps = sugestao.get("porte")
    if isinstance(ps, str) and ps in {p.value for p in PorteEmpresa}:
        pe = PorteEmpresa(ps)
        if nova.porte != pe:
            historico.append(("empresa_porte", nova.porte.value, pe.value))
            nova = replace(nova, porte=pe)

    rs = sugestao.get("regime")
    if isinstance(rs, str) and rs in {r.value for r in RegimeTributario}:
        rg = RegimeTributario(rs)
        if nova.regime != rg:
            historico.append(("empresa_regime", nova.regime.value, rg.value))
            nova = replace(nova, regime=rg)

    sm = sugestao.get("setor_macro")
    if isinstance(sm, str) and sm in {s.value for s in SetorMacro}:
        se = SetorMacro(sm)
        if nova.setor_macro != se:
            historico.append(("empresa_setor_macro", nova.setor_macro.value, se.value))
            nova = replace(nova, setor_macro=se)

    return nova, historico
