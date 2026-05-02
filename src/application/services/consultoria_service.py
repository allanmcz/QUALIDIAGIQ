"""
Serviço de consultoria determinística (checklist, matriz, cronograma).

Camada: Application
Base normativa: EC 132/2023; LC 214/2025; ABNT NBR 17301:2026 (referências em bullets).
"""

from __future__ import annotations

from dataclasses import dataclass

from src.domain.entities.diagnostico import Diagnostico, PorteEmpresa
from src.domain.value_objects.score import Dimensao, ScoreCompleto

_ROTULO_DIMENSAO_PT: dict[Dimensao, str] = {
    Dimensao.FISCAL: "Fiscal",
    Dimensao.ESTRATEGICA: "Estratégica",
    Dimensao.CONTABIL: "Contábil",
    Dimensao.FINANCEIRA: "Financeira",
    Dimensao.OPERACIONAL: "Operacional",
    Dimensao.TECNOLOGICA: "Tecnológica",
    Dimensao.COMPLIANCE_ABNT: "Compliance ABNT NBR 17301",
}


@dataclass
class AcaoChecklist:
    """Uma ação priorizada com ancoragem legal opcional (M07/M08)."""

    descricao: str
    responsavel: str
    prazo: str
    criticidade: str
    base_legal: str | None = None
    prioridade: int = 50


@dataclass
class FrenteTrabalho:
    nome: str
    acoes: list[AcaoChecklist]


@dataclass
class ImpactoDepartamento:
    departamento: str
    impacto_resumo: str
    criticidade: str
    base_legal: str | None = None


