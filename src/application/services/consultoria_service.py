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
    Dimensao.COMPLIANCE_ABNT: "Conformidade ABNT NBR 17301",
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
            "validação de XML, plano de reversão em caso de falha e critérios de entrada em produção "
            "antes do piloto produtivo.",
            "TI / Fiscal",
            "60 dias",
            "NT 2025.002; NTs CGNFS-e (série RFB)",
        ),
    ],
    Dimensao.FINANCEIRA: [
        (
            "Construir modelo mensal de fluxo de caixa com abas de sensibilidade CBS/IBS "
            "(alíquota de referência + bandas) confrontando com a referência atual de PIS/COFINS/ICMS — "
            "lacuna «{rotulo}» (score {score_fmt}/100).",
            "Controladoria / Planejamento financeiro",
            "30 dias",
            "LC 214/2025 arts. 28-32; EC 132/2023",
        ),
        (
            "Recalcular margem por linha de produto/serviço com demonstração de resultados sombra "
            "(simulação de DRE tributária sem alterar a escrituração oficial) e anexar premissas ao "
            "comitê de reforma.",
            "Controladoria",
            "45 dias",
            "LC 214/2025 (transição); ABNT NBR 17301:2026 cap. 9",
        ),
        (
            "Rever cláusulas de repasse, reajuste e preço mínimo em contratos de longo prazo à luz "
            "da transição de contribuições indiretas (reprecificação e cláusula de compensação CBS — "
            "«gross-up»).",
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
            "Instituir conciliação mensal SPED face à razão contábil no ERP (receitas, devoluções, "
            "créditos) com roteiro de evidências para auditoria interna e fiscalização futura.",
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
            "Submeter à diretoria um dossiê executivo (até 5 páginas) com os compromissos da reforma "
            "(margem, capital de giro, investimentos em capital em TI e fiscal) e três cenários "
            "quantificados — lacuna «{rotulo}» (score {score_fmt}/100).",
            "Diretoria / Estratégia",
            "30 dias",
            "EC 132/2023; LC 214/2025 art. 5º",
        ),
        (
            "Alinhar calendário decisório da alta administração (aprovações de investimento em ERP, "
            "contratos críticos e política de preços) ao cronograma normativo da LC 214/2025.",
            "Estratégia / Gestão de projetos",
            "45 dias",
            "LC 214/2025 (transição 2026-2033)",
        ),
        (
            "Mapear fusões e aquisições, leilões ou expansão geográfica previstos em 24-36 meses face a "
            "riscos de sinergia fiscal e de ágio (goodwill) tributário pós-reforma.",
            "Fusões e aquisições / Jurídico",
            "60 dias",
            "EC 132/2023; LC 214/2025",
        ),
    ],
    Dimensao.OPERACIONAL: [
        (
            "Documentar procedimento operacional padronizado (POP) ponta a ponta "
            "(pedido → faturamento → logística → devolução) com pontos de controle fiscal, metas de "
            "prazo e qualidade acordadas e evidências — lacuna «{rotulo}» (score {score_fmt}/100).",
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
            "Publicar roteiro técnico de entregas de versão do ERP/módulo fiscal (atualização NT 2025.002, "
            "interfaces com as SEFAZ, retenção de XML) com dependências e janela de congelamento de "
            "alterações — lacuna «{rotulo}» (score {score_fmt}/100).",
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
            "Avaliar integrações por troca eletrônica de dados (EDI) e por interfaces de programa (API) "
            "com clientes e fornecedores que exigirão novo pacote de dados fiscais (cadastro duplo "
            "legado face a CBS/IBS).",
            "TI / Integrações",
            "60 dias",
            "NT 2025.002; NTs CGNFS-e",
        ),
    ],
    Dimensao.COMPLIANCE_ABNT: [
        (
            "Executar análise formal de lacunas face aos controles da ABNT NBR 17301:2026 (caps. 5 a 9) "
            "e registrar achados priorizados em matriz causa e impacto — lacuna «{rotulo}» "
            "(score {score_fmt}/100).",
            "Conformidade / Auditoria interna",
            "45 dias",
            "ABNT NBR 17301:2026",
        ),
        (
            "Implementar trilha de evidências PDCA para incidentes fiscais (registro, tratamento, "
            "ação corretiva, lição aprendida) conforme cap. 10.",
            "Conformidade / Qualidade",
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
        Para cada dimensão entre as três piores, gera **três ações distintas** (cadastro, processo,
        artefato entregável) — uma linha por meta (30/45/60 dias típicos), para o quadro ``f{i}_a{j}``
        e o PDF permanecerem legíveis (evita um único bloco gigante ``(1)…(2)…(3)``).
        """
        piores = sorted(score.score_por_dimensao.items(), key=lambda kv: kv[1].valor)[:3]
        acoes: list[AcaoChecklist] = []
        for dim_idx, (dim, sn) in enumerate(piores, start=1):
            rotulo = _ROTULO_DIMENSAO_PT.get(dim, dim.value.replace("_", " "))
            score_fmt = f"{sn.valor:.1f}"
            crit = "Crítica" if sn.valor < 45.0 else "Alta"
            templates = _LACUNAS_ACOES_POR_DIMENSAO.get(dim)
            if not templates:
                continue
            for tpl_idx, tpl in enumerate(templates):
                desc = tpl[0].format(rotulo=rotulo, score_fmt=score_fmt)
                # Ordem estável na frente M07: pior dimensão (1-3), depois sub-ação (1-3).
                prioridade = (dim_idx - 1) * len(templates) + tpl_idx + 1
                acoes.append(
                    AcaoChecklist(
                        desc,
                        tpl[1],
                        tpl[2],
                        crit,
                        tpl[3],
                        prioridade,
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

        Analogia Winthor: equivalente a um roteiro de projeto por fases de entrada em produção.
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
                "foco": "IBS/CBS plenos; revisão de políticas de preços e de conformidade tributária.",
                "referencia_normativa": "EC 132/2023; ABNT NBR 17301:2026",
            },
        ]

    @staticmethod
    def _checklist_abnt_10_itens() -> list[AcaoChecklist]:
        """M12 — 10 controles binários (sim/não) ancorados na ABNT NBR 17301:2026."""
        refs = "ABNT NBR 17301:2026"
        return [
            AcaoChecklist(
                "Política de conformidade tributária formalizada e divulgada?",
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
                "Controles sobre obrigações tributárias documentados (instruções de trabalho e fluxos)?",
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
                "Indicadores de desempenho fiscal e de conformidade acompanhados pela diretoria?",
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
                            "Mapear lacunas funcionais do ERP face às exigências da reforma (NF-e, CBS)",
                            "TI / Fiscal",
                            "Dez/2025",
                            "Crítica",
                            "NT 2025.002 (cClassTrib / NF-e)",
                            20,
                        ),
                        AcaoChecklist(
                            "Aplicar pacotes de correção (patches) fornecidos pelo fornecedor do ERP",
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
                        "Padronizar cláusula de compensação da oneração CBS («gross-up»)",
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
                "Adequação do ERP e da NF-e (estrutura de campos CBS conforme NT 2025.002)",
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
