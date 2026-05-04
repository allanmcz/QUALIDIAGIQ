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

# M07 — três ações concretas por dimensão em lacuna (texto {rotulo} + {score_fmt}).
_LACUNAS_ACOES_POR_DIMENSAO: dict[Dimensao, list[tuple[str, str, str, str]]] = {
    Dimensao.FISCAL: [
        (
            "Auditar cadastro fiscal (NCM, CFOP/CST e campos ligados à classificação tributária, "
            "incluindo preparação para cClassTrib — NT 2025.002) nos itens/serviços que concentram "
            "≥80% do faturamento — lacuna «{rotulo}» (score {score_fmt}/100).",
            "Fiscal / Cadastro",
            "30 dias",
            "NT 2025.002; LC 214/2025 arts. 12-15",
        ),
        (
            "Conduzir oficina fiscal + controladoria mapeando créditos presumidos, diferimento, "
            "monofásico e regimes especiais aplicáveis ao mix real da operação (LC 214/2025 arts. 28-32; "
            "EC 132/2023).",
            "Fiscal / Comitê",
            "45 dias",
            "LC 214/2025 arts. 28-32; EC 132/2023 art. 156-A",
        ),
        (
            "Definir roteiro de homologação NF-e/NFS-e com ERP e parceiro fiscal: lotes de teste, "
            "validação de XML, rollback e critérios de go-live antes do piloto produtivo.",
            "TI / Fiscal",
            "60 dias",
            "NT 2025.002; NTs CGNFS-e (série RFB)",
        ),
    ],
    Dimensao.FINANCEIRA: [
        (
            "Construir modelo mensal de fluxo de caixa com abas de sensibilidade CBS/IBS "
            "(alíquota de referência + bandas) confrontando com baseline atual de PIS/COFINS/ICMS — "
            "lacuna «{rotulo}» (score {score_fmt}/100).",
            "Controladoria / FP&A",
            "30 dias",
            "LC 214/2025 arts. 28-32; EC 132/2023",
        ),
        (
            "Recalcular margem por linha de produto/serviço com «shadow P&L» tributário "
            "(sem alterar contabilidade formal) e anexar premissas ao comitê de reforma.",
            "Controladoria",
            "45 dias",
            "LC 214/2025 (transição); ABNT NBR 17301:2026 cap. 9",
        ),
        (
            "Rever cláusulas de repasse, reajuste e preço mínimo em contratos de longo prazo à luz "
            "da transição de contribuições indiretas (reprecificação / gross-up CBS).",
            "Jurídico / Comercial",
            "60 dias",
            "LC 214/2025 art. 415; CC art. 478",
        ),
    ],
    Dimensao.CONTABIL: [
        (
            "Parametrizar plano de contas auxiliares e rotinas para segregar bases de CBS/IBS "
            "sem perder rastreabilidade perante o SPED — lacuna «{rotulo}» (score {score_fmt}/100).",
            "Contabilidade",
            "30 dias",
            "LC 214/2025 (transparência contábil e escrituração)",
        ),
        (
            "Instituir conciliação mensal SPED versus razão ERP (receitas, devoluções, créditos) com "
            "checklist de evidências para auditoria interna e fiscalização futura.",
            "Contabilidade / Fiscal",
            "45 dias",
            "ABNT NBR 17301:2026 cap. 7.1",
        ),
        (
            "Documentar política de estimativas e provisões tributárias (CPC 25) para cenários "
            "de transição e testes de recuperabilidade de ativos fiscais.",
            "Contabilidade / Auditoria",
            "60 dias",
            "CPC 25 (R1); LC 214/2025",
        ),
    ],
    Dimensao.ESTRATEGICA: [
        (
            "Submeter à diretoria um dossiê executivo (≤5 páginas) com trade-offs da reforma "
            "(margem, capital de giro, capex em TI/fiscal) e três cenários quantificados — "
            "lacuna «{rotulo}» (score {score_fmt}/100).",
            "Diretoria / Estratégia",
            "30 dias",
            "EC 132/2023; LC 214/2025 art. 5º",
        ),
        (
            "Alinhar calendário decisório do board (aprovações de investimento em ERP, contratos "
            "críticos e política de preços) ao cronograma normativo da LC 214/2025.",
            "Estratégia / PMO",
            "45 dias",
            "LC 214/2025 (transição 2026-2033)",
        ),
        (
            "Mapear M&A, leilões ou expansão geográfica previstos em 24-36 meses contra riscos "
            "de sinergia fiscal e goodwill tributário pós-reforma.",
            "M&A / Jurídico",
            "60 dias",
            "EC 132/2023; LC 214/2025",
        ),
    ],
    Dimensao.OPERACIONAL: [
        (
            "Documentar SOP ponta a ponta (pedido → faturamento → logística → devolução) com "
            "checkpoints fiscais, SLAs e evidências — lacuna «{rotulo}» (score {score_fmt}/100).",
            "Operações / Qualidade",
            "30 dias",
            "ABNT NBR 17301:2026 cap. 7",
        ),
        (
            "Executar inventário físico-contábil piloto (CD/loja/planta) com reconciliação "
            "automática de divergências que impactem base de IBS/CBS futura.",
            "Logística / Fiscal",
            "45 dias",
            "LC 214/2025 (cadastro de operações)",
        ),
        (
            "Definir matriz RACI por unidade/ERP para dono do cadastro de produtos, serviços e "
            "contratos — eliminando responsável «órfão» da classificação tributária.",
            "Operações / TI",
            "30 dias",
            "NT 2025.002; ABNT NBR 17301:2026 cap. 5",
        ),
    ],
    Dimensao.TECNOLOGICA: [
        (
            "Publicar roadmap técnico de releases do ERP/módulo fiscal (patch NT 2025.002, "
            "APIs SEFAZ, retenção de XML) com dependências e janela de congelamento — "
            "lacuna «{rotulo}» (score {score_fmt}/100).",
            "TI / Arquitetura",
            "30 dias",
            "NT 2025.002",
        ),
        (
            "Dimensionar ambientes de homologação, mascaramento de dados e testes de carga "
            "para emissão/recebimento de documentos em volume de pico.",
            "TI / Infra",
            "45 dias",
            "LC 214/2025 arts. 12-15",
        ),
        (
            "Avaliar integrações EDI/API com clientes e fornecedores que exigirão novo pacote "
            "de dados fiscais (cadastro dual legado versus CBS/IBS).",
            "TI / Integrações",
            "60 dias",
            "NT 2025.002; NTs CGNFS-e",
        ),
    ],
    Dimensao.COMPLIANCE_ABNT: [
        (
            "Executar gap analysis formal contra controles da ABNT NBR 17301:2026 (caps. 5 a 9) "
            "e registrar achados priorizados em matriz causa versus impacto — lacuna «{rotulo}» "
            "(score {score_fmt}/100).",
            "Compliance / Auditoria interna",
            "45 dias",
            "ABNT NBR 17301:2026",
        ),
        (
            "Implementar trilha de evidências PDCA para incidentes fiscais (registro, tratamento, "
            "ação corretiva, lição aprendida) conforme cap. 10.",
            "Compliance / Qualidade",
            "60 dias",
            "ABNT NBR 17301:2026 cap. 10",
        ),
        (
            "Agendar autoconferência independente (ou terceira parte qualificada) dos dez controles "
            "mínimos ABNT vinculados ao programa tributário da empresa.",
            "Auditoria / Conselho",
            "90 dias",
            "ABNT NBR 17301:2026; LC 214/2025 art. 5º",
        ),
    ],
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

        Regra determinística: usa só o snapshot quantitativo do diagnóstico (sem LLM).
        Para cada dimensão entre as três piores, gera **três ações** objetivas (cadastro, processo,
        artefato entregável) — evita texto genérico do tipo «priorizar plano de ação».
        """
        piores = sorted(score.score_por_dimensao.items(), key=lambda kv: kv[1].valor)[:3]
        acoes: list[AcaoChecklist] = []
        for idx, (dim, sn) in enumerate(piores, start=1):
            rotulo = _ROTULO_DIMENSAO_PT.get(dim, dim.value.replace("_", " "))
            score_fmt = f"{sn.valor:.1f}"
            crit = "Crítica" if sn.valor < 45.0 else "Alta"
            templates = _LACUNAS_ACOES_POR_DIMENSAO.get(dim)
            if not templates:
                continue
            # Um cartão por dimensão em lacuna (mantém f0_a0..f0_a2 estáveis para quadro persistido).
            partes_fmt = [tpl[0].format(rotulo=rotulo, score_fmt=score_fmt) for tpl in templates]
            desc = " ".join(f"({k}) {t}" for k, t in enumerate(partes_fmt, start=1))
            responsaveis = sorted({tpl[1] for tpl in templates})
            prazos = sorted({tpl[2] for tpl in templates})
            bases = [tpl[3] for tpl in templates]
            resp_txt = " / ".join(responsaveis)
            prazo_txt = f"Metas: {', '.join(prazos)}"
            base_txt = "; ".join(bases)
            acoes.append(
                AcaoChecklist(
                    desc,
                    resp_txt,
                    prazo_txt,
                    crit,
                    base_txt,
                    idx,
                )
            )
        return FrenteTrabalho(
            nome="Prioridade conforme lacunas do score (automático — M07)",
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
                "Apuração paralela de PIS/COFINS e CBS ao longo de 2026",
                "Crítica",
                "LC 214/2025 arts. 130-145 (transição)",
            ),
            ImpactoDepartamento(
                "Comercial",
                "Recalibragem da precificação com as novas alíquotas e créditos",
                "Alta",
                "EC 132/2023 (IBS/CBS); LC 214/2025",
            ),
            ImpactoDepartamento(
                "TI",
                "Adequação do ERP e da NF-e (layout CBS / campos da NT 2025.002)",
                "Crítica",
                "NT 2025.002",
            ),
            ImpactoDepartamento(
                "Jurídico",
                "Revisão e aditivos de contratos vigentes",
                "Média",
                "LC 214/2025 art. 415; CC art. 478; NT CGNFS-e (série RFB) — documentação e serviços",
            ),
            ImpactoDepartamento(
                "Financeiro / Controladoria",
                "Projeção de fluxo de caixa com CBS/IBS e efeitos na formação de preço",
                "Alta",
                "LC 214/2025 arts. 28-32 (créditos); EC 132/2023 art. 156-A",
            ),
            ImpactoDepartamento(
                "RH / Folha",
                "Retenções e benefícios com impacto na base das contribuições correlatas",
                "Média",
                "LC 214/2025 (disciplina do sistema tributário); Lei 8.212/1991 art. 28 (base de contribuição)",
            ),
        ]
