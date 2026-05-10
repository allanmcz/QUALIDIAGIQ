"""
Textos estáticos do relatório PDF por idioma (WeasyPrint + Jinja2).

Camada: Infrastructure — sem dependência de FastAPI.
Idiomas: **pt-BR** (completo), **en** (layout + labels; conteúdo gerado por ``ConsultoriaService`` permanece em PT até tradução dedicada).
"""

from __future__ import annotations

from datetime import UTC, datetime


def formatar_telefone_exibicao_br(digitos: str | None) -> str:
    """Formata DDD + número para leitura humana (apenas PDF)."""
    if not digitos or not digitos.isdigit():
        return ""
    d = digitos.strip()
    if len(d) == 10:
        return f"({d[:2]}) {d[2:6]}-{d[6:]}"
    if len(d) == 11:
        return f"({d[:2]}) {d[2:7]}-{d[7:]}"
    return d


_STR_PT_BR: dict[str, str] = {
    "html_title": "Relatório QualiDiagIQ",
    "h1_report_title": "Relatório de Diagnóstico Tributário",
    "label_company": "Empresa",
    "label_sector": "Setor",
    "label_size": "Porte",
    "label_regime": "Regime",
    "lead_section_title": "Captação de lead (contato no relatório)",
    "lead_section_note": (
        "No PDF constam apenas e-mail e telefone neste bloco, conforme política de minimização de dados na peça comercial."
    ),
    "label_email": "E-mail",
    "label_phone": "Telefone",
    "phone_not_informed": "Não informado",
    "label_generated_at": "Data da geração",
    "pdf_engine_note": "Documento gerado com WeasyPrint (motor PDF da QualiDiagIQ).",
    "exec_summary_title": "Síntese executiva",
    "label_overall_score": "Score geral",
    "label_level": "Nível",
    "exec_summary_body": (
        "Este relatório consolida o diagnóstico de prontidão para a Reforma Tributária do Consumo "
        "(<strong>EC 132/2023</strong>, <strong>LC 214/2025</strong>) e aderência ao modelo de compliance da "
        "<strong>ABNT NBR 17301:2026</strong>."
    ),
    "dimensions_priority_title": "Dimensões com menor pontuação (priorizar plano de ação)",
    "maturity_title": "Score de Maturidade Tributária",
    "level_prefix": "Nível",
    "dimensions_detail_title": "Detalhamento por Dimensão (ABNT NBR 17301)",
    "dimensions_detail_intro": (
        "Abaixo apresentamos o detalhamento do seu score em relação aos 7 eixos normativos da ABNT NBR 17301:2026."
    ),
    "th_dimension": "Dimensão",
    "th_score": "Score alcançado",
    "th_weight": "Peso aplicado",
    "gaps_title": "Gaps identificados e recomendações",
    "gaps_intro": (
        "Com base no diagnóstico realizado, identificamos as seguintes oportunidades de melhoria (gaps) na sua operação:"
    ),
    "gap_li_fiscal": (
        "<strong>Políticas internas (Fiscal):</strong> As rotinas fiscais estão pouco alinhadas às novas "
        "resoluções da EC 132/2023."
    ),
    "gap_li_tech": (
        "<strong>Automação (Tecnológica):</strong> Sugerimos a adoção de um sistema ERP atualizado ou módulo fiscal "
        "específico para mitigar riscos de cálculos de CBS/IBS."
    ),
    "gap_li_compliance": (
        "<strong>Conformidade (Compliance ABNT):</strong> Iniciar processo de auditoria interna para "
        "alinhamento mínimo com a ABNT NBR 17301."
    ),
    "ai_box_title": "Consultoria assistida por IA",
    "ai_box_disclaimer": (
        "Texto complementar — validar sempre com base legal versionada (Lexiq) e parecer profissional."
    ),
    "schedule_title": "Cronograma em cinco horizontes (transição LC 214/2025)",
    "schedule_intro": (
        "Referência temporal para governança e projetos — alinhado ao pipeline de implantação CBS/IBS."
    ),
    "th_phase": "Fase",
    "th_focus": "Foco",
    "th_norm_ref": "Referência normativa",
    "matrix_title": "Matriz de impacto por departamento (Reforma do Consumo)",
    "matrix_intro": (
        "Avaliamos quais áreas da sua operação sofrerão maior atrito durante a implantação da CBS:"
    ),
    "th_department": "Departamento",
    "th_impact": "Impacto / ação necessária",
    "th_criticality": "Criticidade",
    "th_legal_ref": "Base legal (referência)",
    "plan_title": "Plano de ação sugerido (checklist de implantação)",
    "plan_intro": (
        "Com base no seu perfil, listamos as ações estruturantes recomendadas para os próximos meses:"
    ),
    "th_num": "#",
    "th_action": "Ação",
    "th_owner": "Responsável",
    "th_deadline": "Prazo",
    "th_crit_table": "Criticidade",
    "th_legal_action": "Base legal (referência)",
    "plan_blocked_title": "Plano de ação avançado (bloqueado)",
    "plan_blocked_body": (
        "O seu plano atual é o <strong>Gratuito</strong>. Para acessar o checklist de implantação e a matriz de "
        "impacto departamental, faça o upgrade para o plano <strong>Avançado</strong>."
    ),
    "disclaimer_title": "Disclaimer",
    "disclaimer_body": (
        "Este relatório foi gerado automaticamente pelo motor QualiDiagIQ com base nas respostas fornecidas. "
        "Os resultados são estimativa de maturidade e conformidade metodológica, com âncoras normativas de referência "
        "(<strong>EC 132/2023</strong>, <strong>LC 214/2025</strong>, <strong>ABNT NBR 17301:2026</strong>). "
        "<strong>Não constitui parecer jurídico consultivo nem opinião fiscal vinculante.</strong> "
        "Não substitui auditoria independente, parecer jurídico formal nem trabalho contábil fiscal; "
        "consulte um profissional habilitado."
    ),
    "footer_brand": "<strong>QualiDiagIQ</strong> — ecossistema <strong>Tributiq</strong>.",
    "cnpj_not_informed": "(CNPJ não informado)",
    "partial_locale_notice": "",
}

