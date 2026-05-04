"""
Escala Likert 1-5 para autoconferência ABNT M12 (10 itens).

Camada: Domain (value object + invariantes)
Base normativa: ABNT NBR 17301:2026 - autoconferência operacional com nuance (não só sim/não).

Valores 1-5 (ordem crescente de maturidade / aderência declarada):
    1: ausência ou não implementado
    5: implementado e monitorado
"""

from __future__ import annotations

M12_NUM_ITENS = 10
M12_LIKERT_MIN = 1
M12_LIKERT_MAX = 5


def validar_itens_m12_likert(itens: list[int]) -> None:
    """Garante exatamente 10 inteiros no intervalo Likert fechado."""
    if len(itens) != M12_NUM_ITENS:
        raise ValueError(
            f"Autoconf M12 exige exatamente {M12_NUM_ITENS} itens; recebido {len(itens)}."
        )
    for i, x in enumerate(itens):
        if not isinstance(x, int) or not (M12_LIKERT_MIN <= x <= M12_LIKERT_MAX):
            raise ValueError(
                f"Item M12 índice {i} inválido: {x!r} - use inteiros entre "
                f"{M12_LIKERT_MIN} e {M12_LIKERT_MAX} (Likert)."
            )


def normalizar_checklist_m12_estado_bruto(raw: object) -> list[int] | None:
    """
    Converte valor JSONB (lista) para 10 inteiros Likert.

    Compatibilidade: listas legadas com booleanos (True vira 5, False vira 1).
    Rejeita listas de tamanho errado ou elementos não mapeáveis.
    """
    if raw is None:
        return None
    if not isinstance(raw, list) or len(raw) != M12_NUM_ITENS:
        return None
    out: list[int] = []
    for x in raw:
        if isinstance(x, bool):
            out.append(M12_LIKERT_MAX if x else M12_LIKERT_MIN)
            continue
        if isinstance(x, int) and M12_LIKERT_MIN <= x <= M12_LIKERT_MAX:
            out.append(x)
            continue
        try:
            xi = int(x)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
        if M12_LIKERT_MIN <= xi <= M12_LIKERT_MAX:
            out.append(xi)
            continue
        return None
    return out
