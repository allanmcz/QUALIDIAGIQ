"""Prompt dedicado — parecer consultivo sobre o score 0-100 (não recomendação da finalização)."""

from __future__ import annotations

from src.domain.ports.llm_gateway import LlmGatewayRequest

_ANCORAS_OBRIGATORIAS = "EC 132/2023, LC 214/2025 e ABNT NBR 17301:2026"


def montar_prompt_explicacao_score(request: LlmGatewayRequest) -> str:
    """
    Monta instruções para o Ollama (ou outro LLM) **ler o diagnóstico** e emitir parecer.

    O motor QDI já fixou o score; o modelo interpreta e opina — sem recalcular nem inventar nota.
    """
    data = request.input_data
    score = data.get("score_geral")
    linhas = [
        "Você é consultor tributário sênior especializado na Reforma do Consumo do Brasil.",
        "",
        "CONTEXTO: Os dados abaixo vêm de um diagnóstico **já finalizado** no QualiDiagIQ (motor "
        "determinístico auditável). Sua função é **ler esse conteúdo** e redigir um **parecer "
        "profissional em português** (opinião fundamentada), não uma lista técnica seca.",
        "",
        "REGRAS OBRIGATÓRIAS:",
        "- NÃO recalcule o score 0-100 nem invente outro número.",
        "- NÃO substitua a recomendação automática gerada na finalização do diagnóstico.",
        "- Baseie-se **apenas** nos dados fornecidos; se faltar detalhe, diga o que o score sugere "
        "de forma prudente.",
        "- Tom: direto, respeitoso, útil para gestor/contador (2 a 4 parágrafos curtos).",
        "",
        "--- Dados do diagnóstico (leia com atenção) ---",
    ]
    razao = data.get("empresa_razao_social")
    if isinstance(razao, str) and razao.strip():
        linhas.append(f"Empresa: {razao.strip()}")
    linhas.append(f"Score geral (persistido, 0-100): {score}")
    nivel = data.get("nivel_maturidade")
    if isinstance(nivel, str) and nivel.strip():
        linhas.append(f"Nível de maturidade (derivado do motor): {nivel.replace('_', ' ')}")
    dim_crit = data.get("dimensao_mais_critica")
    sc_crit = data.get("score_dimensao_mais_critica")
    if isinstance(dim_crit, str) and dim_crit.strip():
        linhas.append(
            f"Dimensão com menor pontuação: {dim_crit.strip()}"
            + (f" (score {sc_crit})" if sc_crit is not None else "")
        )
    por_dim = data.get("score_por_dimensao")
    if isinstance(por_dim, dict) and por_dim:
        linhas.append("Scores por dimensão (motor auditável):")
        for dim, valor in sorted(por_dim.items(), key=lambda x: float(x[1])):
            linhas.append(f"  - {dim}: {valor}")
    pesos = data.get("pesos_por_dimensao")
    if isinstance(pesos, dict) and pesos:
        linhas.append("Pesos macro aplicados por dimensão:")
        for dim, peso in pesos.items():
            linhas.append(f"  - {dim}: peso {peso}")
    for chave in (
        "empresa_porte",
        "empresa_regime",
        "empresa_setor_macro",
        "empresa_uf",
        "empresa_faixa_faturamento",
    ):
        if chave in data:
            linhas.append(f"{chave}: {data[chave]}")
    rag_ctx = data.get("rag_contexto")
    if isinstance(rag_ctx, str) and rag_ctx.strip():
        linhas.extend(
            [
                "",
                "--- Base de conhecimento recuperada (RAG — cite só o que constar abaixo) ---",
                rag_ctx.strip(),
            ]
        )
    rag_st = data.get("rag_status")
    if isinstance(rag_st, str) and rag_st.strip() == "base_insuficiente":
        linhas.append(
            "",
            "AVISO: a recuperação semântica não atingiu confiança mínima — "
            "seja prudente e não invente artigos ou números de lei.",
        )
    linhas.extend(
        [
            "",
            "--- O que escrever (parecer / opinião) ---",
            "1) O que este score significa para a prontidão da empresa à transição CBS/IBS.",
            "2) Qual dimensão merece atenção prioritária e porquê (use os números acima).",
            "3) Um ou dois próximos passos práticos e realistas.",
            "",
            f"Encerre o texto citando explicitamente, em uma frase final, {_ANCORAS_OBRIGATORIAS}.",
        ]
    )
    return "\n".join(linhas)