_STR_EN: dict[str, str] = {
    "html_title": "QualiDiagIQ Report",
    "h1_report_title": "Tax Diagnostic Report",
    "label_company": "Company",
    "label_sector": "Sector",
    "label_size": "Size",
    "label_regime": "Tax regime",
    "lead_section_title": "Lead capture (as shown on this report)",
    "lead_section_note": (
        "Only e-mail and phone appear in this block on the PDF, per data minimization for the commercial artifact."
    ),
    "label_email": "E-mail",
    "label_phone": "Phone",
    "phone_not_informed": "Not provided",
    "label_generated_at": "Generated at",
    "pdf_engine_note": "PDF generated with WeasyPrint (QualiDiagIQ PDF engine).",
    "exec_summary_title": "Executive summary",
    "label_overall_score": "Overall score",
    "label_level": "Level",
    "exec_summary_body": (
        "This report consolidates readiness for the Brazilian consumption tax reform "
        "(<strong>EC 132/2023</strong>, <strong>LC 214/2025</strong>) and alignment with "
        "<strong>ABNT NBR 17301:2026</strong> compliance management."
    ),
    "dimensions_priority_title": "Lowest-scoring dimensions (prioritize action plan)",
    "maturity_title": "Tax Maturity Score",
    "level_prefix": "Level",
    "dimensions_detail_title": "Breakdown by dimension (ABNT NBR 17301)",
    "dimensions_detail_intro": (
        "Below is your score detail across the seven normative axes of ABNT NBR 17301:2026."
    ),
    "th_dimension": "Dimension",
    "th_score": "Score",
    "th_weight": "Weight applied",
    "gaps_title": "Identified gaps and recommendations",
    "gaps_intro": "Based on the diagnostic, we highlight the following improvement opportunities:",
    "gap_li_fiscal": (
        "<strong>Internal policies (Tax):</strong> Fiscal routines appear weakly aligned with EC 132/2023-driven changes."
    ),
    "gap_li_tech": (
        "<strong>Automation (Technology):</strong> Consider an updated ERP or dedicated tax module to mitigate "
        "CBS/IBS calculation risks."
    ),
    "gap_li_compliance": (
        "<strong>Compliance (ABNT):</strong> Start internal audit minimum alignment with ABNT NBR 17301."
    ),
    "ai_box_title": "AI-assisted advisory",
    "ai_box_disclaimer": (
        "Complementary text — always validate against versioned legal sources (Lexiq) and professional judgment."
    ),
    "schedule_title": "Five-horizon roadmap (LC 214/2025 transition)",
    "schedule_intro": "Timeline reference for governance and CBS/IBS deployment.",
    "th_phase": "Phase",
    "th_focus": "Focus",
    "th_norm_ref": "Normative reference",
    "matrix_title": "Departmental impact matrix (consumption reform)",
    "matrix_intro": "Areas likely to face higher friction during CBS rollout:",
    "th_department": "Department",
    "th_impact": "Impact / required action",
    "th_criticality": "Criticality",
    "th_legal_ref": "Legal reference",
    "plan_title": "Suggested action plan (implementation checklist)",
    "plan_intro": "Structural actions recommended for the coming months:",
    "th_num": "#",
    "th_action": "Action",
    "th_owner": "Owner",
    "th_deadline": "Deadline",
    "th_crit_table": "Criticality",
    "th_legal_action": "Legal reference",
    "plan_blocked_title": "Advanced action plan (locked)",
    "plan_blocked_body": (
        "Your current tier is <strong>Free</strong>. Upgrade to <strong>Advanced</strong> for the full checklist "
        "and departmental impact matrix."
    ),
    "disclaimer_title": "Disclaimer",
    "disclaimer_body": (
        "This report was generated automatically by QualiDiagIQ from the answers provided. Results are indicative "
        "of methodological maturity with reference anchors (<strong>EC 132/2023</strong>, <strong>LC 214/2025</strong>, "
        "<strong>ABNT NBR 17301:2026</strong>). "
        "<strong>It is not binding legal advice nor a formal tax opinion.</strong> "
        "It does not replace independent audit, formal legal opinion, or "
        "formal tax accounting work; consult a qualified professional."
    ),
    "footer_brand": "<strong>QualiDiagIQ</strong> — <strong>Tributiq</strong> ecosystem.",
    "cnpj_not_informed": "(CNPJ not provided)",
    "partial_locale_notice": (
        "<em>Note:</em> Checklist, matrix rows and schedule narrative below may still appear in Portuguese until "
        "full English localization is shipped."
    ),
}