class ConsultoriaService:
    """
    Traduz o perfil da empresa (porte, regime) em checklist, matriz e fases temporais.
    """

    @staticmethod
    def _frente_prioridade_por_gaps_score(score: ScoreCompleto) -> FrenteTrabalho:
        """
        Orquestra recomendações iniciais a partir das **piores dimensões** no score (M07).

        Regra determinística: usa só o snapshot quantitative do diagnóstico (sem LLM).
        """
        piores = sorted(score.score_por_dimensao.items(), key=lambda kv: kv[1].valor)[:3]
        acoes: list[AcaoChecklist] = []
        for idx, (dim, sn) in enumerate(piores, start=1):
            rotulo = _ROTULO_DIMENSAO_PT.get(dim, dim.value.replace("_", " "))
            desc = (
                f"Priorizar plano de ação na dimensão «{rotulo}» (score {sn.valor:.1f}/100). "
                "Revise respostas e projetos correlatos antes de expansão para outras frentes."
            )
            crit = "Crítica" if sn.valor < 45.0 else "Alta"
            acoes.append(
                AcaoChecklist(
                    desc,
                    "Comitê tributário / sponsor executivo",
                    "Imediato",
                    crit,
                    "LC 214/2025 art. 5º (previsibilidade); ABNT NBR 17301:2026 cap. 9 (indicadores)",
                    idx,
                )
            )
        return FrenteTrabalho(
            nome="Prioridade por gaps do score (automático — M07)",
            acoes=acoes,
        )

    @staticmethod
    def gerar_cronograma_cinco_fases() -> list[dict[str, str]]:
        """
        Cronograma em 5 horizontes (M06) — referências da LC 214/2025 e transição.

        Analogia Winthor: equivalente a um roteiro de projeto por “fases de go-live”.
        """
        return [
            {
                "fase": "Curto prazo (0-12 meses)",
                "foco": "Governança, comitê tributário e mapeamento de impacto fiscal e de TI.",
                "referencia_normativa": "LC 214/2025 (transição); EC 132/2023 ADCT",
            },
            {
                "fase": "Médio prazo (12-24 meses)",
                "foco": "Adequação de cadastros, contratos e ERP (cClassTrib / CBS).",
                "referencia_normativa": "NT 2025.002; LC 214/2025 arts. 12-15",
            },
            {
                "fase": "Longo prazo (24-36 meses)",
                "foco": "Estabilização de apuração paralela e créditos pré-reforma.",
                "referencia_normativa": "LC 214/2025 arts. 130-145",
            },
            {
                "fase": "36-60 meses",
                "foco": "Convergência de alíquotas e redução de regimes especiais.",
                "referencia_normativa": "LC 214/2025 arts. 384-410",
            },
            {
                "fase": "60-96 meses (transição plena)",
                "foco": "IBS/CBS plenos; revisão de políticas de preços e compliance.",
                "referencia_normativa": "EC 132/2023; ABNT NBR 17301:2026",
            },
        ]

    @staticmethod
    def _checklist_abnt_10_itens() -> list[AcaoChecklist]:
        """M12 — 10 controles binários (sim/não) ancorados na ABNT NBR 17301:2026."""
        refs = "ABNT NBR 17301:2026"
        return [
            AcaoChecklist(
                "Política de compliance tributário formalizada e divulgada?",
                "Governança",
                "Curto prazo",
                "Alta",
                f"{refs} cap. 5.1",
                1,
            ),
            AcaoChecklist(
                "Riscos fiscais identificados e avaliados periodicamente?",
                "Fiscal",
                "Curto prazo",
                "Alta",
                f"{refs} cap. 6.1",
                2,
            ),
            AcaoChecklist(
                "Controles sobre obrigações tributárias documentados (ITs/fluxos)?",
                "Fiscal",
                "Médio prazo",
                "Alta",
                f"{refs} cap. 7.1",
                3,
            ),
            AcaoChecklist(
                "Monitoramento contínuo de obrigações (não só no fechamento)?",
                "Fiscal",
                "Médio prazo",
                "Alta",
                f"{refs} cap. 9",
                4,
            ),
            AcaoChecklist(
                "Mecanismo formal de melhoria contínua (PDCA) nos processos tributários?",
                "Governança",
                "Médio prazo",
                "Média",
                f"{refs} cap. 10",
                5,
            ),
            AcaoChecklist(
                "Treinamento periódico da equipe em reforma e novos controles?",
                "RH / Fiscal",
                "Curto prazo",
                "Média",
                f"{refs} cap. 8",
                6,
            ),
            AcaoChecklist(
                "Registro e gestão de não conformidades com tratamento e evidências?",
                "Qualidade",
                "Médio prazo",
                "Alta",
                f"{refs} cap. 9",
                7,
            ),
            AcaoChecklist(
                "Indicadores de desempenho fiscal/compliance acompanhados pela diretoria?",
                "Diretoria",
                "Curto prazo",
                "Alta",
                f"{refs} cap. 9",
                8,
            ),
            AcaoChecklist(
                "Revisão de terceiros (fornecedores de dados fiscais) contratualmente prevista?",
                "Jurídico",
                "Longo prazo",
                "Média",
                f"{refs} cap. 7",
                9,
            ),
            AcaoChecklist(
                "Plano de continuidade fiscal / TI para falhas em obrigações acessórias?",
                "TI / Fiscal",
                "Médio prazo",
                "Crítica",
                f"{refs} cap. 7 e cap. 9",
                10,
            ),
        ]

    @staticmethod
    def gerar_checklist(
        diagnostico: Diagnostico,
        score_completo: ScoreCompleto | None = None,
    ) -> list[FrenteTrabalho]:
        frentes: list[FrenteTrabalho] = []

        score = score_completo
        if score is None and diagnostico.score_completo_snapshot is not None:
            score = diagnostico.score_completo_snapshot

        frentes.append(
            FrenteTrabalho(
                nome="Governança e Comitê",
                acoes=[
                    AcaoChecklist(
                        "Constituir Comitê Tributário Reforma",
                        "Diretoria",
                        "Out/2025",
                        "Crítica",
                        "LC 214/2025 art. 5º (previsibilidade)",
                        10,
                    ),
                    AcaoChecklist(
                        "Aprovar plano-mestre de implantação",
                        "Comitê",
                        "Nov/2025",
                        "Alta",
                        "ABNT NBR 17301:2026 cap. 5",
                        11,
                    ),
                ],
            )
        )

        if diagnostico.empresa.porte in (PorteEmpresa.MEDIO, PorteEmpresa.GRANDE):
            frentes.append(
                FrenteTrabalho(
                    nome="TI / ERP / Sistema Fiscal",
                    acoes=[
                        AcaoChecklist(
                            "Levantar gap funcional do ERP",
                            "TI / Fiscal",
                            "Dez/2025",
                            "Crítica",
                            "NT 2025.002 (cClassTrib / NF-e)",
                            20,
                        ),
                        AcaoChecklist(
                            "Aplicar patches fornecidos pelo ERP",
                            "TI",
                            "Mar/2026",
                            "Crítica",
                            "LC 214/2025 arts. 12-15",
                            21,
                        ),
                    ],
                )
            )
            frentes.append(
                FrenteTrabalho(
                    nome="Cadastros Mestres",
                    acoes=[
                        AcaoChecklist(
                            "Revisar 100% do cadastro de itens (NCM, GTIN)",
                            "Cadastro / Fiscal",
                            "Mar/2026",
                            "Crítica",
                            "LC 214/2025 (cadastro de operações)",
                            30,
                        ),
                        AcaoChecklist(
                            "Atualizar CST CBS por item/serviço",
                            "Fiscal",
                            "Mar/2026",
                            "Crítica",
                            "LC 214/2025; NT 2025.002",
                            31,
                        ),
                    ],
                )
            )

        frentes.append(
            FrenteTrabalho(
                nome="Contratos e Cláusulas Tributárias",
                acoes=[
                    AcaoChecklist(
                        "Padronizar nova cláusula tributária (gross-up CBS)",
                        "Jurídico",
                        "Fev/2026",
                        "Crítica",
                        "LC 214/2025 art. 415; CC art. 478",
                        40,
                    ),
                    AcaoChecklist(
                        "Negociar aditivos com fornecedores estratégicos",
                        "Compras",
                        "Mar/2026",
                        "Alta",
                        "LC 214/2025 art. 28 (créditos)",
                        41,
                    ),
                ],
            )
        )

        frentes.append(
            FrenteTrabalho(
                nome="Checklist ABNT NBR 17301 — 10 controles (sim/não)",
                acoes=ConsultoriaService._checklist_abnt_10_itens(),
            )
        )

        if score is not None:
            frentes.insert(0, ConsultoriaService._frente_prioridade_por_gaps_score(score))

        for frente in frentes:
            frente.acoes.sort(key=lambda a: a.prioridade)
        return frentes

    @staticmethod
    def gerar_matriz_impacto(diagnostico: Diagnostico) -> list[ImpactoDepartamento]:
        _ = diagnostico
        return [
            ImpactoDepartamento(
                "Fiscal",
                "Apuração paralela PIS/COFINS e CBS ao longo de 2026",
                "Crítica",
                "LC 214/2025 arts. 130-145 (transição)",
            ),
            ImpactoDepartamento(
                "Comercial",
                "Recalibragem de pricing com novas alíquotas e créditos",
                "Alta",
                "EC 132/2023 (IBS/CBS); LC 214/2025",
            ),
            ImpactoDepartamento(
                "TI",
                "Adequação ERP e NF-e (layout CBS / campos NT 2025.002)",
                "Crítica",
                "NT 2025.002",
            ),
            ImpactoDepartamento(
                "Jurídico",
                "Revisão e aditivo de contratos vigentes",
                "Média",
                "LC 214/2025 art. 415; CC art. 478; NT CGNFS-e (série RFB) — documentação e serviços",
            ),
            ImpactoDepartamento(
                "Financeiro / Controladoria",
                "Projeção de caixa com CBS/IBS e reflexos na formação de preço",
                "Alta",
                "LC 214/2025 arts. 28-32 (créditos); EC 132/2023 art. 156-A",
            ),
            ImpactoDepartamento(
                "RH / Folha",
                "Retenções e benefícios com impacto na base de contribuições correlatas",
                "Média",
                "LC 214/2025 (disciplina do sistema tributário); Lei 8.212/1991 art. 28 (base contrib.)",
            ),
        ]
