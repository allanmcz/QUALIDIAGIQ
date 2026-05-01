#!/usr/bin/env python3
"""
Gera `src/infrastructure/questionario/data/perguntas_mvp.json` a partir do doc canônico.

Uso: PYTHONPATH=. python scripts/generate_questionario_catalog.py

UUID v5 fixos por código (namespace QDI) para estabilidade entre execuções.
"""

from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid5

NS = UUID("01800000-baad-4217-8000-000000000001")
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/infrastructure/questionario/data/perguntas_mvp.json"


def main() -> None:
    perguntas: list[dict] = []

    def add(
        codigo: str,
        dim: str,
        texto: str,
        peso: float,
        tipo: str,
        base_legal: str | None,
        condicao: dict | None = None,
        multipla_total: int | None = None,
    ) -> None:
        d: dict = {
            "id": str(uuid5(NS, codigo)),
            "codigo": codigo,
            "dimensao": dim,
            "texto": texto,
            "peso": peso,
            "tipo": tipo,
            "base_legal": base_legal,
            "condicao": condicao,
        }
        if multipla_total is not None:
            d["multipla_total"] = multipla_total
        perguntas.append(d)

    # --- Bloco 1 Estratégica ---
    add(
        "Q-EST-001",
        "estrategica",
        "Sua empresa já iniciou um plano estruturado de transição para a Reforma Tributária?",
        7.5,
        "ternaria",
        "EC 132/2023; LC 214/2025",
    )
    add(
        "Q-EST-002",
        "estrategica",
        "O time fiscal e contábil já mapeou como o novo modelo de créditos e débitos pode afetar o resultado financeiro e a formação de preços?",
        8.0,
        "ternaria",
        "LC 214/2025 art. 28-32",
    )
    add(
        "Q-EST-003",
        "estrategica",
        "Sua empresa já revisou suas margens e políticas de preço considerando a tributação no destino e preços diferenciados por região?",
        7.5,
        "ternaria",
        "LC 214/2025 art. 5º",
    )
    add(
        "Q-EST-004",
        "estrategica",
        "Os contratos comerciais e de prestação de serviços já foram revisados para tributos na transição?",
        7.0,
        "ternaria",
        "LC 214/2025 art. 415; CC art. 478",
    )
    # --- Bloco 2 Tecnológico ---
    add(
        "Q-TEC-001",
        "tecnologica",
        "Seu ERP e sistemas fiscais já estão sendo adaptados para o novo modelo de apuração do IBS e da CBS?",
        9.0,
        "ternaria",
        "LC 214/2025 art. 12-15; NT 2025.002",
    )
    add(
        "Q-TEC-002",
        "tecnologica",
        "Seu sistema fiscal está pronto para os novos campos da NF-e (cClassTrib, cCredPres) e validações da NT 2025.002?",
        9.0,
        "ternaria",
        "NT 2025.002",
    )
    add(
        "Q-TEC-003",
        "tecnologica",
        "Sua equipe financeira/TI já estimou o impacto da mudança na forma de recolhimento (split payment, retenções)?",
        8.5,
        "ternaria",
        "LC 214/2025 art. 200-220",
    )
    add(
        "Q-TEC-004",
        "tecnologica",
        "Sua empresa monitora NTs e cronogramas do CGNFS-e e CGSEFAZ para a transição?",
        7.0,
        "ternaria",
        "NTs CGNFS-e; NT 2025.002",
    )
    # --- Bloco 3 Fiscal ---
    add(
        "Q-FISC-001",
        "fiscal",
        "A empresa já avaliou como benefícios fiscais e regimes especiais podem ser afetados na transição até 2033?",
        8.5,
        "ternaria",
        "EC 132/2023 ADCT; LC 214/2025 art. 384-410",
    )
    add(
        "Q-FISC-002",
        "fiscal",
        "Sua empresa já avaliou o impacto da extinção de regimes especiais (Reporto, Recap, crédito presumido)?",
        7.5,
        "ternaria",
        "Lei 11.196/05; Lei 11.488/07; LC 214/2025 art. 392",
    )
    add(
        "Q-FISC-003",
        "fiscal",
        "A gestão de créditos de ICMS, PIS e COFINS acumulados está sendo monitorada para evitar perdas?",
        8.5,
        "ternaria",
        "LC 214/2025 art. 130-145",
    )
    add(
        "Q-FISC-004",
        "fiscal",
        "Sua empresa identifica produtos sujeitos ao Imposto Seletivo no mix (combustíveis, bebidas, fumo, veículos, minerais)?",
        6.5,
        "ternaria",
        "EC 132/2023 art. 153, VIII; LC 214/2025 art. 432-450",
        {"setores_permitidos": ["comercio", "industria", "agro"]},
    )
    # --- Bloco 4 Financeiro + Operacional ---
    add(
        "Q-FIN-001",
        "financeira",
        "A gestão de estoques e regimes de reposição foi avaliada para evitar perda de créditos na transição?",
        7.5,
        "ternaria",
        "LC 214/2025 art. 130-135",
        {"setores_excluidos": ["servicos"]},
    )
    add(
        "Q-OPER-001",
        "operacional",
        "A empresa possui processos claros para rastrear e controlar créditos tributários entre compras, vendas e serviços?",
        8.0,
        "ternaria",
        "LC 214/2025 art. 28",
    )
    add(
        "Q-OPER-002",
        "operacional",
        "As operações entre filiais/fornecedores/clientes foram simuladas considerando tributação no destino?",
        7.5,
        "ternaria",
        "LC 214/2025 art. 5º; art. 415",
        {"portes_permitidos": ["medio", "grande", "enterprise"]},
    )
    add(
        "Q-OPER-003",
        "operacional",
        "Sua empresa já iniciou treinamentos sobre IBS, CBS, IS e efeitos operacionais e financeiros?",
        6.5,
        "ternaria",
        "Referência mercado / melhores práticas",
    )
    # --- Bloco 5 ABNT ---
    add(
        "Q-ABNT-001",
        "compliance_abnt_17301",
        "Sua empresa possui política interna formal de Compliance Tributário (escrita, aprovada e divulgada)?",
        8.5,
        "escala_1_5",
        "ABNT NBR 17301:2026 cap. 5.1",
    )
    add(
        "Q-ABNT-002",
        "compliance_abnt_17301",
        "A empresa identifica e avalia periodicamente os riscos fiscais?",
        8.5,
        "escala_1_5",
        "ABNT NBR 17301:2026 cap. 6.1",
    )
    add(
        "Q-ABNT-003",
        "compliance_abnt_17301",
        "Os controles sobre obrigações tributárias estão documentados (ITs, fluxos)?",
        9.0,
        "escala_1_5",
        "ABNT NBR 17301:2026 cap. 7.1",
    )
    add(
        "Q-ABNT-004",
        "compliance_abnt_17301",
        "A empresa monitora obrigações tributárias de forma contínua (não só no fechamento)?",
        8.0,
        "escala_1_5",
        "ABNT NBR 17301:2026 cap. 9",
    )
    add(
        "Q-ABNT-005",
        "compliance_abnt_17301",
        "Existe mecanismo formal de melhoria contínua dos processos tributários?",
        7.5,
        "escala_1_5",
        "ABNT NBR 17301:2026 cap. 10",
    )
    # --- Setoriais varejo (macro comercio) ---
    add(
        "Q-VAREJO-001",
        "fiscal",
        "No varejo/atacado, a empresa já analisou impacto de créditos e débitos na margem e precificação?",
        8.0,
        "ternaria",
        "LC 214/2025 art. 28",
        {"setores_permitidos": ["comercio"]},
    )
    add(
        "Q-VAREJO-002",
        "fiscal",
        "Sua operação tem alto volume sob ICMS-ST e já avaliou o impacto do fim desse regime?",
        9.0,
        "ternaria",
        "LC 214/2025 art. 60-65",
        {"setores_permitidos": ["comercio"]},
    )
    add(
        "Q-VAREJO-003",
        "fiscal",
        "Sua empresa avaliou impacto na cesta básica e produtos com alíquota reduzida (saúde, educação, agro)?",
        6.5,
        "ternaria",
        "LC 214/2025 art. 9º; art. 137; art. 145",
        {"setores_permitidos": ["comercio"]},
    )
    # --- Indústria ---
    add(
        "Q-IND-001",
        "fiscal",
        "Sua indústria já avaliou impacto na cadeia com tributação no destino (fornecedores, CDs, filiais)?",
        8.5,
        "ternaria",
        "LC 214/2025 art. 5º; art. 50",
        {"setores_permitidos": ["industria"]},
    )
    add(
        "Q-IND-002",
        "fiscal",
        "Sua empresa monitora impactos da extinção do IPI (exceto ZFM) sobre o mix de produtos?",
        7.0,
        "ternaria",
        "EC 132/2023 art. 153, IV; LC 214/2025 art. 451-460",
        {"setores_permitidos": ["industria"]},
    )
    add(
        "Q-IND-003",
        "fiscal",
        "Sua indústria já avaliou impactos da CBS na cadeia (insumos, energia, créditos)?",
        8.0,
        "ternaria",
        "LC 214/2025 art. 12-15",
        {"setores_permitidos": ["industria"]},
    )
    # --- Serviços ---
    add(
        "Q-SERV-001",
        "fiscal",
        "Sua emissão de NFS-e está sendo adequada ao layout RTC (NTs 003 a 007 CGNFS-e)?",
        9.0,
        "ternaria",
        "NTs 003-007 CGNFS-e",
        {"setores_permitidos": ["servicos"]},
    )
    add(
        "Q-SERV-002",
        "fiscal",
        "Sua empresa já avaliou o impacto da nova alíquota IBS+CBS sobre serviços?",
        8.5,
        "ternaria",
        "LC 214/2025 art. 12-15",
        {"setores_permitidos": ["servicos"]},
    )
    add(
        "Q-SERV-003",
        "fiscal",
        "Sua empresa atua em setor com alíquota diferenciada (saúde, educação, transporte) e já avaliou benefícios?",
        6.5,
        "ternaria",
        "LC 214/2025 art. 137; 145; 156",
        {"setores_permitidos": ["servicos"]},
    )
    # --- Agro ---
    add(
        "Q-AGRO-001",
        "fiscal",
        "Sua empresa do agro já avaliou impactos da redução de alíquota de 60% sobre produtos agropecuários?",
        8.5,
        "ternaria",
        "LC 214/2025 art. 138-141",
        {"setores_permitidos": ["agro"]},
    )
    add(
        "Q-AGRO-002",
        "fiscal",
        "Sua empresa avalia impactos do crédito presumido ao produtor rural PF e da apropriação por agroindústrias?",
        7.5,
        "ternaria",
        "LC 214/2025 art. 165-170",
        {"setores_permitidos": ["agro"]},
    )
    # --- Lucro real avançado (proxy: porte médio+ — doc original cita faturamento > 100M) ---
    lr_cond = {"regimes_permitidos": ["lucro_real"], "portes_permitidos": ["medio", "grande", "enterprise"]}
    add(
        "Q-REAL-001",
        "contabil",
        "Sua empresa avaliou reestruturações societárias (filiais, holding, fusões) na transição tributária?",
        7.5,
        "ternaria",
        "Lei 6.404/76 art. 226",
        lr_cond,
    )
    add(
        "Q-REAL-002",
        "contabil",
        "Sua empresa atua como substituto tributário no modelo CBS/IBS e já preparou os controles?",
        7.0,
        "ternaria",
        "LC 214/2025 art. 60-65",
        lr_cond,
    )
    add(
        "Q-REAL-003",
        "financeira",
        "Sua tesouraria projetou cenários de fluxo de caixa 2026-2033 com sensibilidade às alíquotas?",
        8.0,
        "ternaria",
        "EC 132/2023; LC 214/2025 art. 384-410",
        lr_cond,
    )
    add(
        "Q-REAL-004",
        "contabil",
        "Sua empresa avaliou impactos da Reforma sobre IRPJ e CSLL?",
        6.5,
        "ternaria",
        "Lei 9.430/96; CPC 32",
        lr_cond,
    )
    add(
        "Q-REAL-005",
        "contabil",
        "A empresa tem governança contratual para Cláusulas de Repactuação Tributária em contratos longos (> 12 meses)?",
        7.0,
        "ternaria",
        "CC art. 478",
        lr_cond,
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "versao_catalogo": "v1-doc-05-full-37",
        "namespace_uuid": str(NS),
        "perguntas": perguntas,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Escrito {OUT} ({len(perguntas)} perguntas)")


if __name__ == "__main__":
    main()
