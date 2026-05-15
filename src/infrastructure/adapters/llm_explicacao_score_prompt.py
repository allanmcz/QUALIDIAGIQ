"""Prompt dedicado — narrativa sobre o score 0-100 (não recomendação genérica da finalização)."""

from __future__ import annotations

from src.domain.ports.llm_gateway import LlmGatewayRequest


def montar_prompt_explicacao_score(request: LlmGatewayRequest) -> str:
    """Monta instruções focadas em explicar o score já calculado (motor determinístico)."""
    data = request.input_data
    score = data.get("score_geral")
    linhas = [
        "Você é consultor tributário sênior (Reforma do Consumo — EC 132/2023, LC 214/2025).",
        "Tarefa: explicar em português o SIGNIFICADO do score de prontidão já calculado (0 a 100).",
        "NÃO recalcule o score. NÃO invente percentuais novos. NÃO substitua a recomendação da finalização.",
        "",
        f"Score geral (persistido): {score}",
    ]
    por_dim = data.get("score_por_dimensao")
    if isinstance(por_dim, dict) and por_dim:
        linhas.append("Scores por dimensão (motor auditável):")
        for dim, valor in por_dim.items():
            linhas.append(f"  - {dim}: {valor}")
    pesos = data.get("pesos_por_dimensao")
    if isinstance(pesos, dict) and pesos:
        linhas.append("Pesos aplicados por dimensão:")
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
    base = data.get("base_normativa")
    if isinstance(base, str) and base.strip():
        linhas.extend(["", "--- Referências normativas ---", base.strip()])
    linhas.extend(
        [
            "",
            "Produza 1 a 3 parágrafos objetivos: interpretação do nível de maturidade, "
            "dimensão mais crítica e próximo passo prático.",
            "Cite ao menos um dispositivo entre: LC 214/2025, EC 132/2023 ou ABNT NBR 17301:2026.",
        ]
    )
    return "\n".join(linhas)