def obter_textos_pdf(locale_relatorio: str) -> dict[str, str]:
    """Resolve o pacote de strings para o template Jinja (default pt-BR)."""
    loc = (locale_relatorio or "pt-BR").strip().lower().replace("_", "-")
    if loc == "en":
        return dict(_STR_EN)
    return dict(_STR_PT_BR)


def nivel_score_labels(locale_relatorio: str) -> dict[str, str]:
    """Rótulos de nível do score geral para o PDF (badges)."""
    loc = (locale_relatorio or "pt-BR").strip().lower().replace("_", "-")
    if loc == "en":
        return {
            "CRITICO": "Critical",
            "INICIAL": "Initial",
            "INTERMEDIARIO": "Intermediate",
            "AVANCADO": "Advanced",
            "EXEMPLAR": "Exemplary",
        }
    return {
        "CRITICO": "Crítico",
        "INICIAL": "Inicial",
        "INTERMEDIARIO": "Intermediário",
        "AVANCADO": "Avançado",
        "EXEMPLAR": "Exemplar",
    }


def formatar_data_geracao_pdf(locale_relatorio: str, agora: datetime | None = None) -> str:
    """Formata carimbo de data/hora da geração conforme idioma (``agora``: ``datetime`` timezone-aware)."""
    if agora is None or not isinstance(agora, datetime):
        agora = datetime.now(UTC)
    loc = (locale_relatorio or "pt-BR").strip().lower().replace("_", "-")
    if loc == "en":
        if agora.tzinfo is None:
            agora = agora.replace(tzinfo=UTC)
        return agora.strftime("%Y-%m-%d %H:%M:%S UTC")
    return agora.strftime("%d/%m/%Y %H:%M:%S")
