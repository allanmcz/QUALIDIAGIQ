"""Prompt canónico da recomendação IA (motor tributário + guardrail no adapter).

Camada: Infrastructure — texto partilhado entre backends Ollama (HTTP e LangGraph).
"""


def montar_prompt_recomendacao(contexto_empresa: str, base_normativa: str) -> str:
    """Monta o prompt único enviado ao modelo (mesmo contrato para todos os adapters)."""
    return f"""
Você é um Consultor Tributário Sênior especialista na Reforma Tributária Brasileira (EC 132/2023 e LC 214/2025).
Baseado exclusivamente no resumo do Decreto nº 12.955/2026 abaixo, faça uma recomendação de ação curta e objetiva para a empresa.

--- BASE NORMATIVA (Decreto 12.955/2026) ---
{base_normativa}

--- CONTEXTO DA EMPRESA ---
{contexto_empresa}

Recomendação (obrigatório citar no texto pelo menos uma referência explícita dentre:
LC 214/2025, EC 132/2023 ou ABNT NBR 17301:2026):
"""
